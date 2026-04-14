from __future__ import annotations

import json
from pathlib import Path

from jsonschema import validate


ROOT = Path(__file__).resolve().parents[1]


def test_single_order_response_matches_contract(client, auth_headers) -> None:
    schema = json.loads((ROOT / "contracts" / "order.schema.json").read_text())
    created = client.post(
        "/api/orders",
        json={
            "item_id": "tea",
            "quantity": 2,
            "customer_email": "contract@example.com",
        },
        headers=auth_headers,
    )

    assert created.status_code == 201
    validate(instance=created.json(), schema=schema)


def test_order_collection_matches_contract(client, auth_headers) -> None:
    schema = json.loads((ROOT / "contracts" / "order-list.schema.json").read_text())
    client.post(
        "/api/orders",
        json={
            "item_id": "coffee",
            "quantity": 1,
            "customer_email": "first@example.com",
        },
        headers=auth_headers,
    )
    client.post(
        "/api/orders",
        json={
            "item_id": "cookie",
            "quantity": 2,
            "customer_email": "second@example.com",
        },
        headers=auth_headers,
    )

    response = client.get("/api/orders")

    assert response.status_code == 200
    validate(instance=response.json(), schema=schema)
