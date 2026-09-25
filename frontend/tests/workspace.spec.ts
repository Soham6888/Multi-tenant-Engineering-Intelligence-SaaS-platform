import { expect, test, type Page } from "@playwright/test";

async function navigate(page: Page, name: string) {
  const toggle = page.getByRole("button", { name: "Open navigation" });
  if (await toggle.isVisible()) await toggle.click();
  await page
    .getByRole("navigation")
    .getByRole("button", { name, exact: true })
    .click();
}

test("clearly labels sample data and changes aggregate period", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Engineering overview" }),
  ).toBeVisible();
  await expect(page.locator(".demo-notice")).toContainText("Demo workspace");
  const before = await page.locator(".metric-value").first().innerText();
  await page.getByRole("button", { name: "7 days", exact: true }).click();
  await expect(page.locator(".metric-value").first()).not.toHaveText(before!);
  await expect(
    page.getByRole("button", { name: "7 days", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  expect(await page.evaluate(() => window.innerWidth)).toBe(
    page.viewportSize()!.width,
  );
});

test("repository filter and drill-down stay in sync", async ({ page }) => {
  await page.goto("/");
  await page
    .getByLabel("Repository", { exact: true })
    .selectOption("payments-api");
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await page
    .getByRole("button", { name: "View payments-api", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Repositories", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Deployment history" }),
  ).toBeVisible();
});

test("PR state filters records and empty state is useful", async ({ page }) => {
  await page.goto("/");
  await navigate(page, "Pull Requests");
  await page.getByLabel("PR state").selectOption("Awaiting review");
  await expect(page.locator("tbody tr")).toHaveCount(2);
  await page
    .getByLabel("Repository", { exact: true })
    .selectOption("auth-service");
  await expect(
    page.getByText("No pull requests match your filters."),
  ).toBeVisible();
});

test("integration dialog is honest and keyboard dismissible", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .getByRole("button", { name: "Connect GitHub", exact: true })
    .click();
  await page.getByRole("button", { name: "Set up GitHub" }).click();
  await expect(page.getByRole("dialog")).toContainText(
    "No credentials are collected",
  );
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
});

test("export produces a sample CSV", async ({ page }) => {
  await page.goto("/");
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export", exact: true }).click();
  expect((await download).suggestedFilename()).toBe("demo-engineering-30d.csv");
  await expect(page.getByRole("status")).toContainText(
    "Sample-data report exported",
  );
});

test("review focus drills into the selected sample repository", async ({
  page,
}) => {
  await page.goto("/");
  const focus = page.getByRole("region", {
    name: "Keep good work moving forward.",
  });
  await expect(focus).toContainText("Sample data. GitHub is not connected.");
  await page
    .getByLabel("Repository", { exact: true })
    .selectOption("payments-api");
  await expect(page.locator(".focus-row")).toHaveCount(1);
  await page.locator(".focus-row").click();
  await expect(
    page.getByRole("heading", { name: "Pull Requests", exact: true }),
  ).toBeVisible();
  await expect(page.getByLabel("PR state")).toHaveValue("Awaiting review");
  await expect(page.locator("tbody tr")).toHaveCount(1);
  await expect(page.locator("tbody")).toContainText("Add idempotency keys");
});
