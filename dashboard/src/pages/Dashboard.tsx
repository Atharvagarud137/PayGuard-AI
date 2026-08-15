import {
    useCallback,
    useEffect,
    useMemo,
    useState,
} from "react"

const API_BASE_URL = "http://127.0.0.1:8000/api/v1"

type TransactionStatus =
    | "AUTHORIZED"
    | "DECLINED"
    | "CAPTURED"
    | "SETTLED"
    | "REFUNDED"
    | "PARTIALLY_REFUNDED"

type DashboardSummary = {
    total_transactions: number
    successful_transactions: number
    pending_transactions: number
    declined_transactions: number
    success_rate: number
}

type Transaction = {
    transaction_id: string
    card_id: string
    merchant_id?: string | null
    authorized_amount?: number | string | null
    captured_amount?: number | string | null
    settled_amount?: number | string | null
    refunded_amount?: number | string | null
    status: TransactionStatus
    decline_reason?: string | null
    created_at?: string | null
}

type DashboardTransaction = Transaction & {
    amount: number
    method: string
    time: string
}

type StatType =
    | "neutral"
    | "success"
    | "warning"
    | "danger"

type Stat = {
    label: string
    value: string
    change: string
    description: string
    icon: string
    type: StatType
}

/* ==========================================================================
   Utility Functions
   ========================================================================== */

function toNumber(
    value: number | string | null | undefined,
): number {
    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return 0
    }

    const parsed = Number(value)

    return Number.isFinite(parsed)
        ? parsed
        : 0
}

function formatCurrency(amount: number): string {
    const safeAmount = Number.isFinite(amount)
        ? amount
        : 0

    return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    }).format(safeAmount)
}

function formatRelativeTime(
    dateString: string | null | undefined,
): string {
    if (!dateString) {
        return "—"
    }

    const date = new Date(dateString)

    if (Number.isNaN(date.getTime())) {
        return "—"
    }

    const now = new Date()

    const differenceInSeconds = Math.floor(
        (now.getTime() - date.getTime()) / 1000,
    )

    if (differenceInSeconds < 60) {
        return `${Math.max(
            differenceInSeconds,
            0,
        )} sec ago`
    }

    const differenceInMinutes = Math.floor(
        differenceInSeconds / 60,
    )

    if (differenceInMinutes < 60) {
        return `${differenceInMinutes} min ago`
    }

    const differenceInHours = Math.floor(
        differenceInMinutes / 60,
    )

    if (differenceInHours < 24) {
        return `${differenceInHours} hr ago`
    }

    const differenceInDays = Math.floor(
        differenceInHours / 24,
    )

    return `${differenceInDays} day${
        differenceInDays === 1 ? "" : "s"
    } ago`
}

function getTransactionAmount(
    transaction: Transaction,
): number {
    switch (transaction.status) {
        case "REFUNDED":
        case "PARTIALLY_REFUNDED":
            return toNumber(
                transaction.refunded_amount,
            )

        case "SETTLED":
            return toNumber(
                transaction.settled_amount,
            )

        case "CAPTURED":
            return toNumber(
                transaction.captured_amount,
            )

        case "AUTHORIZED":
        case "DECLINED":
            return toNumber(
                transaction.authorized_amount,
            )

        default:
            return 0
    }
}

