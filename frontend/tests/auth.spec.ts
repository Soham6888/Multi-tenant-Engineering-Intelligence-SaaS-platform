import { expect, test } from "@playwright/test";

const identity = {
  user: {
    id: "test-user",
    name: "Alex Morgan",
    email: "alex@example.com",
    created_at: "2026-09-23T10:00:00Z",
  },
  csrf_token: "test-csrf",
};

test("login submits credentials and shows account identity", async ({
  page,
}) => {
  await page.route("**/api/v1/auth/login", async (route) => {
    expect(route.request().postDataJSON()).toEqual({
      email: "alex@example.com",
      password: "a long test passphrase",
    });
    expect(route.request().headers()["x-eip-request"]).toBe("1");
    await route.fulfill({ json: identity });
  });
  await page.route("**/api/v1/auth/me", (route) =>
    route.fulfill({ json: identity }),
  );
  await page.route("**/api/v1/organizations", (route) =>
    route.fulfill({
      json: { data: [], pagination: { has_more: false, next_cursor: null } },
    }),
  );
  await page.goto("/login");
  await page.getByLabel("Email address").fill("alex@example.com");
  await page
    .getByLabel("Password", { exact: true })
    .fill("a long test passphrase");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Good to have you here, Alex Morgan." }),
  ).toBeVisible();
  await expect(
    page.getByText("The analytics preview contains sample data.", {
      exact: false,
    }),
  ).toBeVisible();
});

test("registration supports password visibility and responsive form", async ({
  page,
}) => {
  await page.goto("/register");
  await page.getByLabel("Full name").fill("Alex Morgan");
  await page.getByLabel("Email address").fill("alex@example.com");
  const password = page.getByLabel("Password", { exact: true });
  await password.fill("a long test passphrase");
  await page.getByRole("button", { name: "Show password" }).click();
  await expect(password).toHaveAttribute("type", "text");
  await page.getByRole("button", { name: "Hide password" }).click();
  await expect(password).toHaveAttribute("type", "password");
  expect(await page.evaluate(() => innerWidth)).toBe(
    page.viewportSize()!.width,
  );
  await page.route("**/api/v1/auth/register", (route) =>
    route.fulfill({
      status: 409,
      json: {
        error: {
          message: "Unable to register with these details",
          request_id: "req_test",
        },
      },
    }),
  );
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  await expect(page.getByRole("form").getByRole("alert")).toContainText(
    "Unable to register with these details",
  );
  await expect(
    page.getByRole("button", { name: "Create account", exact: true }),
  ).toBeEnabled();
});

test("unavailable authentication displays a recoverable error", async ({
  page,
}) => {
  await page.route("**/api/v1/auth/login", (route) =>
    route.fulfill({
      status: 503,
      json: { error: { message: "Sign-in is temporarily unavailable" } },
    }),
  );
  await page.goto("/login");
  await page.getByLabel("Email address").fill("alex@example.com");
  await page.getByLabel("Password", { exact: true }).fill("wrong password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("form").getByRole("alert")).toContainText(
    "temporarily unavailable",
  );
  await expect(
    page.getByRole("button", { name: "Sign in", exact: true }),
  ).toBeEnabled();
});

test("unauthenticated account redirects and logout uses session CSRF", async ({
  page,
}) => {
  let signedIn = false;
  await page.route("**/api/v1/auth/me", (route) =>
    route.fulfill(
      signedIn
        ? { json: identity }
        : { status: 401, json: { error: { message: "Please sign in" } } },
    ),
  );
  await page.route("**/api/v1/organizations", (route) =>
    route.fulfill({
      json: { data: [], pagination: { has_more: false, next_cursor: null } },
    }),
  );
  await page.goto("/account");
  await expect(page).toHaveURL(/\/login$/);
  signedIn = true;
  await page.goto("/account");
  await page.route("**/api/v1/auth/logout", async (route) => {
    expect(route.request().headers()["x-csrf-token"]).toBe("test-csrf");
    signedIn = false;
    await route.fulfill({ status: 204 });
  });
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
});

