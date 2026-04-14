from __future__ import annotations

import random
import string


def _random_text(length: int) -> str:
    alphabet = string.ascii_letters + string.digits + "<>{}[]!?"
    return "".join(random.choice(alphabet) for _ in range(length))


def test_random_invalid_payloads_do_not_crash_the_api(client, auth_headers) -> None:
    random.seed(42)
    allowed_statuses = {404, 409, 422}

    for index in range(60):
        payload = {
            "item_id": random.choice(["coffee", "tea", "cookie", _random_text(5)]),
            "quantity": random.choice([-5, -1, 0, 1, 50, _random_text(2)]),
            "customer_email": random.choice(
                [
                    "valid@example.com",
                    "missing-at-symbol",
                    _random_text(12),
                    "",
                ]
            ),
            "notes": random.choice(
                [
                    None,
                    _random_text(20),
                    "<script>alert(1)</script>",
                ]
            ),
        }

        response = client.post("/api/orders", json=payload, headers=auth_headers)
        assert response.status_code in allowed_statuses, f"unexpected status on iteration {index}: {response.text}"
