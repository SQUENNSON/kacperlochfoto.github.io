// Lightbox: <dialog class="lb"> na pełny ekran, nawigacja (klawisze, przyciski, swipe), historia
// (przycisk „wstecz” zamyka) i zoom (kółko, przeciąganie, pinch, dwuklik). Ładowany leniwie z main.js.
import { fitSize, clampPan, zoomAt, pinch, isSwipe } from "./zoom-math.js";

const reduced = matchMedia("(prefers-reduced-motion: reduce)");
const FADE = 350;

let dlg, stage, counter, img;
let items = [];
let index = 0;
let state = { s: 1, x: 0, y: 0 };
let fit = { w: 0, h: 0 };
let vp = { w: 0, h: 0 };
let sized = false; // img.sizes podbite po pierwszym przybliżeniu
let pendingBack = false;

const pointers = new Map();
let gesture = null; // {x, y, t, start, moved, pinch, d0, cx, cy, onImg}
let lastTap = null;

function build() {
  dlg = document.createElement("dialog");
  dlg.className = "lb";
  dlg.setAttribute("aria-label", "Podgląd zdjęcia");
  dlg.innerHTML =
    '<div class="lb-stage"></div>' +
    '<p class="lb-count" aria-live="polite"></p>' +
    '<button class="lb-btn lb-prev" type="button" aria-label="Poprzednie">←</button>' +
    '<button class="lb-btn lb-next" type="button" aria-label="Następne">→</button>' +
    '<button class="lb-btn lb-close" type="button" aria-label="Zamknij">✕</button>';
  document.body.append(dlg);
  stage = dlg.querySelector(".lb-stage");
  counter = dlg.querySelector(".lb-count");
  dlg.querySelector(".lb-prev").addEventListener("click", () => go(-1));
  dlg.querySelector(".lb-next").addEventListener("click", () => go(1));
  dlg.querySelector(".lb-close").addEventListener("click", () => dlg.close());
  dlg.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") { e.preventDefault(); go(-1); }
    else if (e.key === "ArrowRight") { e.preventDefault(); go(1); }
  });
  dlg.addEventListener("close", onClose);
  dlg.addEventListener("wheel", onWheel, { passive: false });
  stage.addEventListener("pointerdown", onDown);
  stage.addEventListener("pointermove", onMove);
  stage.addEventListener("pointerup", onUp);
  stage.addEventListener("pointercancel", onUp);
  addEventListener("resize", () => { if (dlg.open) layout(); });
  addEventListener("popstate", () => {
    if (pendingBack) { pendingBack = false; return; }
    if (dlg.open) dlg.close();
  });
}

function data(i) {
  const a = items[i];
  return { srcset: a.dataset.srcset, w: +a.dataset.w, h: +a.dataset.h, c: a.style.getPropertyValue("--c"), alt: a.querySelector("img")?.alt || "" };
}

function layout() {
  vp = { w: stage.clientWidth, h: stage.clientHeight };
  const d = data(index);
  const padX = vp.w > 900 ? 72 : 0;
  const padY = vp.w > 900 ? 56 : 52;
  fit = fitSize(d.w, d.h, vp.w - 2 * padX, vp.h - 2 * padY);
  Object.assign(img.style, {
    width: `${fit.w}px`,
    height: `${fit.h}px`,
    left: `${(vp.w - fit.w) / 2}px`,
    top: `${(vp.h - fit.h) / 2}px`,
  });
  apply(clampPan(state, vp.w, vp.h, fit.w, fit.h));
}

function apply(next) {
  state = next;
  img.style.transform = `translate(${state.x}px, ${state.y}px) scale(${state.s})`;
  if (state.s > 1 && !sized) {
    sized = true;
    img.sizes = `${Math.ceil(vp.w * state.s)}px`;
  }
}

function prefetch(i) {
  const d = data((i + items.length) % items.length);
  const im = new Image();
  im.sizes = "100vw";
  im.srcset = d.srcset;
}

function show(i) {
  index = (i + items.length) % items.length;
  const d = data(index);
  const old = img;
  img = document.createElement("img");
  img.className = "lb-img";
  img.alt = d.alt;
  img.decoding = "async";
  img.draggable = false;
  img.style.background = d.c;
  img.addEventListener("load", () => { img.style.background = ""; }, { once: true });
  img.sizes = "100vw";
  img.srcset = d.srcset;
  state = { s: 1, x: 0, y: 0 };
  sized = false;
  stage.append(img);
  layout();
  counter.textContent = `${index + 1} / ${items.length}`;
  if (old) {
    old.classList.remove("cur");
    if (reduced.matches) old.remove();
    else setTimeout(() => old.remove(), FADE);
  }
  if (old && !reduced.matches) requestAnimationFrame(() => requestAnimationFrame(() => img.classList.add("cur")));
  else img.classList.add("cur");
  prefetch(index + 1);
  prefetch(index - 1);
}

