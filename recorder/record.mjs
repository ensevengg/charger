// Records the live TPS dashboard in headless Chromium until SIGTERM.
// Usage (inside the OpenClaw image): node record.mjs <dashboard-url> <out-dir>
import { createRequire } from "node:module";
import fs from "node:fs";
const require = createRequire("/app/node_modules/");
const { chromium } = require("playwright-core");

const [url, outDir] = process.argv.slice(2);
const size = { width: 1920, height: 1080 };
const browser = await chromium.launch({
  headless: true, args: ["--no-sandbox"],
  handleSIGTERM: false, handleSIGINT: false, handleSIGHUP: false,   // we save the video first
});
const ctx = await browser.newContext({ viewport: size, recordVideo: { dir: outDir, size } });
const page = await ctx.newPage();
const t0 = Date.now() / 1000;
await page.goto(url);
fs.writeFileSync(`${outDir}/start.txt`, String(t0));
console.log("recording", url);

let stopping = false;
async function stop() {
  if (stopping) return;
  stopping = true;
  await page.waitForTimeout(4000);           // hold the final frame a moment
  const video = page.video();
  await ctx.close();
  await video.saveAs(`${outDir}/full.webm`);
  await video.delete();
  await browser.close();
  console.log("saved");
  process.exit(0);
}
process.on("SIGTERM", stop);
process.on("SIGINT", stop);
setInterval(() => {}, 1 << 30);
