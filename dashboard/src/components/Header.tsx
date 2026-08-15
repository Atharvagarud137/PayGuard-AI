interface HeaderProps {
    activePage: string
}

const pageTitles: Record<string, string> = {
    overview: "Overview",
    transactions: "Transactions",
    cards: "Cards",
    "ai-insights": "AI Insights",
}

const pageDescriptions: Record<string, string> = {
    overview: "Monitor payment activity and gateway health.",
    transactions: "Inspect payment lifecycle events and transaction states.",
    cards: "Manage mock cards and available balances.",
    "ai-insights": "Analyze failures and surface intelligent test insights.",
}

export default function Header({ activePage }: HeaderProps) {
    const title = pageTitles[activePage] ?? "Overview"
    const description =
        pageDescriptions[activePage] ??
        "Monitor payment activity and gateway health."

    return (
        <header className="top-header">
            <div className="header-copy">
                <div className="breadcrumb">
                    PayGuard AI <span>/</span> {title}
                </div>

                <h1>{title}</h1>
                <p>{description}</p>
            </div>

            <div className="header-actions">
                <div className="gateway-health">
                    <span className="status-dot online" />
                    <div>
                        <span className="health-label">Gateway</span>
                        <span className="health-value">Operational</span>
                    </div>
                </div>

                <div className="header-divider" />

                <button
                    type="button"
                    className="icon-button"
                    aria-label="Notifications"
                >
                    ♢
                </button>

                <div className="user-avatar">
                    AG
                </div>
            </div>
        </header>
    )
}