function go(step) {
  if (items.length > 1) show(index + step);
}

function onClose() {
  stage.replaceChildren();
  img = null;
  state = { s: 1, x: 0, y: 0 };
  pointers.clear();
  gesture = null;
  if (history.state && history.state.lb) {
    pendingBack = true;
    history.back();
  }
  const a = items[index];
  if (a) {
    a.focus({ preventScroll: true });
    a.scrollIntoView({ block: "nearest" });
  }
}

function setGesture(on) {
  if (img) img.style.willChange = on ? "transform" : "";
}

let wheelEnd;
function onWheel(e) {
  e.preventDefault();
  if (!img) return;
  setGesture(true);
  clearTimeout(wheelEnd);
  wheelEnd = setTimeout(() => setGesture(false), 200);
  apply(zoomAt(state, Math.exp(-e.deltaY * 0.0015), e.clientX, e.clientY, vp.w, vp.h, fit.w, fit.h));
}

function dist() {
  const [a, b] = [...pointers.values()];
  return Math.hypot(a.x - b.x, a.y - b.y);
}

function onDown(e) {
  if (!img) return;
  stage.setPointerCapture(e.pointerId);
  pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
  setGesture(true);
  if (pointers.size === 1) {
    gesture = { x: e.clientX, y: e.clientY, t: e.timeStamp, start: state, moved: false, pinch: false, onImg: e.target === img };
  } else if (pointers.size === 2 && gesture) {
    const [a, b] = [...pointers.values()];
    Object.assign(gesture, { pinch: true, moved: true, start: state, d0: dist() || 1, cx: (a.x + b.x) / 2, cy: (a.y + b.y) / 2 });
  }
}

function onMove(e) {
  if (!gesture || !pointers.has(e.pointerId)) return;
  pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
  if (gesture.pinch) {
    if (pointers.size === 2) apply(pinch(gesture.start, gesture.d0, dist(), gesture.cx, gesture.cy, vp.w, vp.h, fit.w, fit.h));
    return;
  }
  const dx = e.clientX - gesture.x;
  const dy = e.clientY - gesture.y;
  if (Math.hypot(dx, dy) > 8) gesture.moved = true;
  if (gesture.start.s > 1) apply(clampPan({ s: state.s, x: gesture.start.x + dx, y: gesture.start.y + dy }, vp.w, vp.h, fit.w, fit.h));
}

function onUp(e) {
  if (!pointers.delete(e.pointerId) || !gesture) return;
  const g = gesture;
  if (pointers.size > 0) {
    // po pinchu jeden palec zostaje: dalej przesuwa od bieżącego stanu
    const [p] = [...pointers.values()];
    gesture = { x: p.x, y: p.y, t: e.timeStamp, start: state, moved: true, pinch: false, onImg: false, afterPinch: true };
    return;
  }
  gesture = null;
  setGesture(false);
  if (e.type === "pointercancel" || g.pinch || g.afterPinch) return;
  const dx = e.clientX - g.x;
  const dy = e.clientY - g.y;
  const dir = isSwipe(dx, dy, e.timeStamp - g.t, g.start.s);
  if (dir) { go(dir); return; }
  if (g.moved) return;
  if (!g.onImg) { if (state.s === 1) dlg.close(); return; }
  // dwuklik / double-tap: 1 ↔ 2.5 w miejscu stuknięcia
  if (lastTap && e.timeStamp - lastTap.t < 320 && Math.hypot(e.clientX - lastTap.x, e.clientY - lastTap.y) < 30) {
    lastTap = null;
    const target = state.s > 1 ? 1 : 2.5;
    img.classList.add("anim");
    apply(zoomAt(state, target / state.s, e.clientX, e.clientY, vp.w, vp.h, fit.w, fit.h));
    setTimeout(() => img && img.classList.remove("anim"), FADE);
  } else {
    lastTap = { t: e.timeStamp, x: e.clientX, y: e.clientY };
  }
}

export function open(i, list) {
  if (!dlg) build();
  items = list;
  if (!dlg.open) {
    dlg.showModal();
    history.pushState({ lb: 1 }, "");
  }
  show(Math.max(0, i));
  dlg.querySelector(".lb-close").focus({ preventScroll: true });
}
