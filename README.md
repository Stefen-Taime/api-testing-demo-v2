# API Testing Demo V2

This project tells a simple story: a client gets a `JWT`, creates an order through a FastAPI API, the API stores that order in SQL, sends a notification to a dedicated microservice, and a `/dashboard` UI shows the current system state.  
The goal of the repository is to demonstrate, along that same end-to-end flow, **11 types of API testing** with real executions, real outputs, and screenshots embedded directly in this README.

## The Business Scenario

1. The auth service issues a token through `/oauth/token`.
2. The client calls `POST /api/orders` with a `Bearer JWT`.
3. The API stores the order in SQL and decrements inventory.
4. The API calls the notification microservice.
5. The dashboard reads `/api/dashboard-data` and displays the current state.

![Dashboard](./docs/screenshots/dashboard.png)

## The 11 Test Types Covered

| # | Type | What it means in this project |
| --- | --- | --- |
| 1 | `Smoke Testing` | Check that the API starts correctly and answers on its core endpoints. |
| 2 | `Functional Testing` | Validate the expected business behavior for creating and reading orders. |
| 3 | `Integration Testing` | Verify that the API, database, and notification service work together correctly. |
| 4 | `Regression Testing` | Lock down fragile behaviors that must not break over time. |
| 5 | `Load Testing` | Measure behavior under expected traffic. |
| 6 | `Stress Testing` | Push the system harder to observe how it behaves near its limits. |
| 7 | `Security Testing` | Verify authentication, rejection of dangerous payloads, and non-exposure of internal data. |
| 8 | `UI Testing` | Verify that the UI consumes the API correctly and reflects live system state. |
| 9 | `Fuzz Testing` | Send invalid or random inputs to test robustness. |
| 10 | `Reliability Testing` | Verify consistency and stability over repeated requests. |
| 11 | `Contract Testing` | Verify that JSON responses still match the published schemas. |

## Stack

| Component | Role |
| --- | --- |
| `app/main.py` | FastAPI business API |
| `services/auth_service/main.py` | JWT auth service |
| `services/notification_service/main.py` | Notification microservice |
| `SQLite` | Fast local database for non-Docker runs |
| `Postgres` | External database in Docker Compose |
| `Playwright` | Real browser UI testing |
| `JMeter` | Load and stress testing |
| `Docker Compose` | Realistic distributed environment |
| `OWASP ZAP` | Entry point for baseline security scanning |

## Quick Start

Run the API locally:

```bash
make run
```

Run the distributed Docker stack:

```bash
make docker-up
```

Generate a demo token locally:

```bash
make token
```

Run the main test campaigns:

```bash
make test
make test-ui
make load
make stress
```

## Overall Campaign Result

Latest documented local campaign: **April 14, 2026**.

| Verification | Observed result |
| --- | --- |
| API suite | `19 passed in 10.86s` |
| Browser UI suite | `2 passed (8.3s)` |
| Load | `900 samples`, `92.7/s`, `0.00% error` |
| Stress | `4800 samples`, `258.5/s`, `0.00% error` |
| Docker Compose | `config validated` |

![Validation report](./docs/screenshots/validation-report.png)

## How To Read The Test Sections

For the `pytest` suites, [tests/conftest.py](./tests/conftest.py) starts a real local HTTP mini-stack and the tests talk to the application through `httpx`.  
For browser UI validation, the campaign uses [playwright/tests/dashboard.spec.js](./playwright/tests/dashboard.spec.js).  
For performance, the JMeter plans live in [jmeter/load-test-plan.jmx](./jmeter/load-test-plan.jmx) and [jmeter/stress-test-plan.jmx](./jmeter/stress-test-plan.jmx).

## 1. Smoke Testing

- `What we test`: basic API startup and core endpoint availability.
- `Why it matters`: this is the fastest signal that the platform is simply alive.
- `How it is implemented`: [tests/test_smoke.py](./tests/test_smoke.py) calls `/health` and `/api/items`.
- `What it proves`: the API answers through a real HTTP server and returns a coherent seeded catalog.
- `Command`: `make test TEST_ARGS='tests/test_smoke.py -q'`
- `Observed result`: `2 passed in 3.41s`
- `Raw output`: [docs/validation/raw/smoke.txt](./docs/validation/raw/smoke.txt)

![Smoke output](./docs/screenshots/smoke-output.png)

## 2. Functional Testing

