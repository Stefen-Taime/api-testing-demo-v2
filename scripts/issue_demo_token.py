from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.jwt_utils import create_access_token


USERS = {
    "tester": {"role": "tester", "scopes": ["orders:write"]},
    "admin": {"role": "admin", "scopes": ["orders:write", "admin:reset"]},
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a local demo JWT for the API testing stack.")
    parser.add_argument("--user", choices=sorted(USERS), default="tester")
    parser.add_argument("--lifetime-seconds", type=int, default=60 * 60 * 24 * 365 * 50)
    args = parser.parse_args()

    user = USERS[args.user]
    token = create_access_token(
        subject=args.user,
        role=user["role"],
        scopes=user["scopes"],
        secret=os.getenv("AUTH_SHARED_SECRET", "local-dev-shared-secret"),
        issuer=os.getenv("AUTH_ISSUER", "api-testing-auth"),
        audience=os.getenv("AUTH_AUDIENCE", "api-testing-api"),
        lifetime_seconds=args.lifetime_seconds,
    )
    print(token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
