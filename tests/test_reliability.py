from __future__ import annotations

import pytest


@pytest.mark.reliability
def test_api_stays_consistent_over_repeated_requests(client, auth_headers) -> None:
    for index in range(150):
        health = client.get("/health")
        items = client.get("/api/items")
        orders = client.get("/api/orders")

        assert health.status_code == 200
        assert items.status_code == 200
        assert orders.status_code == 200

        if index % 10 == 0:
            created = client.post(
                "/api/orders",
                json={
                    "item_id": "coffee" if index % 20 == 0 else "tea",
                    "quantity": 1,
                    "customer_email": f"reliability-{index}@example.com",
                },
                headers=auth_headers | {"X-Request-Id": f"reliability-{index}"},
            )
            assert created.status_code in {200, 201}

    summary = client.get("/api/dashboard-data")
    items = client.get("/api/items")

    assert summary.status_code == 200
    assert summary.json()["total_orders"] == summary.json()["total_notifications"] == 15
    assert items.status_code == 200

    items_by_id = {item["id"]: item for item in items.json()}
    assert items_by_id["coffee"]["stock"] == 32
    assert items_by_id["tea"]["stock"] == 28