- `What we test`: valid order creation, invalid payload rejection, and reading a created order.
- `Why it matters`: the business flow must work before any advanced testing has value.
- `How it is implemented`: [tests/test_functional.py](./tests/test_functional.py) creates an order, expects `201`, then verifies order retrieval and `422` validation failures.
- `What it proves`: the core business behavior matches the expected API contract for a normal client.
- `Command`: `make test TEST_ARGS='tests/test_functional.py -q'`
- `Observed result`: `3 passed in 4.93s`
- `Raw output`: [docs/validation/raw/functional.txt](./docs/validation/raw/functional.txt)

![Functional output](./docs/screenshots/functional-output.png)

## 3. Integration Testing

- `What we test`: coordination between orders, inventory, dashboard summary, and the notification service.
- `Why it matters`: an API can be correct in isolation but fail when real components interact.
- `How it is implemented`: [tests/test_integration.py](./tests/test_integration.py) creates an order, re-reads inventory, re-reads dashboard data, and checks notification effects through the counters.
- `What it proves`: a successful order flows correctly across the whole application chain, not just inside one function.
- `Command`: `make test TEST_ARGS='tests/test_integration.py -q'`
- `Observed result`: `2 passed in 4.75s`
- `Raw output`: [docs/validation/raw/integration.txt](./docs/validation/raw/integration.txt)

![Integration output](./docs/screenshots/integration-output.png)

## 4. Regression Testing

- `What we test`: idempotency and the guarantee that a failed business operation does not mutate inventory.
- `Why it matters`: these are classic behaviors that often break during feature work or refactoring.
- `How it is implemented`: [tests/test_regression.py](./tests/test_regression.py) sends the same request twice with `X-Request-Id`, then verifies that an out-of-stock failure does not change state.
- `What it proves`: the most sensitive order-creation regressions are explicitly locked down.
- `Command`: `make test TEST_ARGS='tests/test_regression.py -q'`
- `Observed result`: `2 passed in 4.83s`
- `Raw output`: [docs/validation/raw/regression.txt](./docs/validation/raw/regression.txt)

![Regression output](./docs/screenshots/regression-output.png)

## 5. Load Testing

- `What we test`: API behavior under expected traffic.
- `Why it matters`: a system should stay smooth under realistic usage, not only in an idle state.
- `How it is implemented`: [jmeter/load-test-plan.jmx](./jmeter/load-test-plan.jmx) exercises `health`, `items`, and `orders` after resetting demo state.
- `What it proves`: the platform sustains a stable local load with no errors during the documented run.
- `Command`: `jmeter -n -t jmeter/load-test-plan.jmx -l docs/validation/raw/load-results.jtl`
- `Observed result`: `900 samples`, `93.2/s`, `0.00% error`
- `Raw output`: [docs/validation/raw/load.txt](./docs/validation/raw/load.txt)

![Load output](./docs/screenshots/load-output.png)

## 6. Stress Testing

- `What we test`: API behavior under a stronger and more aggressive workload.
- `Why it matters`: stress testing looks for the edge of the system and how it behaves under pressure.
- `How it is implemented`: [jmeter/stress-test-plan.jmx](./jmeter/stress-test-plan.jmx) increases the workload after resetting state with larger stock levels.
- `What it proves`: the system remains coherent and completes the documented local stress campaign without errors.
- `Command`: `jmeter -n -t jmeter/stress-test-plan.jmx -l docs/validation/raw/stress-results.jtl`
- `Observed result`: `4800 samples`, `271.1/s`, `0.00% error`
- `Raw output`: [docs/validation/raw/stress.txt](./docs/validation/raw/stress.txt)

![Stress output](./docs/screenshots/stress-output.png)

## 7. Security Testing

- `What we test`: mandatory `Bearer JWT` authentication, rejection of a bad token, blocking of scripted payloads, and non-leakage of internal fields.
- `Why it matters`: an order API must not allow anonymous writes or expose internal structure details.
- `How it is implemented`: [tests/test_security.py](./tests/test_security.py) calls `POST /api/orders` with and without authentication, then injects malicious content into `notes`.
- `What it proves`: the write surface is protected and defensive validation works on the critical cases covered by the demo.
- `Command`: `make test TEST_ARGS='tests/test_security.py -q'`
- `Observed result`: `4 passed in 4.78s`
- `Raw output`: [docs/validation/raw/security.txt](./docs/validation/raw/security.txt)

![Security output](./docs/screenshots/security-output.png)

## 8. UI Testing

