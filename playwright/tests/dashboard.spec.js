const { test, expect } = require("@playwright/test");

const resetKey = "demo-reset-key";

async function fetchAccessToken(request) {
  const response = await request.post("http://127.0.0.1:8001/oauth/token", {
    data: {
      username: "tester",
      password: "tester-password"
    }
  });

  expect(response.ok()).toBeTruthy();
  const body = await response.json();
  return body.access_token;
}

test.describe("Dashboard UI", () => {
  test.beforeEach(async ({ request }) => {
    const resetState = await request.post("/api/test/reset", {
      headers: {
        "X-Test-Reset-Key": resetKey
      }
    });

    const resetNotifications = await request.post("http://127.0.0.1:8002/test/reset", {
      headers: {
        "X-Test-Reset-Key": resetKey
      }
    });

    expect(resetState.ok()).toBeTruthy();
    expect(resetNotifications.ok()).toBeTruthy();
  });

  test("loads the dashboard and renders API-backed counters", async ({ page }) => {
    await page.goto("/dashboard");

    await expect(page.getByRole("heading", { name: "API Testing Demo Dashboard" })).toBeVisible();
    await expect(page.locator('[data-testid="items-count"]')).toHaveText("3");
    await expect(page.locator('[data-testid="orders-count"]')).toHaveText("0");
    await expect(page.locator('[data-testid="notifications-count"]')).toHaveText("0");
    await expect(page.locator("#orders-json")).toContainText("[]");
  });

  test("reflects an order created through the real API", async ({ page, request }) => {
    const accessToken = await fetchAccessToken(request);
    const createOrder = await request.post("/api/orders", {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "X-Request-Id": "playwright-order-1"
      },
      data: {
        item_id: "coffee",
        quantity: 1,
        customer_email: "playwright@example.com"
      }
    });

    expect(createOrder.ok()).toBeTruthy();

    await page.goto("/dashboard");

    await expect(page.locator('[data-testid="orders-count"]')).toHaveText("1");
    await expect(page.locator('[data-testid="notifications-count"]')).toHaveText("1");
    await expect(page.locator("#orders-json")).toContainText("playwright@example.com");
    await expect(page.locator("#orders-json")).toContainText("\"status\": \"confirmed\"");
  });
});
