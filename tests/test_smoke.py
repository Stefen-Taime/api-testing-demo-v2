from __future__ import annotations


def test_health_endpoint_is_up(client) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "api-testing-demo-v2"}


def test_items_endpoint_returns_seeded_catalog(client) -> None:
    response = client.get("/api/items")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 3
    assert [item["id"] for item in body] == ["coffee", "cookie", "tea"]
