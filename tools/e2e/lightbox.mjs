// E2E lightboxa. Wymaga serwera `py -m http.server 8080` w korzeniu repo.
// Uruchom: node tools/e2e/lightbox.mjs  → wypisuje „LIGHTBOX OK”.
import { chromium } from "playwright-core";
import assert from "node:assert/strict";

const BASE = process.env.BASE_URL || "http://localhost:8080/";
const errors = [];

const scaleOf = (page) =>
  page.$eval("dialog.lb .lb-img.cur", (im) => {
    const m = /scale\(([\d.]+)\)/.exec(im.style.transform);
    return m ? +m[1] : 1;
  });
const count = (page) => page.$eval("dialog.lb .lb-count", (el) => el.textContent.trim());
const isOpen = (page) => page.evaluate(() => !!document.querySelector("dialog.lb[open]"));

function watch(page, label) {
  page.on("pageerror", (e) => errors.push(`${label}: ${e.message}`));
  page.on("console", (m) => { if (m.type() === "error") errors.push(`${label}: ${m.text()}`); });
}

const browser = await chromium.launch({ channel: "chrome" });
try {
  // ---- desktop 1440×900, sport/ ----
  {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();
    watch(page, "desktop");
    await page.goto(BASE + "sport/", { waitUntil: "load" });
    const href = page.url();
    await page.locator("a[data-lb]").nth(2).click();
    await page.waitForSelector("dialog.lb[open] .lb-img.cur");
    assert.equal(await count(page), "3 / 88");

    await page.keyboard.press("ArrowRight");
    assert.equal(await count(page), "4 / 88");

    const largest = await page.locator("a[data-lb]").nth(3).evaluate((a) =>
      a.dataset.srcset.split(",").pop().trim().split(" ")[0].split("/").pop());
    await page.mouse.move(720, 450);
    await page.mouse.wheel(0, -500);
    await page.waitForTimeout(100);
    const s = await scaleOf(page);
    assert.ok(s > 1, `scale po kółku = ${s}`);
    await page.waitForFunction(
      (file) => decodeURI(document.querySelector("dialog.lb .lb-img.cur").currentSrc).endsWith("/" + file),
      largest, { timeout: 15000 });

    await page.keyboard.press("Escape");
    await page.waitForFunction(() => !document.querySelector("dialog.lb[open]"));
    await page.waitForTimeout(150);
    assert.equal(page.url(), href);
    await ctx.close();
  }

  // ---- telefon 390×844 (dotyk), reportaz/ ----
  {
    const ctx = await browser.newContext({
      viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, hasTouch: true, isMobile: true,
    });
    const page = await ctx.newPage();
    watch(page, "mobile");
    await page.goto(BASE + "reportaz/", { waitUntil: "load" });
    const href = page.url();

    await page.locator("a[data-lb]").nth(1).tap();
    await page.waitForSelector("dialog.lb[open] .lb-img.cur");
    await page.goBack({ waitUntil: "commit" }).catch(() => {});
    await page.waitForFunction(() => !document.querySelector("dialog.lb[open]"));
    await page.waitForTimeout(150);
    assert.equal(page.url(), href);
    assert.ok(href.endsWith("/reportaz/"));

    await page.locator("a[data-lb]").nth(1).tap();
    await page.waitForSelector("dialog.lb[open] .lb-img.cur");
    await page.waitForTimeout(400);
    const before = await count(page);
    const cdp = await ctx.newCDPSession(page);
    const cx = 195, cy = 422;
    const pts = (d) => [{ x: cx - d, y: cy, id: 0 }, { x: cx + d, y: cy, id: 1 }];
    await cdp.send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: pts(30) });
    for (let d = 40; d <= 120; d += 10) {
      await cdp.send("Input.dispatchTouchEvent", { type: "touchMove", touchPoints: pts(d) });
    }
    await cdp.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
    await page.waitForTimeout(400);
    assert.equal(await count(page), before, "pinch nie może przełączyć zdjęcia");
    const s = await scaleOf(page);
    assert.ok(s > 1, `scale po pinchu = ${s}`);
    assert.ok(await isOpen(page));
    await ctx.close();
  }
  assert.deepEqual(errors, []);
} finally {
  await browser.close();
}
console.log("LIGHTBOX OK");
