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

// Lightbox (Task 5): zwykły klik w zdjęcie otwiera podgląd zamiast pełnego pliku; moduł ładuje się
// leniwie (wcześniej, gdy kursor najedzie na pierwsze zdjęcie). Ctrl/⌘/Shift/środkowy = zwykły link.
const loadLightbox = () => import("./lightbox.js");
document.addEventListener("click", (e) => {
  const a = e.target instanceof Element && e.target.closest("a[data-lb]");
  if (!a || e.defaultPrevented || e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
  e.preventDefault();
  const items = [...document.querySelectorAll("a[data-lb]")];
  loadLightbox().then((m) => m.open(items.indexOf(a), items), () => { location.href = a.href; });
});
document.querySelector("a.ph")?.addEventListener("pointerenter", loadLightbox, { once: true });
