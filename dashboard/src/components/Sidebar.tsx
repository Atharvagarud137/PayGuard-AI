interface SidebarProps {
    activePage: string
    onNavigate: (page: string) => void
}

const navigationItems = [
    {
        id: "overview",
        label: "Overview",
        icon: "⌂",
    },
    {
        id: "transactions",
        label: "Transactions",
        icon: "⇄",
    },
    {
        id: "cards",
        label: "Cards",
        icon: "▣",
    },
    {
        id: "ai-insights",
        label: "AI Insights",
        icon: "✦",
    },
]

export default function Sidebar({
                                    activePage,
                                    onNavigate,
                                }: SidebarProps) {
    return (
        <aside className="sidebar">
            <div className="sidebar-brand">
                <div className="brand-mark">P</div>

                <div>
                    <div className="brand-name">PayGuard</div>
                    <div className="brand-subtitle">AI PAYMENT CONTROL</div>
                </div>
            </div>

            <nav className="sidebar-navigation">
                <div className="navigation-label">WORKSPACE</div>

                {navigationItems.map((item) => (
                    <button
                        key={item.id}
                        type="button"
                        className={`navigation-item ${
                            activePage === item.id ? "active" : ""
                        }`}
                        onClick={() => onNavigate(item.id)}
                    >
                        <span className="navigation-icon">{item.icon}</span>
                        <span>{item.label}</span>
                    </button>
                ))}
            </nav>

            <div className="sidebar-bottom">
                <div className="environment-card">
                    <div className="environment-status">
                        <span className="status-dot online" />
                        <span>Gateway Online</span>
                    </div>

                    <div className="environment-url">
                        localhost:8000
                    </div>
                </div>

                <div className="sidebar-footer">
                    <span>PayGuard AI</span>
                    <span>v1.0.0</span>
                </div>
            </div>
        </aside>
    )
}