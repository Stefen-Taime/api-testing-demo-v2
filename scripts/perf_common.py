from __future__ import annotations

import asyncio
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import app, store
from app.settings import get_settings
from shared.jwt_utils import create_access_token

SETTINGS = get_settings()
DEMO_BEARER_TOKEN = create_access_token(
    subject="perf-tester",
    role="tester",
    scopes=["orders:write"],
    secret=SETTINGS.auth_shared_secret,
    issuer=SETTINGS.auth_issuer,
    audience=SETTINGS.auth_audience,
    lifetime_seconds=60 * 60 * 24 * 365 * 50,
)


@dataclass
class ScenarioResult:
    total_requests: int
    successes: int
    failures: int
    average_ms: float
    p95_ms: float
    max_ms: float

    @property
    def failure_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.failures / self.total_requests

    def as_dict(self) -> dict[str, float | int]:
        return {
            "total_requests": self.total_requests,
            "successes": self.successes,
            "failures": self.failures,
            "failure_rate": round(self.failure_rate, 4),
            "average_ms": round(self.average_ms, 2),
            "p95_ms": round(self.p95_ms, 2),
            "max_ms": round(self.max_ms, 2),
        }


def p95(values: list[float]) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    values = sorted(values)
    index = max(0, round(0.95 * (len(values) - 1)))
    return values[index]


async def run_scenario(total_requests: int, concurrency: int, order_ratio: int = 4) -> ScenarioResult:
    store.reset(stock_multiplier=max(10, total_requests))
    semaphore = asyncio.Semaphore(max(1, concurrency))
    transport = httpx.ASGITransport(app=app)
    latencies: list[float] = []
    successes = 0
    failures = 0

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        async def issue_request(index: int) -> None:
            nonlocal successes, failures
            async with semaphore:
                started = perf_counter()
                if index % order_ratio == 0:
                    response = await client.post(
                        "/api/orders",
                        json={
                            "item_id": "coffee" if index % 2 == 0 else "tea",
                            "quantity": 1,
                            "customer_email": f"perf-{index}@example.com",
                        },
                        headers={
                            "Authorization": f"Bearer {DEMO_BEARER_TOKEN}",
                            "X-Request-Id": f"perf-{index}",
                        },
                    )
                elif index % 2 == 0:
                    response = await client.get("/api/items")
                else:
                    response = await client.get("/health")

                latencies.append((perf_counter() - started) * 1000)
                if response.status_code in {200, 201}:
                    successes += 1
                else:
                    failures += 1

        await asyncio.gather(*(issue_request(index) for index in range(total_requests)))

    average = statistics.fmean(latencies) if latencies else 0.0
    return ScenarioResult(
        total_requests=total_requests,
        successes=successes,
        failures=failures,
        average_ms=average,
        p95_ms=p95(latencies),
        max_ms=max(latencies) if latencies else 0.0,
    )
