const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "./playwright/tests",
  timeout: 30000,
  workers: 1,
  expect: {
    timeout: 5000
  },
  fullyParallel: false,
  use: {
    baseURL: "http://127.0.0.1:8000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure"
  },
  webServer: [
    {
      command: "python3 -m uvicorn services.auth_service.main:app --host 127.0.0.1 --port 8001",
      url: "http://127.0.0.1:8001/health",
      reuseExistingServer: true,
      timeout: 30000,
      env: {
        AUTH_SHARED_SECRET: "local-dev-shared-secret",
        AUTH_ISSUER: "api-testing-auth",
        AUTH_AUDIENCE: "api-testing-api"
      }
    },
    {
      command: "python3 -m uvicorn services.notification_service.main:app --host 127.0.0.1 --port 8002",
      url: "http://127.0.0.1:8002/health",
      reuseExistingServer: true,
      timeout: 30000,
      env: {
        TEST_RESET_API_KEY: "demo-reset-key"
      }
    },
    {
      command: "python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000",
      url: "http://127.0.0.1:8000/health",
      reuseExistingServer: true,
      timeout: 30000,
      env: {
        DATABASE_URL: "sqlite:///./playwright-demo.db",
        AUTH_SHARED_SECRET: "local-dev-shared-secret",
        AUTH_ISSUER: "api-testing-auth",
        AUTH_AUDIENCE: "api-testing-api",
        NOTIFICATION_SERVICE_URL: "http://127.0.0.1:8002",
        TEST_RESET_API_KEY: "demo-reset-key"
      }
    }
  ]
});
