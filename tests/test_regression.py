from __future__ import annotations


def _items_by_id(client) -> dict[str, dict[str, object]]:
    response = client.get("/api/items")
    assert response.status_code == 200
    return {item["id"]: item for item in response.json()}


def test_idempotency_prevents_duplicate_orders(client, auth_headers) -> None:
    headers = auth_headers | {"X-Request-Id": "req-123"}
    payload = {
        "item_id": "tea",
        "quantity": 2,
        "customer_email": "repeat@example.com",
    }

    first = client.post("/api/orders", json=payload, headers=headers)
    second = client.post("/api/orders", json=payload, headers=headers)
    orders = client.get("/api/orders")
    summary = client.get("/api/dashboard-data")
    items = _items_by_id(client)

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert len(orders.json()) == 1
    assert items["tea"]["stock"] == 33
    assert summary.json()["total_notifications"] == 1


def test_failed_order_does_not_change_inventory(client, auth_headers) -> None:
    before_items = _items_by_id(client)

    response = client.post(
        "/api/orders",
        json={
            "item_id": "cookie",
            "quantity": 999,
            "customer_email": "broken@example.com",
        },
        headers=auth_headers,
    )

    after_items = _items_by_id(client)
    orders = client.get("/api/orders")

    assert response.status_code == 409
    assert before_items["cookie"]["stock"] == after_items["cookie"]["stock"]
    assert len(orders.json()) == 0
