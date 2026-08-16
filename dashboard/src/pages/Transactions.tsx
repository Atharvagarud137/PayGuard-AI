import {
    useCallback,
    useEffect,
    useMemo,
    useState,
} from "react"

import {
    getTransactions,
    getTransaction,
} from "../services/api"

import type {
    Transaction,
    TransactionEvent,
    TransactionStatus,
} from "../types/payment"

type LifecycleStage =
    | "AUTHORIZED"
    | "CAPTURED"
    | "SETTLED"
    | "REFUNDED"

const LIFECYCLE_STAGES: LifecycleStage[] = [
    "AUTHORIZED",
    "CAPTURED",
    "SETTLED",
    "REFUNDED",
]

/* ==========================================================================
   Utility Functions
   ========================================================================== */

function formatCurrency(
    amount: number,
): string {
    const safeAmount =
        Number.isFinite(amount)
            ? amount
            : 0

    return new Intl.NumberFormat(
        "en-US",
        {
            style: "currency",
            currency: "USD",
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        },
    ).format(safeAmount)
}

function formatDate(
    dateString: string,
): string {
    const date =
        new Date(dateString)

    if (
        Number.isNaN(
            date.getTime(),
        )
    ) {
        return "—"
    }

    return date.toLocaleString(
        "en-US",
        {
            month: "short",
            day: "numeric",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
        },
    )
}

function formatShortId(
    id: string,
): string {
    if (!id) {
        return "—"
    }

    if (id.length <= 16) {
        return id
    }

    return `${id.slice(0, 8)}...${id.slice(-6)}`
}

function getTransactionAmount(
    transaction: Transaction,
): number {
    switch (transaction.status) {
        case "REFUNDED":
        case "PARTIALLY_REFUNDED":
            return transaction.settled_amount

        case "SETTLED":
            return transaction.settled_amount

        case "CAPTURED":
            return transaction.captured_amount

        case "AUTHORIZED":
            return transaction.authorized_amount

        case "DECLINED":
            return transaction.authorized_amount

        default:
            return 0
    }
}

function getStatusClass(
    status: TransactionStatus,
): string {
    switch (status) {
        case "SETTLED":
        case "CAPTURED":
        case "REFUNDED":
            return "status-success"

        case "AUTHORIZED":
            return "status-info"

        case "PARTIALLY_REFUNDED":
            return "status-warning"

        case "DECLINED":
            return "status-danger"

        default:
            return ""
    }
}

/* ==========================================================================
   Lifecycle Helpers
   ========================================================================== */

function getStageState(
    transaction: Transaction,
    stage: LifecycleStage,
):
    | "completed"
    | "current"
    | "upcoming"
    | "failed" {
    /*
     * A declined transaction stops at authorization.
     */
    if (
        transaction.status ===
        "DECLINED"
    ) {
        if (
            stage ===
            "AUTHORIZED"
        ) {
            return "failed"
        }

        return "upcoming"
    }

    /*
     * Read the recorded transaction
     * history from the backend.
     */
    const historyStatuses =
        transaction.history.map(
            (
                event,
            ) =>
                event.status,
        )

    /*
     * PARTIALLY_REFUNDED means:
     *
     * AUTHORIZED  ✓
     * CAPTURED    ✓
     * SETTLED     ✓
     * REFUNDED    current
     */
    if (
        transaction.status ===
        "PARTIALLY_REFUNDED"
    ) {
        if (
            stage ===
            "REFUNDED"
        ) {
            return "current"
        }

        return "completed"
    }

    /*
     * Fully refunded transaction.
     */
    if (
        transaction.status ===
        "REFUNDED"
    ) {
        return "completed"
    }

    /*
     * If the event explicitly exists
     * in transaction history, it is
     * completed.
     */
    if (
        historyStatuses.includes(
            stage,
        )
    ) {
        return "completed"
    }

    const stageIndex =
        LIFECYCLE_STAGES.indexOf(
            stage,
        )

    const currentIndex =
        LIFECYCLE_STAGES.indexOf(
            transaction.status as LifecycleStage,
        )

    /*
     * Current lifecycle state.
     */
    if (
        stageIndex ===
        currentIndex
    ) {
        return "current"
    }

    /*
     * Earlier lifecycle stages are
     * considered completed.
     */
    if (
        currentIndex >= 0 &&
        stageIndex <
        currentIndex
    ) {
        return "completed"
    }

    return "upcoming"
}