function getPaymentNetwork(
    transaction: Transaction,
): string {
    /*
     * The current backend Transaction model does not
     * expose card network information.
     *
     * Do not invent VISA/Mastercard values in the UI.
     */
    return transaction.card_id
        ? "CARD"
        : "UNKNOWN"
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
   API Helpers
   ========================================================================== */

async function fetchJson<T>(
    url: string,
): Promise<T> {
    const response = await fetch(url)

    if (!response.ok) {
        throw new Error(
            `API request failed: ${response.status} ${response.statusText}`,
        )
    }

    return (await response.json()) as T
}

function normalizeSummary(
    data:
        | Partial<DashboardSummary>
        | null
        | undefined,
): DashboardSummary {
    const totalTransactions = toNumber(
        data?.total_transactions,
    )

    const successfulTransactions = toNumber(
        data?.successful_transactions,
    )

    const pendingTransactions = toNumber(
        data?.pending_transactions,
    )

    const declinedTransactions = toNumber(
        data?.declined_transactions,
    )

    const calculatedSuccessRate =
        totalTransactions > 0
            ? (successfulTransactions /
                totalTransactions) *
            100
            : 0

    const successRate =
        data?.success_rate !== undefined &&
        data?.success_rate !== null
            ? toNumber(data.success_rate)
            : calculatedSuccessRate

    return {
        total_transactions: totalTransactions,
        successful_transactions:
        successfulTransactions,
        pending_transactions:
        pendingTransactions,
        declined_transactions:
        declinedTransactions,
        success_rate: successRate,
    }
}

/* ==========================================================================
   Dashboard Component
   ========================================================================== */

export default function Dashboard() {
    const [summary, setSummary] =
        useState<DashboardSummary | null>(null)

    const [transactions, setTransactions] =
        useState<DashboardTransaction[]>([])

    const [loading, setLoading] =
        useState(true)

    const [error, setError] =
        useState<string | null>(null)

    const [lastUpdated, setLastUpdated] =
        useState<Date | null>(null)

    /* ----------------------------------------------------------------------
       Load dashboard data
       ---------------------------------------------------------------------- */

    const loadDashboard =
        useCallback(async () => {
            try {
                setLoading(true)
                setError(null)

                const [
                    summaryData,
                    transactionData,
                ] = await Promise.all([
                    fetchJson<
                        Partial<DashboardSummary>
                    >(
                        `${API_BASE_URL}/dashboard/summary`,
                    ),

                    fetchJson<Transaction[]>(
                        `${API_BASE_URL}/transactions`,
                    ),
                ])

                const normalizedSummary =
                    normalizeSummary(
                        summaryData,
                    )

                const safeTransactions =
                    Array.isArray(
                        transactionData,
                    )
                        ? transactionData
                        : []

                const normalizedTransactions =
                    safeTransactions.map(
                        (transaction) => ({
                            ...transaction,
                            amount:
                                getTransactionAmount(
                                    transaction,
                                ),
                            method:
                                getPaymentNetwork(
                                    transaction,
                                ),
                            time:
                                formatRelativeTime(
                                    transaction.created_at,
                                ),
                        }),
                    )

                setSummary(
                    normalizedSummary,
                )

                setTransactions(
                    normalizedTransactions,
                )

                setLastUpdated(
                    new Date(),
                )
            } catch (err) {
                console.error(
                    "PayGuard dashboard error:",
                    err,
                )

                const message =
                    err instanceof Error
                        ? err.message
                        : "Unable to load dashboard data."

                setError(message)
            } finally {
                setLoading(false)
            }
        }, [])

    /* ----------------------------------------------------------------------
       Initial load
       ---------------------------------------------------------------------- */

    useEffect(() => {
        void loadDashboard()
    }, [loadDashboard])

    /* ----------------------------------------------------------------------
       Statistics
       ---------------------------------------------------------------------- */

    const stats: Stat[] = useMemo(() => {
        if (!summary) {
            return [
                {
                    label: "Total Transactions",
                    value: "—",
                    change: "—",
                    description: "loading",
                    icon: "⇄",
                    type: "neutral",
                },
                {
                    label: "Successful",
                    value: "—",
                    change: "—",
                    description: "success rate",
                    icon: "✓",
                    type: "success",
                },
                {
                    label: "Pending",
                    value: "—",
                    change: "—",
                    description:
                        "awaiting settlement",
                    icon: "◷",
                    type: "warning",
                },
                {
                    label: "Declined",
                    value: "—",
                    change: "—",
                    description:
                        "requires attention",
                    icon: "!",
                    type: "danger",
                },
            ]
        }

        const total = toNumber(
            summary.total_transactions,
        )

        const successful = toNumber(
            summary.successful_transactions,
        )

        const pending = toNumber(
            summary.pending_transactions,
        )

        const declined = toNumber(
            summary.declined_transactions,
        )

        const successRate =
            total > 0
                ? (successful / total) * 100
                : 0

        const pendingRate =
            total > 0
                ? (pending / total) * 100
                : 0

        const declinedRate =
            total > 0
                ? (declined / total) * 100
                : 0

        return [
            {
                label: "Total Transactions",
                value: String(total),
                change: "LIVE",
                description:
                    "current gateway volume",
                icon: "⇄",
                type: "neutral",
            },
            {
                label: "Successful",
                value: String(successful),
                change: `${successRate.toFixed(
                    1,
                )}%`,
                description: "success rate",
                icon: "✓",
                type: "success",
            },
            {
                label: "Pending",
                value: String(pending),
                change: `${pendingRate.toFixed(
                    1,
                )}%`,
                description:
                    "awaiting settlement",
                icon: "◷",
                type: "warning",
            },
            {
                label: "Declined",
                value: String(declined),
                change: `${declinedRate.toFixed(
                    1,
                )}%`,
                description:
                    "requires attention",
                icon: "!",
                type: "danger",
            },
        ]
    }, [summary])

    /* ----------------------------------------------------------------------
       Recent transactions
       ---------------------------------------------------------------------- */

    const recentTransactions =
        useMemo(
            () =>
                transactions.slice(
                    0,
                    5,
                ),
            [transactions],
        )

    /* ----------------------------------------------------------------------
       Render
       ---------------------------------------------------------------------- */

    return (
        <div className="dashboard-page">

            {/* ==============================================================
                Error
               ============================================================== */}

            {error && (
                <div className="dashboard-error">
                    <div>
                        <strong>
                            Unable to load
                            gateway data
                        </strong>

                        <p>{error}</p>
                    </div>

                    <button
                        type="button"
                        className="action-button"
                        onClick={() =>
                            void loadDashboard()
                        }
                    >
                        Retry
                    </button>
                </div>
            )}

            {/* ==============================================================
                Statistics
               ============================================================== */}

            <section className="stats-grid">
                {stats.map((stat) => (
                    <article
                        className="stat-card"
                        key={stat.label}
                    >
                        <div className="stat-card-top">
                            <div
                                className={`stat-icon ${stat.type}`}
                            >
                                {stat.icon}
                            </div>

                            <span
                                className={`stat-change ${stat.type}`}
                            >
                                {stat.change}
                            </span>
                        </div>

                        <div className="stat-value">
                            {loading
                                ? "…"
                                : stat.value}
                        </div>

                        <div className="stat-label">
                            {stat.label}
                        </div>

                        <div className="stat-description">
                            {stat.description}
                        </div>
                    </article>
                ))}
            </section>

            {/* ==============================================================
                Main Dashboard
               ============================================================== */}

            <section className="dashboard-grid">

                {/* ----------------------------------------------------------
                    Recent Transactions
                   ---------------------------------------------------------- */}

                <article className="panel transaction-panel">

                    <div className="panel-header">
                        <div>
                            <h2>
                                Recent Transactions
                            </h2>

                            <p>
                                Latest activity
                                across the
                                payment gateway.
                            </p>
                        </div>

                        <div className="transaction-panel-actions">

                            {lastUpdated && (
                                <span className="dashboard-last-updated">
                                    Updated{" "}
                                    {lastUpdated.toLocaleTimeString()}
                                </span>
                            )}

                            <button
                                type="button"
                                className="text-button"
                                onClick={() =>
                                    void loadDashboard()
                                }
                            >
                                Refresh →
                            </button>

                        </div>
                    </div>

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
                                    Method
                                </th>

                                <th>
                                    Amount
                                </th>

                                <th>
                                    Status
                                </th>

                                <th>
                                    Time
                                </th>
                            </tr>
                            </thead>

                            <tbody>

                            {loading && (
                                <tr>
                                    <td colSpan={6}>
                                        <div className="dashboard-table-state">
                                            Loading
                                            transactions...
                                        </div>
                                    </td>
                                </tr>
                            )}

                            {!loading &&
                                recentTransactions.length ===
                                0 && (
                                    <tr>
                                        <td colSpan={6}>
                                            <div className="dashboard-table-state">
                                                No
                                                transactions
                                                available.
                                            </div>
                                        </td>
                                    </tr>
                                )}

                            {!loading &&
                                recentTransactions.map(
                                    (transaction) => (
                                        <tr
                                            key={
                                                transaction.transaction_id
                                            }
                                        >
                                            <td>
                                                <span className="transaction-id">
                                                    {
                                                        transaction.transaction_id
                                                    }
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
                                                <span className="payment-network">
                                                    {
                                                        transaction.method
                                                    }
                                                </span>
                                            </td>

                                            <td>
                                                <span className="transaction-amount">
                                                    {formatCurrency(
                                                        transaction.amount,
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
                                                    {
                                                        transaction.time
                                                    }
                                                </span>
                                            </td>
                                        </tr>
                                    ),
                                )}

                            </tbody>

                        </table>

                    </div>

                </article>

                {/* ----------------------------------------------------------
                    System Health
                   ---------------------------------------------------------- */}

                <aside className="panel system-panel">

                    <div className="panel-header">
                        <div>
                            <h2>
                                System Health
                            </h2>

                            <p>
                                Current gateway
                                components.
                            </p>
                        </div>
                    </div>

                    <div className="health-list">

                        <div className="health-row">
                            <div className="health-service">
                                <span className="service-indicator online" />

                                <div>
                                    <strong>
                                        Payment Gateway
                                    </strong>

                                    <span>
                                        FastAPI
                                    </span>
                                </div>
                            </div>

                            <span className="health-state">
                                Operational
                            </span>
                        </div>

                        <div className="health-row">
                            <div className="health-service">
                                <span className="service-indicator online" />

                                <div>
                                    <strong>
                                        Transaction Service
                                    </strong>

                                    <span>
                                        PaymentService
                                    </span>
                                </div>
                            </div>

                            <span className="health-state">
                                Operational
                            </span>
                        </div>

                        <div className="health-row">
                            <div className="health-service">
                                <span className="service-indicator online" />

                                <div>
                                    <strong>
                                        Storage
                                    </strong>

                                    <span>
                                        In-memory
                                    </span>
                                </div>
                            </div>

                            <span className="health-state">
                                Operational
                            </span>
                        </div>

                        <div className="health-row">
                            <div className="health-service">
                                <span className="service-indicator pending" />

                                <div>
                                    <strong>
                                        AI Engine
                                    </strong>

                                    <span>
                                        RCA pipeline
                                    </span>
                                </div>
                            </div>

                            <span className="health-state pending">
                                Planned
                            </span>
                        </div>

                    </div>

                    <div className="ai-card">

                        <div className="ai-card-icon">
                            ✦
                        </div>

                        <div>
                            <strong>
                                AI RCA Engine
                            </strong>

                            <p>
                                Failure analysis
                                will appear here
                                once the AI
                                pipeline is
                                connected.
                            </p>
                        </div>

                    </div>

                </aside>

            </section>

            {/* ==============================================================
                Quick Actions
               ============================================================== */}

            <section className="quick-actions">

                <div>
                    <h2>
                        Payment Operations
                    </h2>

                    <p>
                        Execute and inspect
                        payment lifecycle
                        operations.
                    </p>
                </div>

                <div className="action-buttons">

                    <button
                        type="button"
                        className="action-button primary"
                    >
                        + Issue Card
                    </button>

                    <button
                        type="button"
                        className="action-button"
                    >
                        Authorize Payment
                    </button>

                    <button
                        type="button"
                        className="action-button"
                    >
                        Simulate Failure
                    </button>

                </div>

            </section>

        </div>
    )
}