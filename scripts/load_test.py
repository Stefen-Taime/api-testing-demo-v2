from __future__ import annotations

import argparse
import asyncio
import json

from perf_common import run_scenario


async def main() -> int:
    parser = argparse.ArgumentParser(description="Expected-load test for the demo API.")
    parser.add_argument("--requests", type=int, default=300, help="Total number of requests to run.")
    parser.add_argument("--concurrency", type=int, default=20, help="Number of concurrent requests.")
    parser.add_argument("--max-p95", type=float, default=250.0, help="Maximum allowed p95 latency in ms.")
    parser.add_argument(
        "--max-failure-rate",
        type=float,
        default=0.01,
        help="Maximum allowed failure rate.",
    )
    args = parser.parse_args()

    result = await run_scenario(total_requests=args.requests, concurrency=args.concurrency)
    print(json.dumps(result.as_dict(), indent=2))

    if result.p95_ms > args.max_p95 or result.failure_rate > args.max_failure_rate:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
