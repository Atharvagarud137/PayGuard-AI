import { useState } from "react"

import Header from "./components/Header"
import Sidebar from "./components/Sidebar"
import Dashboard from "./pages/Dashboard"

import "./App.css"

function App() {
  const [activePage, setActivePage] = useState("overview")

  return (
      <div className="app-shell">
        <Sidebar
            activePage={activePage}
            onNavigate={setActivePage}
        />

        <main className="main-content">
          <Header activePage={activePage} />

          {activePage === "overview" && <Dashboard />}

          {activePage === "transactions" && (
              <div className="placeholder-page">
                <div className="placeholder-icon">⇄</div>
                <h2>Transactions</h2>
                <p>
                  Transaction management will be connected to
                  the FastAPI gateway in the next stage.
                </p>
              </div>
          )}

          {activePage === "cards" && (
              <div className="placeholder-page">
                <div className="placeholder-icon">▣</div>
                <h2>Cards</h2>
                <p>
                  Card issuance and balance management will be
                  connected to the payment API next.
                </p>
              </div>
          )}

          {activePage === "ai-insights" && (
              <div className="placeholder-page ai-placeholder">
                <div className="placeholder-icon">✦</div>
                <h2>AI Insights</h2>
                <p>
                  AI-powered root cause analysis and test
                  generation will appear here once the AI
                  pipeline is connected.
                </p>
              </div>
          )}
        </main>
      </div>
  )
}

export default App