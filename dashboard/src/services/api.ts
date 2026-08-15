import type {
    Card,
    DashboardSummary,
    HealthStatus,
    Transaction,
} from "../types/payment";

const API_BASE_URL = "http://localhost:8000/api/v1";

async function request<T>(
    endpoint: string,
    options: RequestInit = {},
): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...options.headers,
        },
    });

    if (!response.ok) {
        let message = `API request failed with status ${response.status}`;

        try {
            const errorBody = await response.json();

            if (typeof errorBody.detail === "string") {
                message = errorBody.detail;
            }
        } catch {
            // Keep the default error message if the response isn't JSON.
        }

        throw new Error(message);
    }

    return response.json() as Promise<T>;
}

// -----------------------------------------------------------------------------
// Health
// -----------------------------------------------------------------------------

export async function getHealth(): Promise<HealthStatus> {
    const response = await fetch("http://localhost:8000/");

    if (!response.ok) {
        throw new Error("Payment gateway is unavailable");
    }

    const data = await response.json();

    return {
        gateway: {
            status: "operational",
            message: data.message ?? "Payment gateway is running",
        },
    };
}

// -----------------------------------------------------------------------------
// Dashboard
// -----------------------------------------------------------------------------

export async function getDashboardSummary(): Promise<DashboardSummary> {
    return request<DashboardSummary>("/dashboard/summary");
}

// -----------------------------------------------------------------------------
// Transactions
// -----------------------------------------------------------------------------

export async function getTransactions(): Promise<Transaction[]> {
    return request<Transaction[]>("/transactions");
}

export async function getTransaction(
    transactionId: string,
): Promise<Transaction> {
    return request<Transaction>(`/transactions/${transactionId}`);
}

// -----------------------------------------------------------------------------
// Cards
// -----------------------------------------------------------------------------

export async function getCards(): Promise<Card[]> {
    return request<Card[]>("/cards");
}