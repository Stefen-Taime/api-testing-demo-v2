const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "..");
const rawDir = path.join(root, "docs", "validation", "raw");
const validationDir = path.join(root, "docs", "validation");
const screenshotsDir = path.join(root, "docs", "screenshots");

const sections = [
  {
    slug: "smoke",
    title: "Smoke",
    command: "make test TEST_ARGS='tests/test_smoke.py -q'",
    filename: "smoke.txt",
  },
  {
    slug: "functional",
    title: "Functional",
    command: "make test TEST_ARGS='tests/test_functional.py -q'",
    filename: "functional.txt",
  },
  {
    slug: "integration",
    title: "Integration",
    command: "make test TEST_ARGS='tests/test_integration.py -q'",
    filename: "integration.txt",
  },
  {
    slug: "regression",
    title: "Regression",
    command: "make test TEST_ARGS='tests/test_regression.py -q'",
    filename: "regression.txt",
  },
  {
    slug: "security",
    title: "Security",
    command: "make test TEST_ARGS='tests/test_security.py -q'",
    filename: "security.txt",
  },
  {
    slug: "ui-http",
    title: "UI HTTP Wiring",
    command: "make test TEST_ARGS='tests/test_ui.py -q'",
    filename: "ui-http.txt",
  },
  {
    slug: "fuzz",
    title: "Fuzz",
    command: "make test TEST_ARGS='tests/test_fuzz.py -q'",
    filename: "fuzz.txt",
  },
  {
    slug: "reliability",
    title: "Reliability",
    command: "make test TEST_ARGS='tests/test_reliability.py -q'",
    filename: "reliability.txt",
  },
  {
    slug: "contract",
    title: "Contract",
    command: "make test TEST_ARGS='tests/test_contract.py -q'",
    filename: "contract.txt",
  },
  {
    slug: "ui-browser",
    title: "UI Browser Playwright",
    command: "npm run ui:test -- --reporter=line",
    filename: "ui-browser.txt",
  },
  {
    slug: "load",
    title: "Load",
    command: "jmeter -n -t jmeter/load-test-plan.jmx -l docs/validation/raw/load-results.jtl",
    filename: "load.txt",
  },
  {
    slug: "stress",
    title: "Stress",
    command: "jmeter -n -t jmeter/stress-test-plan.jmx -l docs/validation/raw/stress-results.jtl",
    filename: "stress.txt",
  },
];

function stripAnsi(text) {
  return text
    .replace(/\u001b\[[0-9;?]*[ -/]*[@-~]/g, "")
    .replace(/\u001b\][^\u0007]*\u0007/g, "")
    .replace(/\r/g, "");
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function readOutput(filename) {
  const filePath = path.join(rawDir, filename);
  if (!fs.existsSync(filePath)) {
    throw new Error(`Missing raw output file: ${filePath}`);
  }
  return stripAnsi(fs.readFileSync(filePath, "utf8")).trim();
}

function cardHtml(section) {
  return `
    <article class="card">
      <header class="card-header">
        <p class="eyebrow">API Testing Demo</p>
        <h1>${escapeHtml(section.title)}</h1>
        <p class="command">$ ${escapeHtml(section.command)}</p>
      </header>
      <pre>${escapeHtml(section.output)}</pre>
    </article>`;
}

function buildCardPage(section) {
  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>${escapeHtml(section.title)} Output</title>
    <style>
      :root {
        --bg: #0b1324;
        --bg-glow: rgba(34, 197, 94, 0.16);
        --panel: rgba(15, 23, 42, 0.9);
        --panel-strong: rgba(17, 24, 39, 0.96);
        --ink: #e2ecff;
        --muted: #9fb2d1;
        --accent: #22c55e;
        --border: rgba(159, 178, 209, 0.18);
        --shadow: 0 32px 70px rgba(0, 0, 0, 0.42);
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        min-height: 100vh;
        padding: 28px;
        color: var(--ink);
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        background:
          radial-gradient(circle at top left, var(--bg-glow), transparent 26rem),
          radial-gradient(circle at bottom right, rgba(56, 189, 248, 0.12), transparent 34rem),
          var(--bg);
      }
      .card {
        width: min(1400px, calc(100vw - 56px));
        margin: 0 auto;
        border: 1px solid var(--border);
        border-radius: 24px;
        overflow: hidden;
        background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02));
        box-shadow: var(--shadow);
      }
      .card-header {
        display: grid;
        gap: 10px;
        padding: 22px 24px 18px;
        background: linear-gradient(180deg, rgba(23, 32, 51, 0.96), var(--panel-strong));
        border-bottom: 1px solid var(--border);
      }
      .eyebrow {
        margin: 0;
        color: var(--accent);
        font-size: 12px;
        letter-spacing: 0.12em;
        text-transform: uppercase;
      }
      h1 {
        margin: 0;
        font-size: 30px;
        line-height: 1.05;
      }
      .command {
        margin: 0;
        color: #c7d7f3;
        font-size: 13px;
        white-space: pre-wrap;
      }
      pre {
        margin: 0;
        padding: 24px;
        background: rgba(10, 15, 28, 0.92);
        color: #dbeafe;
        font-size: 14px;
        line-height: 1.5;
        white-space: pre-wrap;
        word-break: break-word;
      }
    </style>
  </head>
  <body>
    ${cardHtml(section)}
  </body>
