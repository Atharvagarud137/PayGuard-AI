import {
    useCallback,
    useEffect,
    useState,
} from "react"

import type {
    FormEvent,
} from "react"

import {
    createCard,
    getCards,
} from "../services/api"

import type {
    Card,
    CardNetwork,
} from "../types/payment"

type CardFormState = {
    cardholder_name: string
    network: CardNetwork
    initial_balance: string
    expiry_date: string
}

const INITIAL_FORM: CardFormState = {
    cardholder_name: "",
    network: "VISA",
    initial_balance: "1000",
    expiry_date: "",
}

function formatCurrency(amount: number): string {
    return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    }).format(Number.isFinite(amount) ? amount : 0)
}

function formatDate(dateString: string): string {
    const date = new Date(dateString)

    if (Number.isNaN(date.getTime())) {
        return "—"
    }

    return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
    })
}

function getNetworkLabel(network: CardNetwork): string {
    switch (network) {
        case "VISA":
            return "VISA"

        case "MASTERCARD":
            return "Mastercard"

        case "GENERIC":
            return "Generic"

        default:
            return network
    }
}

function getStatusClass(
    status: Card["status"],
): string {
    switch (status) {
        case "ACTIVE":
            return "card-status-active"

        case "INACTIVE":
            return "card-status-inactive"

        case "EXPIRED":
            return "card-status-expired"

        default:
            return ""
    }
}

function maskCardNumber(cardNumber: string): string {
    if (!cardNumber) {
        return "****-****-****-****"
    }

    return cardNumber
}

