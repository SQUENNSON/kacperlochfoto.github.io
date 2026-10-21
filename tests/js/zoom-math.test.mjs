import { test } from "node:test";
import assert from "node:assert/strict";
import { fitSize, clampScale, zoomAt, clampPan, pinch, isSwipe } from "../../assets/js/zoom-math.js";

// punkt obrazu pod punktem ekranu (px, py): (p - vp/2 - przesunięcie) / s
const imagePoint = (st, px, py, vpW, vpH) => [(px - vpW / 2 - st.x) / st.s, (py - vpH / 2 - st.y) / st.s];

test("fitSize: contain", () => {
  assert.deepEqual(fitSize(3000, 2000, 1500, 800), { w: 1200, h: 800 });
  assert.deepEqual(fitSize(2000, 3000, 1000, 1000), { w: 1000 * 2 / 3, h: 1000 });
  assert.deepEqual(fitSize(4000, 1000, 1000, 1000), { w: 1000, h: 250 });
});

test("clampScale", () => {
  assert.equal(clampScale(0.5), 1);
  assert.equal(clampScale(9), 4);
  assert.equal(clampScale(2), 2);
  assert.equal(clampScale(3, 1, 2.5), 2.5);
});

test("zoomAt keeps point under cursor", () => {
  const before = { s: 1, x: 0, y: 0 };
  const st = zoomAt(before, 2, 300, 200, 1000, 800, 1000, 800);
  assert.equal(st.s, 2);
  const [u0, v0] = imagePoint(before, 300, 200, 1000, 800);
  const [u1, v1] = imagePoint(st, 300, 200, 1000, 800);
  assert.ok(Math.abs(u0 - u1) < 1e-9 && Math.abs(v0 - v1) < 1e-9);
  // dalszy zoom z już przesuniętego stanu też trzyma punkt
  const st2 = zoomAt(st, 1.5, 650, 420, 1000, 800, 1000, 800);
  const [u2, v2] = imagePoint(st, 650, 420, 1000, 800);
  const [u3, v3] = imagePoint(st2, 650, 420, 1000, 800);
  assert.ok(Math.abs(u2 - u3) < 1e-9 && Math.abs(v2 - v3) < 1e-9);
});

test("zoomAt clamps scale and returns to center at s=1", () => {
  const st = zoomAt({ s: 3, x: 200, y: 100 }, 10, 500, 400, 1000, 800, 1000, 800);
  assert.equal(st.s, 4);
  assert.deepEqual(zoomAt({ s: 2, x: 300, y: -100 }, 0.1, 100, 100, 1000, 800, 1000, 800), { s: 1, x: 0, y: 0 });
});

test("clampPan at s=1 centers", () => {
  assert.deepEqual(clampPan({ s: 1, x: 50, y: -20 }, 1000, 800, 1000, 800), { s: 1, x: 0, y: 0 });
});

test("clampPan limits edges at s=2", () => {
  const st = clampPan({ s: 2, x: 5000, y: 0 }, 1000, 800, 1000, 800);
  assert.equal(st.x, 500);
  assert.equal(clampPan({ s: 2, x: -5000, y: -5000 }, 1000, 800, 1000, 800).y, -400);
  // zdjęcie węższe od ekranu nawet po powiększeniu: w poziomie zostaje na środku
  assert.equal(clampPan({ s: 1.5, x: 300, y: 0 }, 1000, 800, 400, 800).x, 0);
});

test("pinch scales by distance ratio and clamps", () => {
  const st = pinch({ s: 1, x: 0, y: 0 }, 100, 250, 500, 400, 1000, 800, 1000, 800);
  assert.equal(st.s, 2.5);
  assert.equal(pinch({ s: 1, x: 0, y: 0 }, 100, 1000, 500, 400, 1000, 800, 1000, 800).s, 4);
  assert.equal(pinch({ s: 2, x: 0, y: 0 }, 200, 50, 500, 400, 1000, 800, 1000, 800).s, 1);
});

test("isSwipe ignores when zoomed", () => {
  assert.equal(isSwipe(-120, 10, 200, 1), 1);
  assert.equal(isSwipe(120, 10, 200, 1), -1);
  assert.equal(isSwipe(-120, 10, 200, 2), 0);
  assert.equal(isSwipe(30, 0, 200, 1), 0);
  assert.equal(isSwipe(-120, 100, 200, 1), 0);
  assert.equal(isSwipe(-120, 10, 700, 1), 0);
});
