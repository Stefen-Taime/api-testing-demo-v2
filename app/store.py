from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx
from sqlalchemy import delete, func, select

from app.database import Base, SessionLocal, check_database_connection, engine
from app.models import DashboardSummary, InventoryItem, NotificationEvent, OrderCreate, OrderPublic
from app.settings import Settings
from app.sql_models import InventoryItemRecord, NotificationDeliveryRecord, OrderRecord


class ResourceNotFoundError(Exception):
    """Raised when an item or order does not exist."""


class OutOfStockError(Exception):
    """Raised when an order requests more stock than available."""


class NotificationDeliveryError(Exception):
    """Raised when the notification microservice cannot be reached or rejects an event."""


class DatabaseStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def initialize(self) -> None:
        Base.metadata.create_all(bind=engine)
        with SessionLocal.begin() as session:
            existing_items = session.scalar(select(func.count()).select_from(InventoryItemRecord))
            if existing_items == 0:
                self._seed_inventory(session=session, stock_multiplier=1)

    def healthcheck(self) -> None:
        check_database_connection()

    def reset(self, stock_multiplier: int = 1) -> None:
        with SessionLocal.begin() as session:
            session.execute(delete(NotificationDeliveryRecord))
            session.execute(delete(OrderRecord))
            session.execute(delete(InventoryItemRecord))
            self._seed_inventory(session=session, stock_multiplier=stock_multiplier)

    def list_items(self) -> list[InventoryItem]:
        with SessionLocal() as session:
            items = session.scalars(select(InventoryItemRecord).order_by(InventoryItemRecord.id)).all()
            return [self._to_inventory_item(item) for item in items]

    def get_item(self, item_id: str) -> InventoryItem:
        with SessionLocal() as session:
            item = session.get(InventoryItemRecord, item_id)
            if item is None:
                raise ResourceNotFoundError(f"Unknown item: {item_id}")
            return self._to_inventory_item(item)

    def list_orders(self) -> list[OrderPublic]:
        with SessionLocal() as session:
            orders = session.scalars(select(OrderRecord).order_by(OrderRecord.id)).all()
            return [self._to_order_public(order) for order in orders]

    def get_order(self, order_id: str) -> OrderPublic:
        with SessionLocal() as session:
            order = session.scalar(select(OrderRecord).where(OrderRecord.public_id == order_id))
            if order is None:
                raise ResourceNotFoundError(f"Unknown order: {order_id}")
            return self._to_order_public(order)

    def create_order(self, payload: OrderCreate, request_id: str | None = None) -> tuple[OrderPublic, bool]:
        normalized_request_id = request_id.strip() if request_id and request_id.strip() else None

        with SessionLocal.begin() as session:
            if normalized_request_id:
                existing_order = session.scalar(
                    select(OrderRecord).where(OrderRecord.request_id == normalized_request_id)
                )
                if existing_order is not None:
                    return self._to_order_public(existing_order), False

            item = session.get(InventoryItemRecord, payload.item_id)
            if item is None:
                raise ResourceNotFoundError(f"Unknown item: {payload.item_id}")
            if item.stock < payload.quantity:
                raise OutOfStockError(
                    f"Insufficient stock for item {payload.item_id}: requested {payload.quantity}, available {item.stock}"
                )

            now = datetime.now(timezone.utc)
            item.stock -= payload.quantity
            order = OrderRecord(
                public_id="",
                item_id=payload.item_id,
                quantity=payload.quantity,
                customer_email=payload.customer_email,
                status="confirmed",
                total_cents=item.price_cents * payload.quantity,
                created_at=now,
                request_id=normalized_request_id,
            )
            session.add(order)
            session.flush()
            order.public_id = f"ord-{order.id:04d}"

            event = NotificationEvent(
                kind="order.confirmed",
                order_id=order.public_id,
                customer_email=payload.customer_email,
                created_at=now,
            )
            notification_response = self._send_notification(event)
            session.add(
                NotificationDeliveryRecord(
                    kind=event.kind,
                    order_id=event.order_id,
                    customer_email=event.customer_email,
                    created_at=event.created_at,
                    response_payload=json.dumps(notification_response, separators=(",", ":"), sort_keys=True),
                )
            )

            return self._to_order_public(order), True

    def summary(self) -> DashboardSummary:
        with SessionLocal() as session:
            total_items = session.scalar(select(func.count()).select_from(InventoryItemRecord)) or 0
            total_orders = session.scalar(select(func.count()).select_from(OrderRecord)) or 0
            total_notifications = session.scalar(select(func.count()).select_from(NotificationDeliveryRecord)) or 0
            low_stock_items = (
                session.scalar(
                    select(func.count()).select_from(InventoryItemRecord).where(InventoryItemRecord.stock < 5)
                )
                or 0
            )
            return DashboardSummary(
                total_items=int(total_items),
                total_orders=int(total_orders),
                total_notifications=int(total_notifications),
                low_stock_items=int(low_stock_items),
            )

    def snapshot(self) -> dict[str, object]:
        with SessionLocal() as session:
            inventory = session.scalars(select(InventoryItemRecord).order_by(InventoryItemRecord.id)).all()
            orders = session.scalars(select(OrderRecord).order_by(OrderRecord.id)).all()
            notifications = session.scalars(
                select(NotificationDeliveryRecord).order_by(NotificationDeliveryRecord.id)
            ).all()
            return {
                "inventory": {item.id: self._to_inventory_item(item).model_dump(mode="json") for item in inventory},
                "orders": [self._to_order_public(order).model_dump(mode="json") for order in orders],
                "outbox": [
                    NotificationEvent(
                        kind=notification.kind,
                        order_id=notification.order_id,
                        customer_email=notification.customer_email,
                        created_at=notification.created_at,
                    ).model_dump(mode="json")
                    for notification in notifications
                ],
                "request_index": {
                    order.request_id: order.public_id for order in orders if order.request_id is not None
                },
            }

    def _send_notification(self, event: NotificationEvent) -> dict[str, object]:
        if not self.settings.notification_service_url:
            return {"status": "skipped", "provider": "local-noop"}

        endpoint = f"{self.settings.notification_service_url.rstrip('/')}/notifications"
        try:
            response = httpx.post(
                endpoint,
                json=event.model_dump(mode="json"),
                timeout=self.settings.notification_service_timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise NotificationDeliveryError(f"Failed to deliver notification to {endpoint}") from exc

        payload = response.json()
        if not isinstance(payload, dict):
            return {"status": "accepted", "provider": "notification-service"}
        return payload

    def _seed_inventory(self, session, stock_multiplier: int) -> None:
        multiplier = max(1, stock_multiplier)
        session.add_all(
            [
                InventoryItemRecord(id="coffee", name="House Coffee", price_cents=450, stock=40 * multiplier),
                InventoryItemRecord(id="tea", name="Black Tea", price_cents=320, stock=35 * multiplier),
                InventoryItemRecord(id="cookie", name="Butter Cookie", price_cents=220, stock=25 * multiplier),
            ]
        )

    @staticmethod
    def _to_inventory_item(item: InventoryItemRecord) -> InventoryItem:
        return InventoryItem(id=item.id, name=item.name, price_cents=item.price_cents, stock=item.stock)

    @staticmethod
    def _to_order_public(order: OrderRecord) -> OrderPublic:
        return OrderPublic(
            id=order.public_id,
            item_id=order.item_id,
            quantity=order.quantity,
            customer_email=order.customer_email,
            status=order.status,
            total_cents=order.total_cents,
            created_at=order.created_at,
            request_id=order.request_id,
        )