export default function Cards() {
    const [cards, setCards] = useState<Card[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    const [showIssueForm, setShowIssueForm] =
        useState(false)

    const [form, setForm] =
        useState<CardFormState>(INITIAL_FORM)

    const [submitting, setSubmitting] =
        useState(false)

    const [formError, setFormError] =
        useState<string | null>(null)

    const [successMessage, setSuccessMessage] =
        useState<string | null>(null)

    /* =========================================================================
       Load Cards
       ========================================================================= */

    const loadCards = useCallback(async () => {
        try {
            setLoading(true)
            setError(null)

            const data = await getCards()

            setCards(
                Array.isArray(data)
                    ? data
                    : [],
            )
        } catch (err) {
            console.error(
                "PayGuard cards error:",
                err,
            )

            setError(
                err instanceof Error
                    ? err.message
                    : "Unable to load cards.",
            )
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        void loadCards()
    }, [loadCards])

    /* =========================================================================
       Derived Statistics
       ========================================================================= */

    const activeCards = cards.filter(
        (card) => card.status === "ACTIVE",
    ).length

    const totalBalance = cards.reduce(
        (total, card) =>
            total + Number(card.balance || 0),
        0,
    )

    /* =========================================================================
       Issue Card
       ========================================================================= */

    const handleSubmit = async (
        event: FormEvent<HTMLFormElement>,
    ) => {
        event.preventDefault()

        setFormError(null)
        setSuccessMessage(null)

        const cardholderName =
            form.cardholder_name.trim()

        const initialBalance =
            Number(form.initial_balance)

        if (!cardholderName) {
            setFormError(
                "Cardholder name is required.",
            )
            return
        }

        if (
            !Number.isFinite(initialBalance) ||
            initialBalance < 0
        ) {
            setFormError(
                "Initial balance must be zero or greater.",
            )
            return
        }

        if (!form.expiry_date) {
            setFormError(
                "Expiry date is required.",
            )
            return
        }

        try {
            setSubmitting(true)

            await createCard({
                cardholder_name: cardholderName,
                network: form.network,
                initial_balance: initialBalance,
                expiry_date: form.expiry_date,
            })

            setForm(INITIAL_FORM)
            setShowIssueForm(false)

            setSuccessMessage(
                "Card issued successfully.",
            )

            await loadCards()
        } catch (err) {
            console.error(
                "PayGuard card issuance error:",
                err,
            )

            setFormError(
                err instanceof Error
                    ? err.message
                    : "Unable to issue card.",
            )
        } finally {
            setSubmitting(false)
        }
    }

    const handleCancel = () => {
        if (submitting) {
            return
        }

        setForm(INITIAL_FORM)
        setFormError(null)
        setShowIssueForm(false)
    }

    const openIssueForm = () => {
        setFormError(null)
        setSuccessMessage(null)
        setShowIssueForm(true)
    }

    /* =========================================================================
       Render
       ========================================================================= */

    return (
        <div className="cards-page">

            {/* =================================================================
               Page Header
               ================================================================= */}

            <section className="cards-page-header">
                <div>
                    <h2>Cards</h2>

                    <p>
                        Manage mock payment cards and
                        available balances.
                    </p>
                </div>

                <div className="cards-header-actions">

                    <button
                        type="button"
                        className="text-button"
                        onClick={() =>
                            void loadCards()
                        }
                        disabled={loading}
                    >
                        {loading
                            ? "Refreshing..."
                            : "Refresh →"}
                    </button>

                    <button
                        type="button"
                        className="action-button primary"
                        onClick={openIssueForm}
                        disabled={submitting}
                    >
                        + Issue Card
                    </button>

                </div>
            </section>

            {/* =================================================================
               Error Message
               ================================================================= */}

            {error && (
                <div className="dashboard-error">
                    <div>
                        <strong>
                            Unable to load cards
                        </strong>

                        <p>
                            {error}
                        </p>
                    </div>

                    <button
                        type="button"
                        className="action-button"
                        onClick={() =>
                            void loadCards()
                        }
                    >
                        Retry
                    </button>
                </div>
            )}

            {/* =================================================================
               Success Message
               ================================================================= */}

            {successMessage && (
                <div className="cards-success-message">
                    {successMessage}
                </div>
            )}

            {/* =================================================================
               Summary Cards
               ================================================================= */}

            <section className="cards-stats-grid">

                <article className="stat-card">

                    <div className="stat-card-top">
                        <div className="stat-icon neutral">
                            ▣
                        </div>

                        <span className="stat-change neutral">
                            LIVE
                        </span>
                    </div>

                    <div className="stat-value">
                        {loading
                            ? "…"
                            : cards.length}
                    </div>

                    <div className="stat-label">
                        Total Cards
                    </div>

                    <div className="stat-description">
                        cards issued by gateway
                    </div>

                </article>

                <article className="stat-card">

                    <div className="stat-card-top">
                        <div className="stat-icon success">
                            ✓
                        </div>

                        <span className="stat-change success">
                            ACTIVE
                        </span>
                    </div>

                    <div className="stat-value">
                        {loading
                            ? "…"
                            : activeCards}
                    </div>

                    <div className="stat-label">
                        Active Cards
                    </div>

                    <div className="stat-description">
                        available for payments
                    </div>

                </article>

                <article className="stat-card">

                    <div className="stat-card-top">
                        <div className="stat-icon neutral">
                            $
                        </div>

                        <span className="stat-change neutral">
                            BALANCE
                        </span>
                    </div>

                    <div className="stat-value cards-balance-value">
                        {loading
                            ? "…"
                            : formatCurrency(
                                totalBalance,
                            )}
                    </div>

                    <div className="stat-label">
                        Available Balance
                    </div>

                    <div className="stat-description">
                        across all cards
                    </div>

                </article>

            </section>

            {/* =================================================================
               Issue Card Form
               ================================================================= */}

            {showIssueForm && (
                <section className="panel card-form-panel">

                    <div className="panel-header">
                        <div>
                            <h2>
                                Issue New Card
                            </h2>

                            <p>
                                Create a virtual mock
                                payment card.
                            </p>
                        </div>
                    </div>

                    <form
                        className="card-form"
                        onSubmit={handleSubmit}
                    >

                        {/* Cardholder */}

                        <div className="form-field">

                            <label htmlFor="cardholder-name">
                                Cardholder Name
                            </label>

                            <input
                                id="cardholder-name"
                                type="text"
                                value={
                                    form.cardholder_name
                                }
                                onChange={(event) =>
                                    setForm(
                                        (current) => ({
                                            ...current,
                                            cardholder_name:
                                            event.target
                                                .value,
                                        }),
                                    )
                                }
                                placeholder="e.g. Atharva Garud"
                                disabled={submitting}
                                autoComplete="off"
                            />

                        </div>

                        {/* Network */}

                        <div className="form-field">

                            <label htmlFor="card-network">
                                Network
                            </label>

                            <select
                                id="card-network"
                                value={form.network}
                                onChange={(event) =>
                                    setForm(
                                        (current) => ({
                                            ...current,
                                            network:
                                                event.target
                                                    .value as CardNetwork,
                                        }),
                                    )
                                }
                                disabled={submitting}
                            >
                                <option value="VISA">
                                    VISA
                                </option>

                                <option value="MASTERCARD">
                                    Mastercard
                                </option>

                                <option value="GENERIC">
                                    Generic
                                </option>
                            </select>

                        </div>

                        {/* Initial Balance */}

                        <div className="form-field">

                            <label htmlFor="initial-balance">
                                Initial Balance
                            </label>

                            <input
                                id="initial-balance"
                                type="number"
                                min="0"
                                step="0.01"
                                value={
                                    form.initial_balance
                                }
                                onChange={(event) =>
                                    setForm(
                                        (current) => ({
                                            ...current,
                                            initial_balance:
                                            event.target
                                                .value,
                                        }),
                                    )
                                }
                                placeholder="1000.00"
                                disabled={submitting}
                            />

                        </div>

                        {/* Expiry Date */}

                        <div className="form-field">

                            <label htmlFor="expiry-date">
                                Expiry Date
                            </label>

                            <input
                                id="expiry-date"
                                type="date"
                                value={
                                    form.expiry_date
                                }
                                onChange={(event) =>
                                    setForm(
                                        (current) => ({
                                            ...current,
                                            expiry_date:
                                            event.target
                                                .value,
                                        }),
                                    )
                                }
                                disabled={submitting}
                            />

                        </div>

                        {/* Form Error */}

                        {formError && (
                            <div className="card-form-error">
                                {formError}
                            </div>
                        )}

                        {/* Form Actions */}

                        <div className="card-form-actions">

                            <button
                                type="button"
                                className="action-button"
                                onClick={handleCancel}
                                disabled={submitting}
                            >
                                Cancel
                            </button>

                            <button
                                type="submit"
                                className="action-button primary"
                                disabled={submitting}
                            >
                                {submitting
                                    ? "Issuing..."
                                    : "Issue Card"}
                            </button>

                        </div>

                    </form>

                </section>
            )}

            {/* =================================================================
               Cards List
               ================================================================= */}

            <section className="panel cards-list-panel">

                <div className="panel-header">

                    <div>
                        <h2>
                            Issued Cards
                        </h2>

                        <p>
                            Cards currently stored by
                            the payment gateway.
                        </p>
                    </div>

                    <span className="cards-count">
                        {loading
                            ? "Loading..."
                            : `${cards.length} ${
                                cards.length === 1
                                    ? "card"
                                    : "cards"
                            }`}
                    </span>

                </div>

                {/* Loading */}

                {loading && (
                    <div className="cards-loading">
                        Loading cards...
                    </div>
                )}

                {/* Empty State */}

                {!loading &&
                    cards.length === 0 && (
                        <div className="cards-empty-state">

                            <div className="cards-empty-icon">
                                ▣
                            </div>

                            <h3>
                                No cards issued yet
                            </h3>

                            <p>
                                Issue a mock payment card
                                to begin testing the
                                payment lifecycle.
                            </p>

                            <button
                                type="button"
                                className="action-button primary"
                                onClick={openIssueForm}
                            >
                                + Issue First Card
                            </button>

                        </div>
                    )}

                {/* Cards */}

                {!loading &&
                    cards.length > 0 && (
                        <div className="cards-grid">

                            {cards.map((card) => (
                                <article
                                    className="payment-card"
                                    key={card.card_id}
                                >

                                    {/* Card Header */}

                                    <div className="payment-card-top">

                                        <div>
                                            <span className="payment-card-label">
                                                PAYGUARD
                                            </span>

                                            <span className="payment-card-network">
                                                {getNetworkLabel(
                                                    card.network,
                                                )}
                                            </span>
                                        </div>

                                        <span
                                            className={`payment-card-status ${getStatusClass(
                                                card.status,
                                            )}`}
                                        >
                                            <span className="status-dot" />

                                            {card.status}
                                        </span>

                                    </div>

                                    {/* Card Number */}

                                    <div className="payment-card-number">
                                        {maskCardNumber(
                                            card.card_number,
                                        )}
                                    </div>

                                    {/* Card Details */}

                                    <div className="payment-card-details">

                                        <div>
                                            <span>
                                                CARDHOLDER
                                            </span>

                                            <strong>
                                                {
                                                    card.cardholder_name
                                                }
                                            </strong>
                                        </div>

                                        <div>
                                            <span>
                                                EXPIRY
                                            </span>

                                            <strong>
                                                {
                                                    card.expiry_date
                                                }
                                            </strong>
                                        </div>

                                    </div>

                                    {/* Card Footer */}

                                    <div className="payment-card-footer">

                                        <div>
                                            <span>
                                                AVAILABLE
                                            </span>

                                            <strong>
                                                {formatCurrency(
                                                    Number(
                                                        card.balance,
                                                    ),
                                                )}
                                            </strong>
                                        </div>

                                        <span className="payment-card-created">
                                            Issued{" "}
                                            {formatDate(
                                                card.created_at,
                                            )}
                                        </span>

                                    </div>

                                </article>
                            ))}

                        </div>
                    )}

            </section>

        </div>
    )
}