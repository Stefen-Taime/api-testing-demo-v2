from __future__ import annotations

import json
import re


def _extract_bootstrap_json(html: str) -> dict[str, int]:
    match = re.search(
        r'<script id="bootstrap-data" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )
    assert match, "bootstrap payload missing from dashboard"
    return json.loads(match.group(1))


def test_dashboard_page_contains_api_wiring(client) -> None:
    response = client.get("/dashboard")

    assert response.status_code == 200
    html = response.text
    assert 'data-testid="orders-count"' in html
    assert 'fetch("/api/dashboard-data")' in html
    assert 'fetch("/api/orders")' in html


def test_dashboard_bootstrap_updates_when_api_state_changes(client, auth_headers) -> None:
    client.post(
        "/api/orders",
        json={
            "item_id": "coffee",
            "quantity": 1,
            "customer_email": "dashboard@example.com",
        },
        headers=auth_headers,
    )

    html = client.get("/dashboard").text
    bootstrap = _extract_bootstrap_json(html)
    live_summary = client.get("/api/dashboard-data").json()

    assert bootstrap["total_orders"] == 1
    assert bootstrap == live_summary
