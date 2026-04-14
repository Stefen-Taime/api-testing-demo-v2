from __future__ import annotations

import os
from functools import lru_cache

from pydantic import BaseModel


class Settings(BaseModel):
    service_name: str = "api-testing-demo-v2"
    database_url: str = "sqlite:///./api-testing-demo.db"
    auth_shared_secret: str = "local-dev-shared-secret"
    auth_issuer: str = "api-testing-auth"
    auth_audience: str = "api-testing-api"
    notification_service_url: str | None = None
    notification_service_timeout_seconds: float = 5.0
    test_reset_api_key: str = "demo-reset-key"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite:///./api-testing-demo.db"),
        auth_shared_secret=os.getenv("AUTH_SHARED_SECRET", "local-dev-shared-secret"),
        auth_issuer=os.getenv("AUTH_ISSUER", "api-testing-auth"),
        auth_audience=os.getenv("AUTH_AUDIENCE", "api-testing-api"),
        notification_service_url=os.getenv("NOTIFICATION_SERVICE_URL"),
        notification_service_timeout_seconds=float(os.getenv("NOTIFICATION_SERVICE_TIMEOUT_SECONDS", "5")),
        test_reset_api_key=os.getenv("TEST_RESET_API_KEY", "demo-reset-key"),
    )
