from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

TEST_RESET_API_KEY = os.getenv("TEST_RESET_API_KEY", "demo-reset-key")

app = FastAPI(title="API Testing Notification Service", version="1.0.0")
EVENTS: list[dict[str, object]] = []


class NotificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str = Field(min_length=1)
    order_id: str = Field(min_length=1)
    customer_email: str = Field(min_length=5)
    created_at: datetime


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "notification-service"}


@app.post("/notifications")
def create_notification(payload: NotificationRequest) -> dict[str, object]:
    EVENTS.append(
        {
            "kind": payload.kind,
            "order_id": payload.order_id,
            "customer_email": payload.customer_email,
            "created_at": payload.created_at.isoformat(),
            "accepted_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    return {"status": "accepted", "delivered_count": len(EVENTS)}


@app.get("/notifications")
def list_notifications() -> list[dict[str, object]]:
    return EVENTS


@app.post("/test/reset")
def reset_notifications(x_test_reset_key: str | None = Header(default=None)) -> dict[str, str]:
    if x_test_reset_key != TEST_RESET_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid X-Test-Reset-Key header is required",
        )
    EVENTS.clear()
    return {"status": "reset"}
