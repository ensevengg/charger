// Runs the Speedy Shopper prompt through OpenClaw's web chat UI and records the screen,
// so the video shows the speed patch's readout (it is only in the web UI).
// Usage (in a container sharing the gateway's network, so the UI is on localhost):
//   node ui-run.mjs <session-id> <out-dir>        token comes from $OPENCLAW_GATEWAY_TOKEN
import { createRequire } from "node:module";
import fs from "node:fs";
const require = createRequire("/app/node_modules/");
const { chromium } = require("playwright-core");

const [sid, outDir] = process.argv.slice(2);
const PROMPT = "Santa's Speedy Shopper: find 5 Christmas gifts that are real products currently sold on real retail websites, with direct product links.";
const size = { width: 1920, height: 1080 };
const url = `http://127.0.0.1:18789/chat/main/explicit/${sid}#token=${process.env.OPENCLAW_GATEWAY_TOKEN}`;

const browser = await chromium.launch({ headless: true, args: ["--no-sandbox"] });
const ctx = await browser.newContext({ viewport: size, recordVideo: { dir: outDir, size }, colorScheme: "dark" });
const page = await ctx.newPage();
fs.writeFileSync(`${outDir}/start.txt`, String(Date.now() / 1000));
await page.goto(url);
const box = page.locator("textarea").first();
await box.waitFor({ timeout: 60000 });
await page.waitForTimeout(1500);
await box.fill(PROMPT);
await box.press("Enter");
fs.writeFileSync(`${outDir}/sent.txt`, String(Date.now() / 1000));
console.log("sent");

// Done when the final table has appeared and no run is in progress for a few seconds.
const deadline = Date.now() + 28 * 60 * 1000;
let idleSince = 0;
await page.waitForTimeout(5000);
while (Date.now() < deadline) {
  const working = await page.locator(".chat-working-indicator").count();
  const table = (await page.getByText("| Name |").count()) + (await page.locator("table th", { hasText: "Retailer" }).count());
  if (!working) {
    idleSince ||= Date.now();
    if (Date.now() - idleSince > (table ? 2500 : 20000)) break;
  } else idleSince = 0;
  await page.waitForTimeout(500);
}
// Hold on the finished answer (products + links) with the speed readouts visible.
await page.evaluate(() => {
  for (const el of document.querySelectorAll("*")) if (el.scrollHeight > el.clientHeight + 50) el.scrollTop = el.scrollHeight;
});
await page.waitForTimeout(5000);
const speeds = await page.locator(".chat-gen-speed").allInnerTexts();
fs.writeFileSync(`${outDir}/readout.json`, JSON.stringify({ end: Date.now() / 1000, speeds }, null, 1));
console.log("readout", JSON.stringify(speeds));
await page.screenshot({ path: `${outDir}/final.png` });
const video = page.video();
await ctx.close();
await video.saveAs(`${outDir}/full.webm`);
await video.delete();
await browser.close();
