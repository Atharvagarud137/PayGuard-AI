import { useCallback, useEffect, useState } from "react"

import { getCards } from "../services/api"
import type { Card } from "../types/payment"

const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        minimumFractionDigits: 2,
    }).format(amount)
}

const formatDate = (dateString: string): string => {
    const date = new Date(dateString)

    if (Number.isNaN(date.getTime())) {
        return "—"
    }

    return date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
    })
}

const getCardStatusClass = (status: Card["status"]): string => {
    switch (status) {
        case "ACTIVE":
            return "status-success"

        case "INACTIVE":
            return "status-warning"

        case "EXPIRED":
            return "status-danger"

        default:
            return ""
    }
}

const getNetworkClass = (network: Card["network"]): string => {
    switch (network) {
        case "VISA":
            return "card-network visa"

        case "MASTERCARD":
            return "card-network mastercard"

        default:
            return "card-network generic"
    }
}

const maskCardNumber = (cardNumber: string): string => {
    if (!cardNumber) {
        return "•••• •••• •••• ••••"
    }

    return cardNumber.replace(/-/g, " ")
}

export default function Cards() {
    const [cards, setCards] = useState<Card[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

    const loadCards = useCallback(async () => {
        try {
            setLoading(true)
            setError(null)

            const data = await getCards()

            setCards(data)
            setLastUpdated(new Date())
        } catch (err) {
            const message =
                err instanceof Error
                    ? err.message
                    : "Unable to load cards."

            setError(message)
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        void loadCards()
    }, [loadCards])

    const activeCards = cards.filter(
        (card) => card.status === "ACTIVE",
    ).length

    const inactiveCards = cards.filter(
        (card) => card.status === "INACTIVE",
    ).length

    const expiredCards = cards.filter(
        (card) => card.status === "EXPIRED",
    ).length

    const totalBalance = cards.reduce(
        (total, card) => total + Number(card.balance),
        0,
    )

    return (
        <div className="cards-page">
            {error && (
                <div className="dashboard-error">
                    <div>
                        <strong>Unable to load cards</strong>
                        <p>{error}</p>
                    </div>

                    <button
                        type="button"
                        className="action-button"
                        onClick={() => void loadCards()}
                    >
                        Retry
                    </button>
                </div>
            )}

            <section className="stats-grid">
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
                        {loading ? "…" : cards.length}
                    </div>

                    <div className="stat-label">
                        Total Cards
                    </div>

                    <div className="stat-description">
                        cards issued
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
                        {loading ? "…" : activeCards}
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
                        <div className="stat-icon warning">
                            ◷
                        </div>

                        <span className="stat-change warning">
                            INACTIVE
                        </span>
                    </div>

                    <div className="stat-value">
                        {loading ? "…" : inactiveCards}
                    </div>

                    <div className="stat-label">
                        Inactive Cards
                    </div>

                    <div className="stat-description">
                        currently disabled
                    </div>
                </article>

                <article className="stat-card">
                    <div className="stat-card-top">
                        <div className="stat-icon danger">
                            !
                        </div>

                        <span className="stat-change danger">
                            BALANCE
                        </span>
                    </div>

                    <div className="stat-value">
                        {loading
                            ? "…"
                            : formatCurrency(totalBalance)}
                    </div>

                    <div className="stat-label">
                        Available Balance
                    </div>

                    <div className="stat-description">
                        across all cards
                    </div>
                </article>
            </section>

            <section className="panel cards-panel">
                <div className="panel-header">
                    <div>
                        <h2>Payment Cards</h2>

                        <p>
                            Mock cards currently stored by the
                            payment gateway.
                        </p>
                    </div>

                    <button
                        type="button"
                        className="text-button"
                        onClick={() => void loadCards()}
                    >
                        Refresh →
                    </button>
                </div>

                <div className="cards-table-wrapper">
                    <table className="transaction-table cards-table">
                        <thead>
                        <tr>
                            <th>Card</th>
                            <th>Cardholder</th>
                            <th>Network</th>
                            <th>Balance</th>
                            <th>Status</th>
                            <th>Expiry</th>
                            <th>Created</th>
                        </tr>
                        </thead>

                        <tbody>
                        {loading && (
                            <tr>
                                <td colSpan={7}>
                                    <div className="dashboard-table-state">
                                        Loading cards...
                                    </div>
                                </td>
                            </tr>
                        )}

                        {!loading && cards.length === 0 && (
                            <tr>
                                <td colSpan={7}>
                                    <div className="cards-empty-state">
                                        <div className="cards-empty-icon">
                                            ▣
                                        </div>

                                        <strong>
                                            No cards available
                                        </strong>

                                        <p>
                                            Issue a card through the
                                            payment API and refresh
                                            this page to see it here.
                                        </p>
                                    </div>
                                </td>
                            </tr>
                        )}

                        {!loading &&
                            cards.map((card) => (
                                <tr key={card.card_id}>
                                    <td>
                                        <div className="card-number-cell">
                                                <span className="card-chip">
                                                    ▣
                                                </span>

                                            <div>
                                                    <span className="transaction-id">
                                                        {maskCardNumber(
                                                            card.card_number,
                                                        )}
                                                    </span>

                                                <span className="card-id">
                                                        {card.card_id}
                                                    </span>
                                            </div>
                                        </div>
                                    </td>

                                    <td>
                                            <span className="merchant-name">
                                                {card.cardholder_name}
                                            </span>
                                    </td>

                                    <td>
                                            <span
                                                className={getNetworkClass(
                                                    card.network,
                                                )}
                                            >
                                                {card.network}
                                            </span>
                                    </td>

                                    <td>
                                            <span className="transaction-amount">
                                                {formatCurrency(
                                                    Number(card.balance),
                                                )}
                                            </span>
                                    </td>

                                    <td>
                                            <span
                                                className={`transaction-status ${getCardStatusClass(
                                                    card.status,
                                                )}`}
                                            >
                                                <span className="status-dot" />
                                                {card.status}
                                            </span>
                                    </td>

                                    <td>
                                            <span className="transaction-time">
                                                {card.expiry_date}
                                            </span>
                                    </td>

                                    <td>
                                            <span className="transaction-time">
                                                {formatDate(
                                                    card.created_at,
                                                )}
                                            </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {lastUpdated && (
                    <div className="dashboard-last-updated">
                        Last updated{" "}
                        {lastUpdated.toLocaleTimeString()}
                    </div>
                )}
            </section>

            <section className="quick-actions">
                <div>
                    <h2>Card Operations</h2>

                    <p>
                        Card issuance and payment operations are
                        handled through the FastAPI gateway.
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
                        onClick={() => void loadCards()}
                    >
                        Refresh Cards
                    </button>

                    <button
                        type="button"
                        className="action-button"
                        disabled={expiredCards === 0}
                    >
                        Review Expired
                    </button>
                </div>
            </section>
        </div>
    )
}