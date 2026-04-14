from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class InventoryItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    price_cents: int = Field(ge=0)
    stock: int = Field(ge=0)


class OrderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: str = Field(min_length=1)
    quantity: int = Field(ge=1)
    customer_email: str = Field(min_length=5, max_length=254)
    notes: str | None = Field(default=None, max_length=200)

    @field_validator("customer_email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        local, separator, domain = value.strip().lower().partition("@")
        if not separator or "." not in domain or not local or domain.startswith("."):
            raise ValueError("customer_email must look like an email")
        return value.strip().lower()

    @field_validator("notes")
    @classmethod
    def reject_script_payloads(cls, value: str | None) -> str | None:
        if value and "<script" in value.lower():
            raise ValueError("notes contains forbidden content")
        return value


class OrderPublic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    item_id: str
    quantity: int = Field(ge=1)
    customer_email: str
    status: Literal["confirmed"]
    total_cents: int = Field(ge=0)
    created_at: datetime
    request_id: str | None = None


class NotificationEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["order.confirmed"]
    order_id: str
    customer_email: str
    created_at: datetime


class DashboardSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_items: int = Field(ge=0)
    total_orders: int = Field(ge=0)
    total_notifications: int = Field(ge=0)
    low_stock_items: int = Field(ge=0)
