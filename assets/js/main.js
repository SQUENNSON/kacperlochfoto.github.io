const root = document.documentElement;
root.classList.add("js");

// Reveal (CSS: html.js [data-reveal]): wiersze i bloki tekstu wchodzące w jednej partii
// pojawiają się po kolei co 0.08 s (najwyżej 0.32 s). Zaraz po klasie js, żeby błąd
// w dalszym kodzie nie zostawił ukrytej treści.
const revealed = document.querySelectorAll("[data-reveal]");
if ("IntersectionObserver" in window) {
  const io = new IntersectionObserver((entries) => {
    let i = 0;
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      entry.target.style.setProperty("--d", `${Math.min(i++ * 0.08, 0.32).toFixed(2)}s`);
      entry.target.classList.add("in");
      io.unobserve(entry.target);
    }
  }, { rootMargin: "0px 0px -8% 0px" });
  revealed.forEach((el) => io.observe(el));
} else {
  revealed.forEach((el) => el.classList.add("in"));
}

// Menu mobilne (≤ 900 px): przycisk w .topbar pokazuje nakładkę z #nav.
const btn = document.querySelector(".menu-btn");
const main = document.getElementById("main");

function setMenu(open) {
  if (!btn) return;
  btn.setAttribute("aria-expanded", String(open));
  root.classList.toggle("menu-open", open);
  if (main) main.inert = open;
}

if (btn) {
  btn.addEventListener("click", () => setMenu(btn.getAttribute("aria-expanded") !== "true"));
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && root.classList.contains("menu-open")) {
      setMenu(false);
      btn.focus();
    }
  });
  // Po przejściu na szeroki ekran nakładki nie ma — zamknij, żeby nie została blokada.
  matchMedia("(max-width: 900px)").addEventListener("change", (e) => {
    if (!e.matches) setMenu(false);
  });
  // Powrót z bfcache (przycisk „wstecz”) nie może przywrócić otwartego menu.
  addEventListener("pageshow", (e) => {
    if (e.persisted) setMenu(false);
  });
}

// Pasek postępu (CSS: .progress): miękko dogania przewijanie (wykładniczo, τ = 0.12 s); pętla rAF
// działa tylko, dopóki go nie dogoni. Ograniczony ruch = 1:1. Ukryty, gdy nie ma czego przewijać.
const progress = document.createElement("div");
progress.className = "progress";
progress.setAttribute("aria-hidden", "true");
progress.innerHTML = "<i></i>";
document.body.append(progress);
const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)");
let maxScroll = 1, target = 0, shown = 0, last = 0, raf = 0;

function draw(now) {
  const dt = Math.min(0.05, Math.max(0, (now - last) / 1000));
  last = now;
  shown = reduceMotion.matches ? target : shown + (target - shown) * (1 - Math.exp(-dt / 0.12));
  if (Math.abs(target - shown) < 1e-4) shown = target;
  progress.style.setProperty("--p", shown.toFixed(4));
  raf = shown === target ? 0 : requestAnimationFrame(draw);
}
function onScroll() {
  target = Math.min(1, Math.max(0, scrollY / maxScroll));
  if (!raf) { last = performance.now() - 16; raf = requestAnimationFrame(draw); }
}
// Bez skoku przy zmianie rozmiaru (na telefonie pasek adresu zmienia wysokość okna w trakcie przewijania).
function measure() {
  const m = root.scrollHeight - innerHeight;
  progress.hidden = m < 40;
  maxScroll = Math.max(1, m);
  onScroll();
}
measure();
shown = target;
addEventListener("scroll", onScroll, { passive: true });
addEventListener("resize", measure);
if (main && "ResizeObserver" in window) new ResizeObserver(measure).observe(main);

// Lightbox (Task 5): zwykły klik w zdjęcie otwiera podgląd zamiast pełnego pliku; moduł ładuje się
// leniwie (wcześniej, gdy kursor najedzie na pierwsze zdjęcie). Ctrl/⌘/Shift/środkowy = zwykły link.
// ?v= z adresu main.js (build_pages) idzie dalej, żeby po wdrożeniu nie wziąć starego lightbox.js z cache.
const loadLightbox = () => import("./lightbox.js" + new URL(import.meta.url).search);
document.addEventListener("click", (e) => {
  const a = e.target instanceof Element && e.target.closest("a[data-lb]");
  if (!a || e.defaultPrevented || e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
  e.preventDefault();
  const items = [...document.querySelectorAll("a[data-lb]")];
  loadLightbox().then((m) => m.open(items.indexOf(a), items), () => { location.href = a.href; });
});
document.querySelector("a.ph")?.addEventListener("pointerenter", loadLightbox, { once: true });
