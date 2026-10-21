// Czysta matematyka zoomu lightboxa. Stan {s, x, y}: skala i przesunięcie (px) środka zdjęcia
// względem środka obszaru vpW × vpH; zdjęcie w skali 1 ma rozmiar fitW × fitH i stoi na środku.

export function fitSize(imgW, imgH, vpW, vpH) {
  const k = Math.min(vpW / imgW, vpH / imgH);
  return { w: imgW * k, h: imgH * k };
}

export function clampScale(s, min = 1, max = 4) {
  return Math.min(max, Math.max(min, s));
}

// Krawędź zdjęcia nie odjeżdża do środka ekranu; mniejsze od ekranu zostaje na środku.
export function clampPan(state, vpW, vpH, fitW, fitH) {
  const s = state.s;
  if (s <= 1) return { s, x: 0, y: 0 };
  const mx = Math.max(0, (fitW * s - vpW) / 2);
  const my = Math.max(0, (fitH * s - vpH) / 2);
  const x = Math.min(mx, Math.max(-mx, state.x));
  const y = Math.min(my, Math.max(-my, state.y));
  return { s, x: x || 0, y: y || 0 };
}

// Punkt obrazu pod (px, py) zostaje w miejscu (o ile nie trzeba dociągnąć krawędzi).
export function zoomAt(state, factor, px, py, vpW, vpH, fitW, fitH) {
  const s = clampScale(state.s * factor);
  const k = s / state.s;
  const cx = px - vpW / 2;
  const cy = py - vpH / 2;
  return clampPan({ s, x: cx - (cx - state.x) * k, y: cy - (cy - state.y) * k }, vpW, vpH, fitW, fitH);
}

// state = stan z początku gestu, d0/d1 = odległość palców na początku i teraz, (cx, cy) = środek gestu.
export function pinch(state, d0, d1, cx, cy, vpW, vpH, fitW, fitH) {
  return zoomAt(state, d1 / d0, cx, cy, vpW, vpH, fitW, fitH);
}

// 1 = następne (palec w lewo), -1 = poprzednie; tylko bez przybliżenia.
export function isSwipe(dx, dy, dt, s) {
  if (s !== 1 || Math.abs(dx) <= 60 || Math.abs(dx) <= 1.5 * Math.abs(dy) || dt >= 600) return 0;
  return dx < 0 ? 1 : -1;
}
