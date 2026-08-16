import type {
    Card,
    DashboardSummary,
    HealthStatus,
    Transaction,
} from "../types/payment"

const API_BASE_URL =
    "http://localhost:8000/api/v1"

async function request<T>(
    endpoint: string,
    options: RequestInit = {},
): Promise<T> {
    const response = await fetch(
        `${API_BASE_URL}${endpoint}`,
        {
            ...options,
            headers: {
                "Content-Type": "application/json",
                ...options.headers,
            },
        },
    )

    if (!response.ok) {
        let message =
            `API request failed with status ${response.status}`

        try {
            const errorBody =
                await response.json()

            if (
                typeof errorBody.detail ===
                "string"
            ) {
                message =
                    errorBody.detail
            }
        } catch {
            // Keep the default message.
        }

        throw new Error(message)
    }

    return response.json() as Promise<T>
}

/* ============================================================================
   Health
   ============================================================================ */

export async function getHealth(): Promise<HealthStatus> {
    const response =
        await fetch("http://localhost:8000/")

    if (!response.ok) {
        throw new Error(
            "Payment gateway is unavailable",
        )
    }

    const data =
        await response.json()

    return {
        gateway: {
            status: "operational",
            message:
                data.message ??
                "Payment gateway is running",
        },
    }
}

/* ============================================================================
   Dashboard
   ============================================================================ */

export async function getDashboardSummary(): Promise<DashboardSummary> {
    return request<DashboardSummary>(
        "/dashboard/summary",
    )
}

/* ============================================================================
   Transactions
   ============================================================================ */

export async function getTransactions(): Promise<Transaction[]> {
    return request<Transaction[]>(
        "/transactions",
    )
}

export async function getTransaction(
    transactionId: string,
): Promise<Transaction> {
    return request<Transaction>(
        `/transactions/${transactionId}`,
    )
}

/* ============================================================================
   Transaction Lifecycle
   ============================================================================ */

export type AuthorizeTransactionRequest = {
    card_id: string
    amount: number
    merchant_id: string
}

export type AuthorizeTransactionResponse = {
    transaction_id: string
    status: Transaction["status"]
    authorized_amount?: number
    decline_reason?: string | null
}

export async function authorizeTransaction(
    data: AuthorizeTransactionRequest,
): Promise<AuthorizeTransactionResponse> {
    return request<AuthorizeTransactionResponse>(
        "/transactions/authorize",
        {
            method: "POST",
            body: JSON.stringify(data),
        },
    )
}

export type CaptureTransactionRequest = {
    capture_amount: number
}

export type CaptureTransactionResponse = {
    transaction_id: string
    status: Transaction["status"]
    captured_amount: number
}

export async function captureTransaction(
    transactionId: string,
    data: CaptureTransactionRequest,
): Promise<CaptureTransactionResponse> {
    return request<CaptureTransactionResponse>(
        `/transactions/${transactionId}/capture`,
        {
            method: "POST",
            body: JSON.stringify(data),
        },
    )
}

export type SettleTransactionResponse = {
    transaction_id: string
    status: Transaction["status"]
    settled_at?: string
}

export async function settleTransaction(
    transactionId: string,
): Promise<SettleTransactionResponse> {
    return request<SettleTransactionResponse>(
        `/transactions/${transactionId}/settle`,
        {
            method: "POST",
        },
    )
}

export type RefundTransactionRequest = {
    refund_amount: number
}

export type RefundTransactionResponse = {
    transaction_id: string
    refund_id: string
    status: Transaction["status"]
    remaining_balance: number
}

export async function refundTransaction(
    transactionId: string,
    data: RefundTransactionRequest,
): Promise<RefundTransactionResponse> {
    return request<RefundTransactionResponse>(
        `/transactions/${transactionId}/refund`,
        {
            method: "POST",
            body: JSON.stringify(data),
        },
    )
}

/* ============================================================================
   Cards
   ============================================================================ */

export async function getCards(): Promise<Card[]> {
    return request<Card[]>("/cards")
}

export type CreateCardRequest = {
    cardholder_name: string
    network: Card["network"]
    initial_balance: number
    expiry_date: string
}

export async function createCard(
    data: CreateCardRequest,
): Promise<Card> {
    return request<Card>("/cards", {
        method: "POST",
        body: JSON.stringify(data),
    })
}