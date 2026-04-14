from __future__ import annotations


def test_create_order_returns_confirmed_order(client, auth_headers) -> None:
    payload = {
        "item_id": "coffee",
        "quantity": 2,
        "customer_email": "buyer@example.com",
        "notes": "deliver before noon",
    }

    response = client.post("/api/orders", json=payload, headers=auth_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["item_id"] == "coffee"
    assert body["quantity"] == 2
    assert body["customer_email"] == "buyer@example.com"
    assert body["status"] == "confirmed"
    assert body["total_cents"] == 900


def test_invalid_order_payload_is_rejected(client, auth_headers) -> None:
    payload = {
        "item_id": "coffee",
        "quantity": 0,
        "customer_email": "not-an-email",
    }

    response = client.post("/api/orders", json=payload, headers=auth_headers)

    assert response.status_code == 422


def test_can_fetch_created_order_by_id(client, auth_headers) -> None:
    created = client.post(
        "/api/orders",
        json={
            "item_id": "tea",
            "quantity": 1,
            "customer_email": "reader@example.com",
        },
        headers=auth_headers,
    )

    order_id = created.json()["id"]
    fetched = client.get(f"/api/orders/{order_id}")

    assert fetched.status_code == 200
    assert fetched.json()["id"] == order_id