</html>`;
}

function buildReportPage(allSections) {
  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Validation Captures</title>
    <style>
      :root {
        --bg: #0f172a;
        --panel: #111827;
        --panel-alt: #172033;
        --ink: #e5eefc;
        --muted: #9fb2d1;
        --accent: #22c55e;
        --border: rgba(159, 178, 209, 0.18);
        --shadow: 0 28px 60px rgba(0, 0, 0, 0.35);
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        color: var(--ink);
        background:
          radial-gradient(circle at top left, rgba(34, 197, 94, 0.14), transparent 24rem),
          radial-gradient(circle at bottom right, rgba(59, 130, 246, 0.18), transparent 30rem),
          var(--bg);
      }
      main {
        width: min(1480px, calc(100vw - 48px));
        margin: 0 auto;
        padding: 32px 0 56px;
      }
      .hero {
        display: grid;
        gap: 10px;
        margin-bottom: 22px;
      }
      .eyebrow {
        margin: 0;
        color: var(--accent);
        font-size: 13px;
        letter-spacing: 0.12em;
        text-transform: uppercase;
      }
      h1 {
        margin: 0;
        font-size: 34px;
        line-height: 1.05;
      }
      .sub {
        margin: 0;
        color: var(--muted);
        font-size: 15px;
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 18px;
      }
      .card {
        border: 1px solid var(--border);
        border-radius: 22px;
        overflow: hidden;
        background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02));
        box-shadow: var(--shadow);
      }
      .card-header {
        display: grid;
        gap: 8px;
        padding: 18px 20px 16px;
        background: linear-gradient(180deg, rgba(23, 32, 51, 0.92), rgba(17, 24, 39, 0.96));
        border-bottom: 1px solid var(--border);
      }
      .card-header h2 {
        margin: 0;
        font-size: 20px;
      }
      .command {
        margin: 0;
        color: #c7d7f3;
        font-size: 13px;
        white-space: pre-wrap;
      }
      pre {
        margin: 0;
        padding: 20px;
        min-height: 340px;
        background: rgba(10, 15, 28, 0.92);
        color: #dbeafe;
        font-size: 13px;
        line-height: 1.45;
        white-space: pre-wrap;
        word-break: break-word;
      }
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <p class="eyebrow">API Testing Demo</p>
        <h1>Validation Command Outputs</h1>
        <p class="sub">Captured from real local executions on April 14, 2026.</p>
      </section>
      <section class="grid">
        ${allSections
          .map(
            (section) => `
        <article class="card">
          <header class="card-header">
            <h2>${escapeHtml(section.title)}</h2>
            <p class="command">$ ${escapeHtml(section.command)}</p>
          </header>
          <pre>${escapeHtml(section.output)}</pre>
        </article>`
          )
          .join("")}
      </section>
    </main>
  </body>
</html>`;
}

async function captureIndividualCards(browser, allSections) {
  for (const section of allSections) {
    const page = await browser.newPage({
      viewport: { width: 1500, height: 1000 },
      deviceScaleFactor: 1.5,
    });
    await page.setContent(buildCardPage(section), { waitUntil: "load" });
    await page.screenshot({
      path: path.join(screenshotsDir, `${section.slug}-output.png`),
      fullPage: true,
    });
    await page.close();
  }
}

async function captureDashboard(browser) {
  try {
    const page = await browser.newPage({
      viewport: { width: 1440, height: 1200 },
      deviceScaleFactor: 1.5,
    });
    await page.goto("http://127.0.0.1:8000/dashboard", { waitUntil: "networkidle", timeout: 5000 });
    await page.screenshot({
      path: path.join(screenshotsDir, "dashboard.png"),
      fullPage: true,
    });
    await page.close();
  } catch (error) {
    console.warn(`Skipping dashboard capture: ${error.message}`);
  }
}

async function main() {
  fs.mkdirSync(validationDir, { recursive: true });
  fs.mkdirSync(screenshotsDir, { recursive: true });

  const hydratedSections = sections.map((section) => ({
    ...section,
    output: readOutput(section.filename),
  }));

  const reportPath = path.join(validationDir, "report.html");
  fs.writeFileSync(reportPath, buildReportPage(hydratedSections));

  const browser = await chromium.launch();

  await captureIndividualCards(browser, hydratedSections);

  const reportPage = await browser.newPage({
    viewport: { width: 1600, height: 2400 },
    deviceScaleFactor: 1.5,
  });
  await reportPage.goto(`file://${reportPath}`);
  await reportPage.screenshot({
    path: path.join(screenshotsDir, "validation-report.png"),
    fullPage: true,
  });
  await reportPage.close();

  await captureDashboard(browser);
  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
