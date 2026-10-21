// Smoke pod podścieżką GitHub Pages. Wymaga serwera `py -m http.server 8081` uruchomionego w B:\GITHUB
// (strona pod http://localhost:8081/kacperlochfoto.github.io/). Uruchom: node tools/e2e/smoke.mjs → „SMOKE OK”.
// http.server nie podaje 404.html dla brakujących ścieżek, więc stronę 404 otwieramy bezpośrednio.
import { chromium } from "playwright-core";
import assert from "node:assert/strict";

const ROOT = process.env.BASE_URL || "http://localhost:8081/kacperlochfoto.github.io/";
const PAGES = ["", "sport/", "reportaz/", "o-mnie/", "kontakt/", "404.html"];
const WIDTHS = [1440, 900, 390, 320];
const status = new Map(); // url -> kod (linki z .nav i .topbar)

const browser = await chromium.launch({ channel: "chrome" });
try {
  for (const width of WIDTHS) {
    const ctx = await browser.newContext({ viewport: { width, height: 900 } });
    for (const path of PAGES) {
      const page = await ctx.newPage();
      const label = `${path || "/"} @${width}`;
      const problems = [];
      page.on("response", (r) => { if (r.status() >= 400) problems.push(`${r.status()} ${r.url()}`); });
      page.on("console", (m) => { if (m.type() === "error") problems.push(`console: ${m.text()}`); });
      page.on("pageerror", (e) => problems.push(`pageerror: ${e.message}`));

      const res = await page.goto(ROOT + path, { waitUntil: "load" });
      assert.equal(res.status(), 200, label);
      await page.waitForTimeout(150);
      assert.deepEqual(problems, [], label);

      const [sw, iw] = await page.evaluate(() => [document.documentElement.scrollWidth, innerWidth]);
      assert.ok(sw <= iw, `${label}: poziomy scroll ${sw} > ${iw}`);

      const links = await page.$$eval(".nav a[href], .topbar a[href]", (as) => as.map((a) => a.href));
      for (const url of links) {
        if (!status.has(url)) status.set(url, (await page.request.get(url)).status());
        assert.equal(status.get(url), 200, `${label}: ${url}`);
        assert.ok(url.startsWith(ROOT), `${label}: link poza podścieżką ${url}`);
      }

      if (path === "404.html") {
        const home = await page.$eval(".notfound a.big-link", (a) => a.href);
        assert.equal(new URL(home).pathname, "/kacperlochfoto.github.io/", label);
      }

      if (width <= 390) {
        await page.click(".menu-btn");
        assert.equal(await page.getAttribute(".menu-btn", "aria-expanded"), "true", label);
        await page.locator("#nav a", { hasText: "Reportaż" }).click();
        await page.waitForURL(ROOT + "reportaz/");
        assert.deepEqual(problems, [], `${label} → reportaz/`);
      }
      await page.close();
    }
    await ctx.close();
  }
} finally {
  await browser.close();
}
console.log("SMOKE OK");
