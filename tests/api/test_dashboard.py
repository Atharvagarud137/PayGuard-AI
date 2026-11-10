from fastapi.testclient import TestClient


def test_dashboard_card_list_reads_from_postgres(
        client: TestClient,
        issued_card: dict,
) -> None:
    response = client.get("/api/v1/cards")

    assert response.status_code == 200

    cards = response.json()
    matching_cards = [
        card
        for card in cards
        if card["card_id"] == issued_card["card_id"]
    ]

    assert len(matching_cards) == 1
    assert matching_cards[0]["card_number"].startswith("****")


def test_dashboard_transaction_list_reads_from_postgres(
        client: TestClient,
        authorized_transaction: dict,
) -> None:
    response = client.get("/api/v1/transactions")

    assert response.status_code == 200

    transactions = response.json()
    matching_transactions = [
        transaction
        for transaction in transactions
        if transaction["transaction_id"]
        == authorized_transaction["transaction_id"]
    ]

    assert len(matching_transactions) == 1
    assert matching_transactions[0]["status"] == "AUTHORIZED"
    assert matching_transactions[0]["history"]


def test_dashboard_summary_counts_postgres_transactions(
        client: TestClient,
        captured_transaction: dict,
) -> None:
    response = client.get("/api/v1/dashboard/summary")

    assert response.status_code == 200

    summary = response.json()

    assert captured_transaction["status"] == "CAPTURED"
    assert summary == {
        "total_transactions": 1,
        "successful": 0,
        "pending": 1,
        "declined": 0,
        "success_rate": 0.0,
    }