function getStageAmount(
    transaction: Transaction,
    stage: LifecycleStage,
): number {
    switch (stage) {
        case "AUTHORIZED":
            return transaction.authorized_amount

        case "CAPTURED":
            return transaction.captured_amount

        case "SETTLED":
            return transaction.settled_amount

        case "REFUNDED":
            return transaction.refunded_amount

        default:
            return 0
    }
}

function getStageEvent(
    transaction: Transaction,
    stage: LifecycleStage,
): TransactionEvent | undefined {
    return transaction.history.find(
        (
            event,
        ) => {
            if (
                stage ===
                "REFUNDED"
            ) {
                return (
                    event.status ===
                    "REFUNDED" ||
                    event.status ===
                    "PARTIALLY_REFUNDED"
                )
            }

            return (
                event.status ===
                stage
            )
        },
    )
}

/* ==========================================================================
   Transactions Page
   ========================================================================== */

export default function Transactions() {
    const [
        transactions,
        setTransactions,
    ] = useState<Transaction[]>([])

    const [
        selectedTransaction,
        setSelectedTransaction,
    ] = useState<Transaction | null>(
        null,
    )

    const [
        loading,
        setLoading,
    ] = useState(true)

    const [
        detailLoading,
        setDetailLoading,
    ] = useState(false)

    const [
        error,
        setError,
    ] = useState<string | null>(
        null,
    )

    const [
        detailError,
        setDetailError,
    ] = useState<string | null>(
        null,
    )

    /* ----------------------------------------------------------------------
       Load transaction list

       IMPORTANT:
       This callback does NOT depend on selectedTransaction.

       That prevents the following loop:

       selectedTransaction
           ↓
       loadTransactions changes
           ↓
       useEffect runs
           ↓
       transaction list reloads
           ↓
       selectedTransaction changes
           ↓
       repeat
       ---------------------------------------------------------------------- */

    const loadTransactions =
        useCallback(
            async () => {
                try {
                    setLoading(true)
                    setError(null)

                    const data =
                        await getTransactions()

                    const safeTransactions =
                        Array.isArray(data)
                            ? data
                            : []

                    /*
                     * Keep newest transactions
                     * at the top regardless of the
                     * backend ordering.
                     */
                    const sortedTransactions =
                        [
                            ...safeTransactions,
                        ].sort(
                            (
                                first,
                                second,
                            ) =>
                                new Date(
                                    second.created_at,
                                ).getTime() -
                                new Date(
                                    first.created_at,
                                ).getTime(),
                        )

                    setTransactions(
                        sortedTransactions,
                    )
                } catch (err) {
                    console.error(
                        "PayGuard transactions error:",
                        err,
                    )

                    setError(
                        err instanceof Error
                            ? err.message
                            : "Unable to load transactions.",
                    )
                } finally {
                    setLoading(false)
                }
            },
            [],
        )

    /* ----------------------------------------------------------------------
       Initial page load
       ---------------------------------------------------------------------- */

    useEffect(() => {
        void loadTransactions()
    }, [loadTransactions])

    /* ----------------------------------------------------------------------
       Open transaction lifecycle
       ---------------------------------------------------------------------- */

    const openTransaction =
        useCallback(
            async (
                transactionId: string,
            ) => {
                try {
                    setDetailLoading(
                        true,
                    )

                    setDetailError(
                        null,
                    )

                    const transaction =
                        await getTransaction(
                            transactionId,
                        )

                    setSelectedTransaction(
                        transaction,
                    )
                } catch (err) {
                    console.error(
                        "PayGuard transaction detail error:",
                        err,
                    )

                    setDetailError(
                        err instanceof Error
                            ? err.message
                            : "Unable to load transaction.",
                    )
                } finally {
                    setDetailLoading(
                        false,
                    )
                }
            },
            [],
        )

    /* ----------------------------------------------------------------------
       Close lifecycle panel
       ---------------------------------------------------------------------- */

    const closeTransaction =
        useCallback(
            () => {
                if (
                    detailLoading
                ) {
                    return
                }

                setSelectedTransaction(
                    null,
                )

                setDetailError(
                    null,
                )
            },
            [detailLoading],
        )

    /* ----------------------------------------------------------------------
       Summary calculations
       ---------------------------------------------------------------------- */

    const transactionCount =
        transactions.length

    const settledCount =
        useMemo(
            () =>
                transactions.filter(
                    (
                        transaction,
                    ) =>
                        transaction.status ===
                        "SETTLED" ||
                        transaction.status ===
                        "REFUNDED" ||
                        transaction.status ===
                        "PARTIALLY_REFUNDED",
                ).length,
            [transactions],
        )

    const pendingCount =
        useMemo(
            () =>
                transactions.filter(
                    (
                        transaction,
                    ) =>
                        transaction.status ===
                        "AUTHORIZED" ||
                        transaction.status ===
                        "CAPTURED",
                ).length,
            [transactions],
        )

    /* ----------------------------------------------------------------------
       Render
       ---------------------------------------------------------------------- */

    return (
        <div className="transactions-page">

            {/* =============================================================
               Page Header
               ============================================================= */}

            <section className="transactions-page-header">

                <div>
                    <h2>
                        Transactions
                    </h2>

                    <p>
                        Inspect payment activity
                        and follow each transaction
                        through its lifecycle.
                    </p>
                </div>

                <button
                    type="button"
                    className="text-button"
                    onClick={() =>
                        void loadTransactions()
                    }
                    disabled={loading}
                >
                    {loading
                        ? "Refreshing..."
                        : "Refresh →"}
                </button>

            </section>

            {/* =============================================================
               Error
               ============================================================= */}

            {error && (
                <div className="dashboard-error">

                    <div>
                        <strong>
                            Unable to load
                            transactions
                        </strong>

                        <p>
                            {error}
                        </p>
                    </div>

                    <button
                        type="button"
                        className="action-button"
                        onClick={() =>
                            void loadTransactions()
                        }
                    >
                        Retry
                    </button>

                </div>
            )}

            {/* =============================================================
               Summary
               ============================================================= */}

            <section className="transactions-stats-grid">

                <article className="stat-card">

                    <div className="stat-card-top">

                        <div className="stat-icon neutral">
                            ⇄
                        </div>

                        <span className="stat-change neutral">
                            LIVE
                        </span>

                    </div>

                    <div className="stat-value">
                        {loading
                            ? "…"
                            : transactionCount}
                    </div>

                    <div className="stat-label">
                        Total Transactions
                    </div>

                    <div className="stat-description">
                        gateway activity
                    </div>

                </article>

                <article className="stat-card">

                    <div className="stat-card-top">

                        <div className="stat-icon success">
                            ✓
                        </div>

                        <span className="stat-change success">
                            COMPLETED
                        </span>

                    </div>

                    <div className="stat-value">
                        {loading
                            ? "…"
                            : settledCount}
                    </div>

                    <div className="stat-label">
                        Completed
                    </div>

                    <div className="stat-description">
                        settled or refunded
                    </div>

                </article>

                <article className="stat-card">

                    <div className="stat-card-top">

                        <div className="stat-icon warning">
                            ◷
                        </div>

                        <span className="stat-change warning">
                            PENDING
                        </span>

                    </div>

                    <div className="stat-value">
                        {loading
                            ? "…"
                            : pendingCount}
                    </div>

                    <div className="stat-label">
                        In Progress
                    </div>

                    <div className="stat-description">
                        awaiting next lifecycle step
                    </div>

                </article>

            </section>

            {/* =============================================================
               Transaction Table
               ============================================================= */}

            <section className="panel transactions-list-panel">

                <div className="panel-header">

                    <div>
                        <h2>
                            Payment Transactions
                        </h2>

                        <p>
                            Select a transaction to
                            inspect its complete lifecycle.
                        </p>
                    </div>

                    <span className="cards-count">
                        {loading
                            ? "Loading..."
                            : `${transactionCount} ${
                                transactionCount ===
                                1
                                    ? "transaction"
                                    : "transactions"
                            }`}
                    </span>

                </div>

                {loading && (
                    <div className="cards-loading">
                        Loading transactions...
                    </div>
                )}

                {!loading &&
                    transactions.length ===
                    0 && (
                        <div className="cards-empty-state">

                            <div className="cards-empty-icon">
                                ⇄
                            </div>

                            <h3>
                                No transactions yet
                            </h3>

                            <p>
                                Authorize a payment
                                from an active card
                                to begin testing
                                the transaction
                                lifecycle.
                            </p>

                        </div>
                    )}

                {!loading &&
                    transactions.length >
                    0 && (
                        <div className="transaction-table-wrapper">

                            <table className="transaction-table">

                                <thead>
                                <tr>

                                    <th>
                                        Transaction
                                    </th>

                                    <th>
                                        Merchant
                                    </th>

                                    <th>
                                        Amount
                                    </th>

                                    <th>
                                        Status
                                    </th>

                                    <th>
                                        Created
                                    </th>

                                    <th>
                                        Action
                                    </th>

                                </tr>
                                </thead>

                                <tbody>

                                {transactions.map(
                                    (
                                        transaction,
                                    ) => (
                                        <tr
                                            key={
                                                transaction.transaction_id
                                            }
                                        >

                                            <td>
                                                <span className="transaction-id">
                                                    {formatShortId(
                                                        transaction.transaction_id,
                                                    )}
                                                </span>
                                            </td>

                                            <td>
                                                <span className="merchant-name">
                                                    {
                                                        transaction.merchant_id ||
                                                        "—"
                                                    }
                                                </span>
                                            </td>

                                            <td>
                                                <span className="transaction-amount">
                                                    {formatCurrency(
                                                        getTransactionAmount(
                                                            transaction,
                                                        ),
                                                    )}
                                                </span>
                                            </td>

                                            <td>
                                                <span
                                                    className={`transaction-status ${getStatusClass(
                                                        transaction.status,
                                                    )}`}
                                                >

                                                    <span className="status-dot" />

                                                    {
                                                        transaction.status
                                                    }

                                                </span>
                                            </td>

                                            <td>
                                                <span className="transaction-time">
                                                    {formatDate(
                                                        transaction.created_at,
                                                    )}
                                                </span>
                                            </td>

                                            <td>
                                                <button
                                                    type="button"
                                                    className="text-button"
                                                    onClick={() =>
                                                        void openTransaction(
                                                            transaction.transaction_id,
                                                        )
                                                    }
                                                    disabled={
                                                        detailLoading
                                                    }
                                                >
                                                    View Lifecycle →
                                                </button>
                                            </td>

                                        </tr>
                                    ),
                                )}

                                </tbody>

                            </table>

                        </div>
                    )}

            </section>

            {/* =============================================================
               Lifecycle Detail Overlay
               ============================================================= */}

            {selectedTransaction && (
                <div
                    className="transaction-detail-overlay"
                    role="presentation"
                >

                    <section
                        className="transaction-detail-panel"
                        role="dialog"
                        aria-modal="true"
                        aria-label="Transaction lifecycle"
                    >

                        {/* -------------------------------------------------
                           Header
                           ------------------------------------------------- */}

                        <div className="transaction-detail-header">

                            <div>

                                <span className="transaction-detail-eyebrow">
                                    TRANSACTION LIFECYCLE
                                </span>

                                <h2>
                                    {formatShortId(
                                        selectedTransaction.transaction_id,
                                    )}
                                </h2>

                                <p>
                                    {
                                        selectedTransaction.merchant_id ||
                                        "No merchant"
                                    }
                                </p>

                            </div>

                            <button
                                type="button"
                                className="icon-button"
                                onClick={
                                    closeTransaction
                                }
                                aria-label="Close transaction details"
                                disabled={
                                    detailLoading
                                }
                            >
                                ×
                            </button>

                        </div>

                        {/* -------------------------------------------------
                           Detail loading
                           ------------------------------------------------- */}

                        {detailLoading && (
                            <div className="cards-loading">
                                Loading transaction lifecycle...
                            </div>
                        )}

                        {/* -------------------------------------------------
                           Detail error
                           ------------------------------------------------- */}

                        {detailError && (
                            <div className="card-form-error">
                                {detailError}
                            </div>
                        )}

                        {/* -------------------------------------------------
                           Amount Summary
                           ------------------------------------------------- */}

                        <div className="transaction-detail-summary">

                            <div>
                                <span>
                                    AUTHORIZED
                                </span>

                                <strong>
                                    {formatCurrency(
                                        selectedTransaction.authorized_amount,
                                    )}
                                </strong>
                            </div>

                            <div>
                                <span>
                                    CAPTURED
                                </span>

                                <strong>
                                    {formatCurrency(
                                        selectedTransaction.captured_amount,
                                    )}
                                </strong>
                            </div>

                            <div>
                                <span>
                                    SETTLED
                                </span>

                                <strong>
                                    {formatCurrency(
                                        selectedTransaction.settled_amount,
                                    )}
                                </strong>
                            </div>

                            <div>
                                <span>
                                    REFUNDED
                                </span>

                                <strong>
                                    {formatCurrency(
                                        selectedTransaction.refunded_amount,
                                    )}
                                </strong>
                            </div>

                        </div>

                        {/* -------------------------------------------------
                           Lifecycle
                           ------------------------------------------------- */}

                        <div className="transaction-lifecycle">

                            {LIFECYCLE_STAGES.map(
                                (
                                    stage,
                                    index,
                                ) => {

                                    const state =
                                        getStageState(
                                            selectedTransaction,
                                            stage,
                                        )

                                    const event =
                                        getStageEvent(
                                            selectedTransaction,
                                            stage,
                                        )

                                    const amount =
                                        getStageAmount(
                                            selectedTransaction,
                                            stage,
                                        )

                                    return (
                                        <div
                                            className="lifecycle-item"
                                            key={
                                                stage
                                            }
                                        >

                                            {/* --------------------------------
                                               Marker
                                               -------------------------------- */}

                                            <div className="lifecycle-marker-column">

                                                <div
                                                    className={`lifecycle-marker ${state}`}
                                                >
                                                    {state ===
                                                    "completed"
                                                        ? "✓"
                                                        : state ===
                                                        "failed"
                                                            ? "!"
                                                            : state ===
                                                            "current"
                                                                ? "●"
                                                                : "○"}
                                                </div>

                                                {index <
                                                    LIFECYCLE_STAGES.length -
                                                    1 && (
                                                        <div
                                                            className={`lifecycle-connector ${
                                                                state ===
                                                                "completed"
                                                                    ? "completed"
                                                                    : ""
                                                            }`}
                                                        />
                                                    )}

                                            </div>

                                            {/* --------------------------------
                                               Content
                                               -------------------------------- */}

                                            <div className="lifecycle-content">

                                                <div className="lifecycle-content-header">

                                                    <div>

                                                        <span className="lifecycle-stage-label">
                                                            {stage}
                                                        </span>

                                                        <span className="lifecycle-stage-state">
                                                            {state ===
                                                            "completed"
                                                                ? "Completed"
                                                                : state ===
                                                                "current"
                                                                    ? "Current state"
                                                                    : state ===
                                                                    "failed"
                                                                        ? "Declined"
                                                                        : "Pending"}
                                                        </span>

                                                    </div>

                                                    {amount >
                                                        0 && (
                                                            <strong>
                                                                {formatCurrency(
                                                                    amount,
                                                                )}
                                                            </strong>
                                                        )}

                                                </div>

                                                {/* --------------------------------
                                                   Event information
                                                   -------------------------------- */}

                                                {event && (
                                                    <div className="lifecycle-event">

                                                        <span>
                                                            {
                                                                event.detail ||
                                                                "Lifecycle event recorded."
                                                            }
                                                        </span>

                                                        <time>
                                                            {formatDate(
                                                                event.timestamp,
                                                            )}
                                                        </time>

                                                    </div>
                                                )}

                                                {/* --------------------------------
                                                   Upcoming stage
                                                   -------------------------------- */}

                                                {!event &&
                                                    state ===
                                                    "upcoming" && (
                                                        <p className="lifecycle-pending">
                                                            Waiting for the
                                                            previous lifecycle
                                                            step to complete.
                                                        </p>
                                                    )}

                                            </div>

                                        </div>
                                    )
                                },
                            )}

                            {/* -------------------------------------------------
                               Declined transaction
                               ------------------------------------------------- */}

                            {selectedTransaction.status ===
                                "DECLINED" && (
                                    <div className="lifecycle-declined">

                                        <div className="lifecycle-marker failed">
                                            !
                                        </div>

                                        <div>

                                            <strong>
                                                Authorization
                                                Declined
                                            </strong>

                                            <p>
                                                {
                                                    selectedTransaction.decline_reason ||
                                                    "The payment was declined."
                                                }
                                            </p>

                                        </div>

                                    </div>
                                )}

                        </div>

                        {/* -------------------------------------------------
                           Footer
                           ------------------------------------------------- */}

                        <div className="transaction-detail-footer">

                            <div>

                                <span>
                                    CARD ID
                                </span>

                                <strong>
                                    {
                                        selectedTransaction.card_id
                                    }
                                </strong>

                            </div>

                            <div>

                                <span>
                                    CREATED
                                </span>

                                <strong>
                                    {formatDate(
                                        selectedTransaction.created_at,
                                    )}
                                </strong>

                            </div>

                        </div>

                    </section>

                </div>
            )}

        </div>
    )
}