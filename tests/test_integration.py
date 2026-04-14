from __future__ import annotations


def _items_by_id(client) -> dict[str, dict[str, object]]:
    response = client.get("/api/items")
    assert response.status_code == 200
    return {item["id"]: item for item in response.json()}


def test_order_creation_updates_inventory_and_outbox(client, auth_headers) -> None:
    before_items = _items_by_id(client)
    before_summary = client.get("/api/dashboard-data").json()

    response = client.post(
        "/api/orders",
        json={
            "item_id": "cookie",
            "quantity": 3,
            "customer_email": "ops@example.com",
        },
        headers=auth_headers,
    )

    after_items = _items_by_id(client)
    after_summary = client.get("/api/dashboard-data").json()

    assert response.status_code == 201
    assert before_items["cookie"]["stock"] == 25
    assert after_items["cookie"]["stock"] == 22
    assert before_summary["total_notifications"] == 0
    assert after_summary["total_notifications"] == 1
    assert after_summary["total_orders"] == 1

    orders = client.get("/api/orders")
    assert orders.status_code == 200
    assert orders.json()[0]["id"] == response.json()["id"]


def test_dashboard_summary_reflects_live_order_counts(client, auth_headers) -> None:
    client.post(
        "/api/orders",
        json={
            "item_id": "coffee",
            "quantity": 1,
            "customer_email": "ui@example.com",
        },
        headers=auth_headers,
    )

    response = client.get("/api/dashboard-data")

    assert response.status_code == 200
    assert response.json()["total_orders"] == 1
    assert response.json()["total_notifications"] == 1
