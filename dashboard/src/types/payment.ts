export type CardNetwork =
    | "VISA"
    | "MASTERCARD"
    | "GENERIC"

export type CardStatus =
    | "ACTIVE"
    | "INACTIVE"
    | "EXPIRED"

export type TransactionStatus =
    | "AUTHORIZED"
    | "DECLINED"
    | "CAPTURED"
    | "SETTLED"
    | "REFUNDED"
    | "PARTIALLY_REFUNDED"

export interface Card {
    card_id: string
    cardholder_name: string
    card_number: string
    network: CardNetwork
    balance: number
    status: CardStatus
    expiry_date: string
    created_at: string
}

export interface TransactionEvent {
    status: TransactionStatus
    timestamp: string
    detail?: string | null
}

export interface Transaction {
    transaction_id: string
    card_id: string
    merchant_id?: string | null

    authorized_amount: number
    captured_amount: number
    settled_amount: number
    refunded_amount: number

    status: TransactionStatus

    decline_reason?: string | null

    history: TransactionEvent[]

    created_at: string
}

export interface DashboardSummary {
    total_transactions: number
    successful: number
    pending: number
    declined: number
    success_rate: number
}

export interface GatewayHealth {
    status:
        | "operational"
        | "degraded"
        | "down"

    message: string
}

export interface HealthStatus {
    gateway: GatewayHealth
}