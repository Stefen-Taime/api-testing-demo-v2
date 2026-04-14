from __future__ import annotations


def test_write_endpoint_requires_api_key(client) -> None:
    response = client.post(
        "/api/orders",
        json={
            "item_id": "coffee",
            "quantity": 1,
            "customer_email": "anon@example.com",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "A valid Bearer token is required"


def test_invalid_api_key_is_rejected(client) -> None:
    response = client.post(
        "/api/orders",
        json={
            "item_id": "coffee",
            "quantity": 1,
            "customer_email": "anon@example.com",
        },
        headers={"Authorization": "Bearer wrong-token"},
    )

    assert response.status_code == 401


def test_script_injection_payload_is_blocked(client, auth_headers) -> None:
    response = client.post(
        "/api/orders",
        json={
            "item_id": "tea",
            "quantity": 1,
            "customer_email": "safe@example.com",
            "notes": "<script>alert('xss')</script>",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_response_does_not_leak_internal_fields(client, auth_headers) -> None:
    response = client.post(
        "/api/orders",
        json={
            "item_id": "tea",
            "quantity": 1,
            "customer_email": "safe@example.com",
        },
        headers=auth_headers,
    )

    body = response.json()

    assert response.status_code == 201
    assert "internal_note" not in body
    assert "inventory" not in body