- `What we test`: the link between the `/dashboard` interface and the API, first at the HTML/JS level and then in a real browser.
- `Why it matters`: a backend can be correct while the screen integration is still wrong.
- `How it is implemented`: [tests/test_ui.py](./tests/test_ui.py) checks HTTP wiring and bootstrap data; [playwright/tests/dashboard.spec.js](./playwright/tests/dashboard.spec.js) opens Chromium and verifies that the screen updates after a real API order.
- `What it proves`: the dashboard really consumes the API and reflects an order created in the system.
- `HTTP command`: `make test TEST_ARGS='tests/test_ui.py -q'`
- `HTTP result`: `2 passed in 4.78s`
- `HTTP raw output`: [docs/validation/raw/ui-http.txt](./docs/validation/raw/ui-http.txt)
- `Browser command`: `npm run ui:test -- --reporter=line`
- `Browser result`: `2 passed (6.4s)`
- `Browser raw output`: [docs/validation/raw/ui-browser.txt](./docs/validation/raw/ui-browser.txt)

![UI HTTP output](./docs/screenshots/ui-http-output.png)

![UI Browser output](./docs/screenshots/ui-browser-output.png)

## 9. Fuzz Testing

- `What we test`: API robustness against absurd, random, or invalid values.
- `Why it matters`: a robust API should reject unexpected inputs cleanly instead of crashing or drifting into bad state.
- `How it is implemented`: [tests/test_fuzz.py](./tests/test_fuzz.py) sends 60 varied payloads with allowed statuses in `{404, 409, 422}`.
- `What it proves`: the API remains defensive and returns controlled errors for unreliable input.
- `Command`: `make test TEST_ARGS='tests/test_fuzz.py -q'`
- `Observed result`: `1 passed in 4.52s`
- `Raw output`: [docs/validation/raw/fuzz.txt](./docs/validation/raw/fuzz.txt)

![Fuzz output](./docs/screenshots/fuzz-output.png)

## 10. Reliability Testing

- `What we test`: consistency under repeated requests over a longer run than the other suites.
- `Why it matters`: some failures only appear after many operations accumulate.
- `How it is implemented`: [tests/test_reliability.py](./tests/test_reliability.py) loops across `health`, `items`, `orders`, and periodically creates idempotent orders.
- `What it proves`: final counters, stock levels, and notifications remain coherent after many calls.
- `Command`: `make test TEST_ARGS='tests/test_reliability.py -q'`
- `Observed result`: `1 passed in 6.20s`
- `Raw output`: [docs/validation/raw/reliability.txt](./docs/validation/raw/reliability.txt)

![Reliability output](./docs/screenshots/reliability-output.png)

## 11. Contract Testing

- `What we test`: JSON response compliance against published schemas.
- `Why it matters`: API consumers depend on response structure, not only on HTTP status codes.
- `How it is implemented`: [tests/test_contract.py](./tests/test_contract.py) validates responses against [contracts/order.schema.json](./contracts/order.schema.json) and [contracts/order-list.schema.json](./contracts/order-list.schema.json).
- `What it proves`: response shape is stabilized for clients that consume the API.
- `Command`: `make test TEST_ARGS='tests/test_contract.py -q'`
- `Observed result`: `2 passed in 4.71s`
- `Raw output`: [docs/validation/raw/contract.txt](./docs/validation/raw/contract.txt)

![Contract output](./docs/screenshots/contract-output.png)

## What This Project Demonstrates

- An API tested through a real HTTP server rather than only through an in-memory client.
- Real `JWT Bearer` authentication on write operations.
- Multi-service integration with SQL persistence and notification delivery.
- A clear educational walkthrough of 11 major API testing types.
- Real execution screenshots embedded directly in the documentation.

## Current Limits

- Local non-Docker runs use `SQLite`, not `Postgres`.
- The JWT flow is real, but it does not yet use a full OIDC provider such as Keycloak.
- The `ZAP` entry point is useful for baseline scanning, but it is not a full offensive security audit.
- The notification service stays intentionally simple to keep the demo readable.

## Useful Files

- API: [app/main.py](./app/main.py)
- Persistence: [app/store.py](./app/store.py)
- Auth: [services/auth_service/main.py](./services/auth_service/main.py)
- Notification: [services/notification_service/main.py](./services/notification_service/main.py)
- Docker config: [docker-compose.yml](./docker-compose.yml)
- Makefile: [Makefile](./Makefile)
