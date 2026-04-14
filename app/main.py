from __future__ import annotations

import json
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response, status
from fastapi.responses import HTMLResponse, JSONResponse

from app.models import DashboardSummary, InventoryItem, OrderCreate, OrderPublic
from app.settings import Settings, get_settings
from app.store import DatabaseStore, NotificationDeliveryError, OutOfStockError, ResourceNotFoundError
from shared.jwt_utils import JWTValidationError, decode_access_token, scopes_from_claims

settings = get_settings()
store = DatabaseStore(settings=settings)

app = FastAPI(
    title="API Testing Demo V2",
    version="2.0.0",
    description="A multi-service API testing demo with JWT auth, SQL persistence, and notification delivery.",
)


@app.on_event("startup")
def startup() -> None:
    store.initialize()


def require_test_reset_key(x_test_reset_key: Annotated[str | None, Header()] = None) -> None:
    if x_test_reset_key != settings.test_reset_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid X-Test-Reset-Key header is required",
        )


def require_access_token(
    authorization: Annotated[str | None, Header()] = None,
    required_scope: str = "orders:write",
) -> dict[str, object]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid Bearer token is required",
        )

    token = authorization.removeprefix("Bearer ").strip()
    try:
        claims = decode_access_token(
            token=token,
            secret=settings.auth_shared_secret,
            issuer=settings.auth_issuer,
            audience=settings.auth_audience,
        )
    except JWTValidationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    scopes = scopes_from_claims(claims)
    if required_scope not in scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Token is missing required scope: {required_scope}",
        )
    return claims


def require_write_scope(
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, object]:
    return require_access_token(authorization=authorization, required_scope="orders:write")


@app.exception_handler(ResourceNotFoundError)
async def handle_not_found(_: object, exc: ResourceNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})


@app.exception_handler(OutOfStockError)
async def handle_out_of_stock(_: object, exc: OutOfStockError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})


@app.exception_handler(NotificationDeliveryError)
async def handle_notification_failure(_: object, exc: NotificationDeliveryError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_502_BAD_GATEWAY, content={"detail": str(exc)})


@app.get("/health")
def health() -> dict[str, str]:
    store.healthcheck()
    return {"status": "ok", "service": settings.service_name}


@app.get("/api/items", response_model=list[InventoryItem])
def list_items() -> list[InventoryItem]:
    return store.list_items()


@app.get("/api/orders", response_model=list[OrderPublic])
def list_orders() -> list[OrderPublic]:
    return store.list_orders()


@app.get("/api/orders/{order_id}", response_model=OrderPublic)
def get_order(order_id: str) -> OrderPublic:
    return store.get_order(order_id)


@app.post("/api/orders", response_model=OrderPublic, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    response: Response,
    _: dict[str, object] = Depends(require_write_scope),
    x_request_id: Annotated[str | None, Header()] = None,
) -> OrderPublic:
    order, created = store.create_order(payload=payload, request_id=x_request_id)
    if not created:
        response.status_code = status.HTTP_200_OK
    return order


@app.get("/api/dashboard-data", response_model=DashboardSummary)
def dashboard_data() -> DashboardSummary:
    return store.summary()


@app.post("/api/test/reset", dependencies=[Depends(require_test_reset_key)])
def reset_demo_state(stock_multiplier: int = Query(default=1, ge=1, le=1000)) -> dict[str, int | str]:
    store.reset(stock_multiplier=stock_multiplier)
    return {"status": "reset", "stock_multiplier": stock_multiplier}


@app.get("/api/test/snapshot")
def test_snapshot() -> dict[str, object]:
    return store.snapshot()


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> HTMLResponse:
    summary = store.summary().model_dump(mode="json")
    summary_json = json.dumps(summary)
    html = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>API Testing Demo Dashboard</title>
    <style>
      :root {
        color-scheme: light;
        --bg: #f5efe5;
        --panel: #fffdf8;
        --ink: #1f2937;
        --accent: #0f766e;
        --muted: #6b7280;
        --border: #d6d3d1;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: Georgia, "Times New Roman", serif;
        color: var(--ink);
        background:
          radial-gradient(circle at top left, rgba(15, 118, 110, 0.16), transparent 28rem),
          linear-gradient(180deg, #fcfbf7 0%%, var(--bg) 100%%);
      }
      main {
        max-width: 960px;
        margin: 0 auto;
        padding: 3rem 1.25rem 4rem;
      }
      .hero {
        display: grid;
        gap: 1rem;
        margin-bottom: 2rem;
      }
      .hero h1 {
        margin: 0;
        font-size: clamp(2rem, 4vw, 3.5rem);
        line-height: 1;
      }
      .hero p {
        margin: 0;
        color: var(--muted);
        font-size: 1.05rem;
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 1rem;
      }
      .card {
        border: 1px solid var(--border);
        border-radius: 18px;
        background: var(--panel);
        padding: 1rem;
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.05);
      }
      .label {
        margin: 0 0 0.5rem;
        font-size: 0.8rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--muted);
      }
      .value {
        margin: 0;
        font-size: 2rem;
        color: var(--accent);
      }
      pre {
        margin-top: 1.5rem;
        padding: 1rem;
        border-radius: 18px;
        background: #172026;
        color: #e5f6f4;
        overflow: auto;
      }
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <h1>API Testing Demo Dashboard</h1>
        <p>This page demonstrates the UI layer consuming live API endpoints backed by SQL storage.</p>
      </section>

      <section class="grid">
        <article class="card">
          <p class="label">Items</p>
          <p class="value" data-testid="items-count">0</p>
        </article>
        <article class="card">
          <p class="label">Orders</p>
          <p class="value" data-testid="orders-count">0</p>
        </article>
        <article class="card">
          <p class="label">Notifications</p>
          <p class="value" data-testid="notifications-count">0</p>
        </article>
        <article class="card">
          <p class="label">Low Stock</p>
          <p class="value" data-testid="low-stock-count">0</p>
        </article>
      </section>

      <pre id="orders-json">[]</pre>
      <script id="bootstrap-data" type="application/json">__BOOTSTRAP__</script>
      <script>
        const bootstrap = JSON.parse(document.getElementById("bootstrap-data").textContent);
        const fields = {
          items: document.querySelector('[data-testid="items-count"]'),
          orders: document.querySelector('[data-testid="orders-count"]'),
          notifications: document.querySelector('[data-testid="notifications-count"]'),
          lowStock: document.querySelector('[data-testid="low-stock-count"]')
        };

        function renderSummary(data) {
          fields.items.textContent = data.total_items;
          fields.orders.textContent = data.total_orders;
          fields.notifications.textContent = data.total_notifications;
          fields.lowStock.textContent = data.low_stock_items;
        }

        async function refreshDashboard() {
          renderSummary(bootstrap);
          const [dashboardResponse, ordersResponse] = await Promise.all([
            fetch("/api/dashboard-data"),
            fetch("/api/orders")
          ]);

          const dashboard = await dashboardResponse.json();
          const orders = await ordersResponse.json();
          renderSummary(dashboard);
          document.getElementById("orders-json").textContent = JSON.stringify(orders, null, 2);
        }

        refreshDashboard();
      </script>
    </main>
  </body>
</html>
""".replace("__BOOTSTRAP__", summary_json)
    return HTMLResponse(html)
