from __future__ import annotations

import argparse
import asyncio
import json

from perf_common import run_scenario


async def main() -> int:
    parser = argparse.ArgumentParser(description="Peak-load stress test for the demo API.")
    parser.add_argument("--start", type=int, default=10, help="Starting concurrency level.")
    parser.add_argument("--step", type=int, default=20, help="Concurrency increment per level.")
    parser.add_argument("--max-concurrency", type=int, default=150, help="Highest concurrency to try.")
    parser.add_argument("--requests-per-level", type=int, default=120, help="Requests executed at each level.")
    parser.add_argument(
        "--failure-threshold",
        type=float,
        default=0.05,
        help="Stop when the failure rate reaches this threshold.",
    )
    args = parser.parse_args()

    report: list[dict[str, float | int]] = []
    for concurrency in range(args.start, args.max_concurrency + 1, args.step):
        result = await run_scenario(
            total_requests=args.requests_per_level,
            concurrency=concurrency,
            order_ratio=3,
        )
        summary = {"concurrency": concurrency, **result.as_dict()}
        report.append(summary)

        if result.failure_rate >= args.failure_threshold:
            print(json.dumps(report, indent=2))
            return 1

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
