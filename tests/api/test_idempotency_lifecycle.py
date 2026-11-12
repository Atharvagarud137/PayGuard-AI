def test_settlement_idempotency_replays_original_response(
        client,
        captured_transaction,
):
    transaction_id = captured_transaction["transaction_id"]
    headers = {"Idempotency-Key": "settlement-replay-001"}
    path = f"/api/v1/transactions/{transaction_id}/settle"

    first = client.post(path, headers=headers)
    second = client.post(path, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json() == first.json()


def test_settlement_idempotency_rejects_a_different_transaction(
        client,
        captured_transaction,
        issued_card,
):
    first_id = captured_transaction["transaction_id"]
    headers = {"Idempotency-Key": "settlement-conflict-001"}

    first = client.post(
        f"/api/v1/transactions/{first_id}/settle",
        headers=headers,
    )

    authorization = client.post(
        "/api/v1/transactions/authorize",
        json={
            "card_id": issued_card["card_id"],
            "amount": "500.00",
            "merchant_id": "merchant-idempotency-second",
        },
    )
    assert authorization.status_code == 200
    second_id = authorization.json()["transaction_id"]

    capture = client.post(
        f"/api/v1/transactions/{second_id}/capture",
        json={"capture_amount": "500.00"},
    )
    assert capture.status_code == 200

    second = client.post(
        f"/api/v1/transactions/{second_id}/settle",
        headers=headers,
    )

    assert first.status_code == 200
    assert second.status_code == 409


def test_refund_idempotency_replays_original_response(
        client,
        settled_transaction,
):
    transaction_id = settled_transaction["transaction_id"]
    headers = {"Idempotency-Key": "refund-replay-001"}
    path = f"/api/v1/transactions/{transaction_id}/refund"
    payload = {"refund_amount": "250.00"}

    first = client.post(path, json=payload, headers=headers)
    second = client.post(path, json=payload, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json() == first.json()


def test_refund_idempotency_rejects_a_different_amount(
        client,
        settled_transaction,
):
    transaction_id = settled_transaction["transaction_id"]
    path = f"/api/v1/transactions/{transaction_id}/refund"
    headers = {"Idempotency-Key": "refund-conflict-001"}

    first = client.post(
        path,
        json={"refund_amount": "100.00"},
        headers=headers,
    )
    second = client.post(
        path,
        json={"refund_amount": "200.00"},
        headers=headers,
    )

    assert first.status_code == 200
    assert second.status_code == 409