test("account creates an isolated organization workspace", async ({ page }) => {
  await page.route("**/api/v1/auth/me", (route) =>
    route.fulfill({ json: identity }),
  );
  let organizations: object[] = [];
  await page.route("**/api/v1/organizations", async (route) => {
    if (route.request().method() === "POST") {
      expect(route.request().postDataJSON()).toEqual({
        name: "Northstar Engineering",
      });
      organizations = [
        {
          id: "organization-1",
          name: "Northstar Engineering",
          slug: "northstar-engineering",
          role: "OWNER",
          created_at: "2026-09-24T10:00:00Z",
        },
      ];
    }
    await route.fulfill({
      json: {
        data: organizations,
        pagination: { has_more: false, next_cursor: null },
      },
    });
  });
  await page.goto("/account");
  await expect(
    page.getByRole("heading", {
      name: "Your engineering data starts with a workspace.",
    }),
  ).toBeVisible();
  await page.getByLabel("Create a workspace").fill("Northstar Engineering");
  await page.getByRole("button", { name: "Create workspace" }).click();
  await expect(
    page.getByRole("heading", { name: "Northstar Engineering" }),
  ).toBeVisible();
  await expect(page.getByText("OWNER", { exact: true })).toBeVisible();
  await expect(
    page.getByText("The analytics preview contains sample data.", {
      exact: false,
    }),
  ).toBeVisible();
  await page.route("**/api/v1/organizations/*/invitations", async (route) => {
    expect(route.request().postDataJSON()).toEqual({
      email: "teammate@example.com",
      role: "DEVELOPER",
    });
    await route.fulfill({
      json: {
        token: "one-time-invitation-token",
        email: "teammate@example.com",
        expires_at: "2026-10-01T10:00:00Z",
      },
    });
  });
  await page.getByText("Invite a teammate").click();
  await page.getByLabel("Work email").fill("teammate@example.com");
  await page.getByRole("button", { name: "Create invitation" }).click();
  await expect(page.getByText("one-time-invitation-token")).toBeVisible();
  await expect(
    page.getByText("Share this one-time invitation token privately:"),
  ).toBeVisible();
});

test("matching account can accept a private workspace invitation", async ({
  page,
}) => {
  const token = `invite-${"0".repeat(36)}`;
  await page.route("**/api/v1/auth/me", (route) =>
    route.fulfill({ json: identity }),
  );
  await page.route("**/api/v1/organizations", (route) =>
    route.fulfill({
      json: { data: [], pagination: { has_more: false, next_cursor: null } },
    }),
  );
  await page.route(
    "**/api/v1/organizations/invitations/accept",
    async (route) => {
      expect(route.request().postDataJSON()).toEqual({
        token,
      });
      await route.fulfill({
        json: {
          id: "joined-org",
          name: "Northstar Platform",
          slug: "northstar-platform",
          role: "DEVELOPER",
          created_at: "2026-09-24T10:00:00Z",
        },
      });
    },
  );
  await page.goto("/account");
  await page.getByLabel("Joining a workspace?").fill(token);
  await page.getByRole("button", { name: "Accept invitation" }).click();
  await expect(
    page.getByRole("heading", { name: "Northstar Platform" }),
  ).toBeVisible();
  await expect(page.getByText("You joined Northstar Platform.")).toBeVisible();
});

test("real registration and logout through the API proxy", async ({ page }) => {
  test.skip(
    process.env.EIP_E2E_REAL_AUTH !== "1",
    "Requires running API, migrated PostgreSQL and Redis",
  );
  const email = `browser-${crypto.randomUUID()}@example.com`;
  await page.goto("/register");
  await page.getByLabel("Full name").fill("Browser Test");
  await page.getByLabel("Email address").fill(email);
  await page
    .getByLabel("Password", { exact: true })
    .fill("a long browser test passphrase");
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Good to have you here, Browser Test." }),
  ).toBeVisible();
  await page
    .getByLabel("Create a workspace")
    .fill(`Browser Workspace ${crypto.randomUUID()}`);
  await page
    .getByRole("button", { name: "Create workspace", exact: true })
    .click();
  await expect(page.getByText("OWNER", { exact: true })).toBeVisible();
  await expect(page.locator(".workspace-card h3")).toContainText(
    "Browser Workspace",
  );
  await page
    .getByLabel("Create a workspace")
    .fill(`Second Browser Workspace ${crypto.randomUUID()}`);
  await page
    .getByRole("button", { name: "Create workspace", exact: true })
    .click();
  await expect(page.locator(".workspace-card")).toHaveCount(2);
  const collection = await page.request.get("/api/v1/organizations?limit=1");
  expect(collection.status()).toBe(200);
  const firstPage = await collection.json();
  expect(firstPage.data).toHaveLength(1);
  expect(firstPage.pagination.has_more).toBe(true);
  const nextPage = await page.request.get(
    `/api/v1/organizations?limit=1&cursor=${encodeURIComponent(firstPage.pagination.next_cursor)}`,
  );
  expect(nextPage.status()).toBe(200);
  const nextData = await nextPage.json();
  expect(nextData.data).toHaveLength(1);
  expect(nextData.data[0].id).not.toBe(firstPage.data[0].id);
  expect(nextData.pagination.has_more).toBe(false);
  const cookies = await page.context().cookies();
  expect(cookies.find((c) => c.name === "eip_session")?.httpOnly).toBe(true);
  await page.reload();
  await expect(page.getByText(email, { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  await page.goto("/account");
  await expect(page).toHaveURL(/\/login$/);
});
