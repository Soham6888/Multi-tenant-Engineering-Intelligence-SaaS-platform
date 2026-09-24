import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const output = new URL("../../docs/design/", import.meta.url);
await mkdir(output, { recursive: true });
const browser = await chromium.launch();
try {
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1100 },
    deviceScaleFactor: 1,
  });
  await page.goto("http://127.0.0.1:3000", { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({
    path: fileURLToPath(new URL("overview-desktop.png", output)),
    fullPage: true,
  });
  const mobile = await browser.newPage({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 1,
    reducedMotion: "reduce",
  });
  await mobile.goto("http://127.0.0.1:3000", { waitUntil: "networkidle" });
  await mobile.evaluate(() => document.fonts.ready);
  await mobile.screenshot({
    path: fileURLToPath(new URL("overview-mobile.png", output)),
    fullPage: true,
  });
  await page.goto("http://127.0.0.1:3000/login", { waitUntil: "networkidle" });
  await page.screenshot({
    path: fileURLToPath(new URL("login-desktop.png", output)),
    fullPage: true,
  });
  await mobile.goto("http://127.0.0.1:3000/register", {
    waitUntil: "networkidle",
  });
  await mobile.screenshot({
    path: fileURLToPath(new URL("register-mobile.png", output)),
    fullPage: true,
  });
  console.log("Saved dashboard and authentication screenshots to docs/design.");
} finally {
  await browser.close();
}
