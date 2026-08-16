import { useState } from "react"

import Header from "./components/Header"
import Sidebar from "./components/Sidebar"

import Dashboard from "./pages/Dashboard"
import Transactions from "./pages/Transactions"
import Cards from "./pages/Cards"

import "./App.css"

function App() {
    const [
        activePage,
        setActivePage,
    ] = useState("overview")

    return (
        <div className="app-shell">

            <Sidebar
                activePage={activePage}
                onNavigate={setActivePage}
            />

            <main className="main-content">

                <Header
                    activePage={activePage}
                />

                {activePage ===
                    "overview" && (
                        <Dashboard />
                    )}

                {activePage ===
                    "transactions" && (
                        <Transactions />
                    )}

                {activePage ===
                    "cards" && (
                        <Cards />
                    )}

                {activePage ===
                    "ai-insights" && (
                        <div className="placeholder-page ai-placeholder">

                            <div className="placeholder-icon">
                                ✦
                            </div>

                            <h2>
                                AI Insights
                            </h2>

                            <p>
                                AI-powered root cause
                                analysis and test
                                generation will appear
                                here once the AI
                                pipeline is connected.
                            </p>

                        </div>
                    )}

            </main>

        </div>
    )
}

export default App