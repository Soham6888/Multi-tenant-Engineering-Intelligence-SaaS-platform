import { expect, test } from "@playwright/test";

// These calls hit the actual Next.js route; browser route mocks cannot hide
// a missing collection handler. The API may be deliberately offline in UI CI.
test("organization collection is routed through the real server proxy", async ({
  request,
}) => {
  for (const method of ["GET", "POST"]) {
    const response = await request.fetch("/api/v1/organizations?limit=1", {
      method,
      ...(method === "POST" ? { data: { name: "Unauthorized" } } : {}),
    });
    expect([401, 403, 503]).toContain(response.status());
    expect(response.headers()["cache-control"]).toBe("no-store");
    expect((await response.json()).error.request_id).toMatch(/^req_/);
  }
});

test("proxy rejects routes outside its allowlist", async ({ request }) => {
  const response = await request.get("/api/v1/organizations/unexpected/admin");
  expect(response.status()).toBe(404);
  expect((await response.json()).error.code).toBe("RESOURCE_NOT_FOUND");
});
