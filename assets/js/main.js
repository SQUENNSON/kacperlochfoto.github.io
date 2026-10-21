const root = document.documentElement;
root.classList.add("js");

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
