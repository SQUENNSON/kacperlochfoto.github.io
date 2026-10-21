# Rebuild portfolio SQphoto — plan implementacji

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Zastąpić obecną stronę statycznym portfolio SQphoto w wersji „Papier”. Stały lewy pasek, galerie Sport i Reportaż bez przycinania kadrów, lightbox z zoomem, płynne animacje, wysoka wydajność.

**Architecture:** Lokalne skrypty Pythona robią trzy rzeczy: kodują zdjęcia z `B:\NA STRONE` do AVIF i zapisują manifest `data/photos.json`, odtwarzają logo jako SVG, a z szablonów Jinja2 i `data/site.json` generują statyczne HTML-e. Wynik trafia do commita, a GitHub Pages serwuje pliki bez buildu. W przeglądarce działa tylko mały vanilla JS (moduły ES): reveal przy przewijaniu, menu mobilne i leniwie ładowany lightbox. Przejścia między stronami robi CSS View Transitions.

**Tech Stack:**
- Python 3.14 + Pillow 12.2 (AVIF), Jinja2 3.1, fontTools + brotli, pytest
- vanilla HTML/CSS/JS (ES modules), testy JS przez `node --test` (Node 24)
- e2e: `playwright-core` z kanałem `chrome` (lokalny Chrome, bez pobierania przeglądarek); Lighthouse CLI przez `npx`

**Spec:** `docs/superpowers/specs/2026-10-21-rebuild-portfolio-design.md`

## Global Constraints

- Gałąź `rebuild`. **Nie mergować do `main` ani nie pushować** bez zgody użytkownika (`main` = produkcja GitHub Pages).
- Wszystkie odnośniki i ścieżki do zasobów są **względne**. Żadnych `href="/…"`, `src="/…"` ani absolutnych URL-i do własnych zasobów. Wyjątki: `og:url`/canonical/`og:image` (absolutny `https://squennson.github.io/kacperlochfoto.github.io/…`) oraz `<base>` w `404.html`.
- Nie ruszać `CNAME` ani ustawień domeny.
- Źródła zdjęć: `B:\NA STRONE\SPORT` i `B:\NA STRONE\REPORTAŻ` (folder z „Ż”).
  - Pomijane pliki: `SPORT/DSC01355.jpg`, `SPORT/DSC04110.jpg`, `SPORT/DSC07121.jpg`, `REPORTAŻ/DSC01355.jpg`, `REPORTAŻ/DSC03143.jpg`, `REPORTAŻ/DSC03835.jpg`, `REPORTAŻ/DSC03504.jpg`, `REPORTAŻ/DSC03639.jpg`.
  - Wynik: Sport 84, Reportaż 97, razem 181.
- AVIF: `quality=72`, `speed=6`. Bez EXIF, z zachowanym profilem ICC źródła. Kalibracja zrobiona 2026-10-21: na wycinkach 1:1 brak widocznej różnicy, PSNR min 35.3 dB na 4 zdjęciach testowych.
- Szerokości wariantów: `[w for w in (800, 1600) if w < W] + [W]`, gdzie W to natywna szerokość. Bez powiększania.
- Budżet obrazów `assets/photos/` ≤ 300 MB łącznie.
- Wydajność:
  - Lighthouse mobile Performance ≥ 95, LCP < 2.0 s, CLS < 0.02,
  - JS łącznie ≤ 15 KB gzip, CSS ≤ 20 KB gzip,
  - strona główna przed pierwszym scrollem ładuje ≤ 1.5 MB.
- Wygląd „Papier”:
  - kolory: `--bg:#f4f2ee`, `--ink:#141413`, `--muted:#8b877e`, `--line:rgba(20,20,19,.08)`, `--gap:6px`, `--ease:cubic-bezier(.16,1,.3,1)`,
  - fonty: Instrument Serif Italic + Schibsted Grotesk 400–700, hostowane lokalnie (woff2, subsety `latin` + `latin-ext`).
- Zakazane: canvas/cząsteczki, własny kursor, loader, glow/poświaty, mocne gradienty, karuzela, napisy-podpowiedzi („DRAG”, „VIEW”), `transform` na `body`, podpisy pod zdjęciami.
- `prefers-reduced-motion: reduce` wyłącza reveal, powiększenie po najechaniu, przejścia stron i animacje lightboxa.
- Windows: skrypty Pythona na starcie robią `sys.stdout.reconfigure(encoding="utf-8")`, bo konsola jest w cp1250, a nazwy mają polskie znaki. Pliki czytamy i zapisujemy z `encoding="utf-8"`, a JSON z `ensure_ascii=False`.
- Copy kontaktu: tel. `538 392 636` (`tel:+48538392636`), `loch.kacper@gmail.com`, Instagram `@sq_photo__` → `https://www.instagram.com/sq_photo__/`, lokalizacja `Nowy Sącz · Małopolska`.

## Review Focus

1. **Hosting pod podścieżką** `/kacperlochfoto.github.io/`. Każda strona otwarta pod tą ścieżką ładuje CSS, JS, fonty i zdjęcia bez żadnego 404. Test e2e w Task 6 serwuje folder nadrzędny `B:\GITHUB`.
2. **Przycisk „wstecz” na telefonie przy otwartym lightboxie** zamyka lightbox i nie opuszcza strony. Test w Task 5.
3. **Pinch-zoom na telefonie** nie przełącza zdjęcia, a swipe działa tylko bez przybliżenia. Testy `zoom-math` i e2e w Task 5.
4. **Brak JS lub błąd JS:** galerie są widoczne (reveal nie chowa treści bez klasy `js`), a kliknięcie zdjęcia otwiera pełny plik AVIF. Test w Task 4.
5. **Wąski ekran 320 px:** brak poziomego scrolla na żadnej stronie, menu mobilne działa. Test e2e w Task 6.

---

## Struktura plików

```
.nojekyll                         # Pages serwuje pliki bez Jekylla
index.html                        # GENEROWANE (strona główna)
sport/index.html                  # GENEROWANE
reportaz/index.html               # GENEROWANE
o-mnie/index.html                 # GENEROWANE
kontakt/index.html                # GENEROWANE
404.html                          # GENEROWANE
assets/css/style.css              # ręcznie: tokeny, layout, komponenty, @font-face
assets/js/main.js                 # moduł: klasa js, reveal, menu mobilne, leniwy import lightboxa
assets/js/lightbox.js             # moduł: <dialog>, nawigacja, swipe, historia, zoom
assets/js/zoom-math.js            # czyste funkcje zoomu/panu (testowane w node)
assets/fonts/*.woff2              # 4 pliki z fetch_fonts.py
assets/img/logo.svg, favicon.svg, apple-touch-icon.png, og.jpg
assets/photos/<slug>-<w>.avif     # GENEROWANE
data/photos.json                  # GENEROWANE (manifest)
data/site.json                    # ręcznie: copy, hero, wybór na główną
tools/requirements.txt            # pillow>=12.2, jinja2>=3.1, fonttools>=4.55, brotli>=1.1, pytest>=8
tools/build_photos.py
tools/fetch_fonts.py              # Google Fonts → assets/fonts + tools/fonts-src/*.ttf (gitignored)
tools/build_logo.py
tools/build_pages.py
tools/templates/{base,home,gallery,about,contact,404}.html.j2, _macros.html.j2
tools/package.json                # devDependencies: playwright-core
tools/e2e/smoke.mjs
tests/conftest.py                 # dodaje tools/ do sys.path, fixture repo_root
tests/test_photos.py, tests/test_logo.py, tests/test_pages.py, tests/test_budgets.py
tests/js/zoom-math.test.mjs
```

Do `.gitignore` dopisać: `tools/fonts-src/`, `tools/node_modules/`, `__pycache__/`, `.pytest_cache/`.

---

### Task 1: Pipeline zdjęć (AVIF + manifest)

**Files:**
- Create: `tools/requirements.txt`, `tools/build_photos.py`, `tests/conftest.py`, `tests/test_photos.py`
- Generate: `assets/photos/*.avif`, `data/photos.json`
- Modify: `.gitignore` (wpisy jak wyżej)

**Interfaces:**
- Produces:
  - `slugify(category_dir: str, filename: str) -> str`
  - `variant_widths(width: int) -> list[int]`
  - `collect_sources(root: Path) -> list[Source]`, gdzie `@dataclass Source(category: str, path: Path, slug: str)`, a `category` ∈ {`"sport"`, `"reportaz"`}
  - `encode_photo(src: Source, repo_root: Path) -> dict`
  - `main(argv: list[str] | None = None) -> int`
  - CLI: `py tools/build_photos.py [--source "B:\NA STRONE"] [--repo .] [--jobs N]`
- Kształt manifestu `data/photos.json`, z którego korzystają Task 4–6:

```json
{"generated": "2026-10-21T12:00:00",
 "photos": [{"slug": "sport-dsc00035", "category": "sport", "source": "DSC00035.jpg",
             "w": 3072, "h": 2458, "color": "#5a6b3c",
             "variants": [{"w": 800, "h": 640, "file": "assets/photos/sport-dsc00035-800.avif", "bytes": 81234}, …]}]}
```

  Kolejność: najpierw `sport`, potem `reportaz`, w każdej kategorii po nazwie pliku bez rozróżniania wielkości liter. Pole `file` jest względne od korzenia repo.

- [ ] **Step 1: Napisz testy jednostkowe w `tests/test_photos.py`**

```python
def test_variant_widths():
    assert variant_widths(3072) == [800, 1600, 3072]
    assert variant_widths(2458) == [800, 1600, 2458]
    assert variant_widths(1440) == [800, 1440]
    assert variant_widths(700) == [700]

def test_slugify():
    assert slugify("SPORT", "DSC00109-2.jpg") == "sport-dsc00109-2"
    assert slugify("REPORTAŻ", "DSC03170-3.jpg") == "reportaz-dsc03170-3"
    assert slugify("SPORT", "2B9AE30E-EB7B-4CBC-9673-F3754CC0FA64.jpg") == "sport-2b9ae30e"
    assert slugify("SPORT", "IMG_3722.JPG") == "sport-img-3722"

def test_encode_photo_synthetic(tmp_path):
    # syntetyczny JPEG 3072x2458 z EXIF (GPS) i profilem sRGB (ImageCms.createProfile("sRGB"))
    # → 3 pliki AVIF o szer. 800/1600/3072 i wysokości round(w*2458/3072)
    # → Image.open(avif).info zawiera "icc_profile" i NIE zawiera "exif"
    # → wpis["color"] pasuje do r"^#[0-9a-f]{6}$"; wpis["variants"][i]["bytes"] == rozmiar pliku
    # → drugie wywołanie nie nadpisuje plików (mtime bez zmian)
```

Dodaj testy na prawdziwym folderze, `@pytest.mark.skipif(not Path(r"B:\NA STRONE").exists(), …)`:
- `test_collect_sources_counts`: 84 `sport`, 97 `reportaz`, żadnego pliku z listy pominiętych, slugi unikalne.
- `test_psnr_quality` (`@pytest.mark.slow`): `SPORT/IMG_3723.JPG` zakodowany jak w `encode_photo` w pełnej rozdzielczości ma PSNR ≥ 34.5 dB względem źródła.

- [ ] **Step 2: Uruchom testy i sprawdź, że padają**

Run: `py -m pytest tests/test_photos.py -q`
Expected: FAIL (ImportError `build_photos`)

- [ ] **Step 3: Zaimplementuj `tools/build_photos.py`**

- Mapa kategorii: `{"SPORT": "sport", "REPORTAŻ": "reportaz"}`. Zbiór `EXCLUDE` jak w Global Constraints.
- `slugify`: część kategorii z tej mapy. Stem pliku: małe litery, `_` → `-`. Stem pasujący do UUID (`^[0-9A-F]{8}-[0-9A-F]{4}-`) skracamy do pierwszych 8 znaków.
- `encode_photo`:
  - `ImageOps.exif_transpose`, potem `.convert("RGB")`,
  - dla każdej szerokości `resize((w, round(w*H/W)), Image.LANCZOS)`,
  - `save(..., "AVIF", quality=72, speed=6, icc_profile=<icc źródła lub pominięte>)`, bez `exif=`,
  - pomija plik wyjściowy, jeśli istnieje i jest nowszy od źródła,
  - `color` = hex z `im.resize((1, 1), Image.BOX)`.
- `main`:
  - `multiprocessing.Pool(jobs)` (domyślnie `os.cpu_count()-1`), postęp na stdout po ASCII,
  - zapis JSON `indent=1, ensure_ascii=False`,
  - usuwa z `assets/photos/` pliki `.avif`, których nie ma w manifeście.

- [ ] **Step 4: Uruchom testy jednostkowe i sprawdź, że przechodzą**

Run: `py -m pytest tests/test_photos.py -q -m "not slow"` → PASS, potem `py -m pytest tests/test_photos.py -q -m slow` → PASS

- [ ] **Step 5: Zbuduj pełny zestaw**

Run: `py tools/build_photos.py --jobs 6` (czas rzędu 10–20 min, uruchamiaj w tle)

Expected:
- `data/photos.json` ma 181 wpisów, w tym 6 pionowych: `sport-dsc00109`, `sport-dsc06738`, `reportaz-dsc01846`, `reportaz-dsc03186`, `reportaz-dsc03504-2`, `reportaz-dsc09721`,
- `du -sh assets/photos` ≤ 300 MB,
- ponowne uruchomienie kończy się w < 30 s, bo nic nie koduje.

- [ ] **Step 6: Commit**

```bash
git add tools/requirements.txt tools/build_photos.py tests/conftest.py tests/test_photos.py .gitignore data/photos.json assets/photos
git commit -m "feat(photos): pipeline AVIF + manifest 181 zdjęć"
```

---

### Task 2: Fonty i logo

**Files:**
- Create: `tools/fetch_fonts.py`, `tools/build_logo.py`, `tests/test_logo.py`, `assets/css/style.css` (na razie tylko blok `@font-face`)
- Generate: `assets/fonts/instrument-serif-italic-latin.woff2`, `…-latin-ext.woff2`, `assets/fonts/schibsted-grotesk-latin.woff2`, `…-latin-ext.woff2`, `assets/img/logo.svg`, `assets/img/favicon.svg`, `assets/img/apple-touch-icon.png`

**Interfaces:**
- Produces:
  - `assets/img/logo.svg`: `fill="currentColor"`, ciasny `viewBox`, `<title>SQphoto</title>`
  - rodziny CSS `"Instrument Serif"` (`font-style: italic`) i `"Schibsted Grotesk"` (`font-weight: 400 700`)
  - `glyph_path(font: TTFont, text: str, size: float, x: float, baseline: float, tracking_em: float = 0) -> tuple[str, float]`, zwraca SVG path `d` i szerokość
- Consumes: TTF-y z `tools/fonts-src/`, które pobiera `fetch_fonts.py`

- [ ] **Step 1: Napisz testy `tests/test_logo.py`**

```python
def test_logo_svg():
    # XML parsuje się; brak elementów <text>; ma viewBox; ≥1 <path>; fill="currentColor"
    # proporcja szer/wys z viewBox w przedziale 3.2–4.2 (1.png: 398×107 ≈ 3.72)
def test_favicon_and_touch_icon():
    # favicon.svg istnieje i ma viewBox kwadratowy; apple-touch-icon.png ma 180×180
def test_fonts_present():
    # 4 pliki woff2 > 5 KB każdy; style.css zawiera 4 reguły @font-face z unicode-range
    # i src: url("../fonts/…woff2") format("woff2")
```

- [ ] **Step 2: Uruchom testy i sprawdź, że padają**

Run: `py -m pytest tests/test_logo.py -q` → FAIL

- [ ] **Step 3: Zaimplementuj `tools/fetch_fonts.py`**

1. Pobierz CSS z `https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@1&family=Schibsted+Grotesk:wght@400..700&display=swap`, z nagłówkiem User-Agent nowoczesnego Chrome, żeby dostać woff2.
2. Z bloków `/* latin */` i `/* latin-ext */` każdej rodziny pobierz woff2 do nazw jak wyżej.
3. Wypisz gotowy blok 4× `@font-face` (z `unicode-range` i `font-display: swap`) i wstaw go na początek `assets/css/style.css`.
4. Pobierz TTF-y do `tools/fonts-src/`:
   - `https://github.com/google/fonts/raw/main/ofl/instrumentserif/InstrumentSerif-Italic.ttf`
   - `https://github.com/google/fonts/raw/main/ofl/intertight/InterTight%5Bwght%5D.ttf`

   Sprawdź, czy plik zaczyna się od bajtów `\x00\x01\x00\x00`, bo zła ścieżka zwraca HTML.

- [ ] **Step 4: Zaimplementuj `tools/build_logo.py`**

Fonty dobrano przez porównanie z `1.png` (2026-10-21): „SQ” to **Instrument Serif Italic**, „photo” to **Inter Tight w wariancie wght=800** (`fontTools.varLib.instancer.instantiateVariableFont`). Ścieżki rysuje `SVGPathPen` + `TransformPen` (oś Y odwrócona).

Układ jak w `1.png`:
- „SQ” ma wysokość wersalików równą wysokości wydłużenia „h” w „photo”,
- obie części stoją na wspólnej linii bazowej,
- „photo” zaczyna się tuż za „Q”, a ogonek „Q” przechodzi pod „p” (zakładka ok. 0.05 em rozmiaru SQ),
- tracking „photo” -0.02 em.

Pozostałe wyjścia:
- `favicon.svg`: samo „SQ” w kolorze `#141413` na kwadracie `#f4f2ee`,
- `apple-touch-icon.png`: to samo w 180×180, rysowane przez PIL `ImageFont.truetype` z TTF.

Źródło referencyjne do porównania: `C:\Users\lochk\AppData\Local\Temp\claude\C--Users-lochk\87fcaa7e-fdd5-4d22-b855-7e80989c0be2\scratchpad\logo-zip\1.png`. Jeśli ścieżka nie istnieje, rozpakuj `1.png` z `B:\POBRANE\Black and White Minimalist Elegant Modern Typography  Creative Studio Brand Logo.zip`.

- [ ] **Step 5: Uruchom i sprawdź**

Run: `py tools/fetch_fonts.py && py tools/build_logo.py && py -m pytest tests/test_logo.py -q` → PASS

Kontrola wizualna: zrób zrzut headless Chrome z `logo.svg` obok `1.png` i zapisz go w scratchpadzie. Proporcje, zakładka „Q” pod „p” i grubość „photo” mają odpowiadać oryginałowi. Zrzut załącz w raporcie.

- [ ] **Step 6: Commit**

```bash
git add tools/fetch_fonts.py tools/build_logo.py tests/test_logo.py assets/fonts assets/img assets/css/style.css .gitignore
git commit -m "feat(brand): lokalne fonty + logo SQphoto jako SVG"
```

---

### Task 3: Szkielet strony (generator, pasek, menu, O mnie, Kontakt, 404, przejścia) i usunięcie starej strony

**Files:**
- Create: `tools/build_pages.py`, `tools/templates/base.html.j2`, `_macros.html.j2`, `about.html.j2`, `contact.html.j2`, `404.html.j2`, `data/site.json`, `assets/js/main.js`, `tests/test_pages.py`, `.nojekyll`
- Modify: `assets/css/style.css` (tokeny, layout, pasek, menu, typografia, strony tekstowe, przejścia)
- Delete: `index.html` (stary), `o-mnie.html`, `projekt-*.html` (6), `Projekt-turniej-żaków.html`, `realizacja-*.html` (4), `turniej-dobry-grajek.html`, `script.js`, `style.css` (stary, w korzeniu), `lightbox.js`, folder `zdjecia/`
- Generate: `o-mnie/index.html`, `kontakt/index.html`, `404.html` (strony z galeriami dochodzą w Task 4)

**Interfaces:**
- Consumes: `logo.svg` i fonty z Task 2
- Produces:
  - `build_pages.py`:
    - `PAGES: list[Page]`, gdzie `@dataclass Page(key: str, out: str, template: str, nav: str | None)` z kluczami `home`, `sport`, `reportaz`, `o-mnie`, `kontakt`, `404`
    - `prefix_for(out: str) -> str` (`"index.html"` → `""`, `"sport/index.html"` → `"../"`, `"404.html"` → `""`)
    - `render_all(repo_root: Path) -> list[Path]`
    - CLI: `py tools/build_pages.py`
  - Jinja context każdej strony: `site`, `page`, `p` (prefiks), `nav_items` = lista `{key, label, href, num}` w kolejności Sport `01`, Reportaż `02`, O mnie `03`, Kontakt `04`
  - Bloki szablonu `base.html.j2`: `head_extra`, `main`
  - Elementy DOM, z których korzystają Task 4–5:
    - `<aside class="side">`: logo, „Kacper Loch”, podtytuł, `<nav class="nav">`, stopka z IG i lokalizacją
    - `<header class="topbar">` (≤ 900 px) z `<button class="menu-btn" aria-expanded="false" aria-controls="nav">`
    - `<main id="main">`
  - `main.js` (`<script type="module" src="{{p}}assets/js/main.js">`):
    - na starcie `document.documentElement.classList.add("js")`
    - eksportuje nic. Task 4 dopisuje do niego reveal, a Task 5 leniwy import lightboxa.

- [ ] **Step 1: Napisz testy `tests/test_pages.py` dla stron szkieletu**

```python
def test_internal_urls_are_relative(built):  # built = render_all(tmp kopia repo) albo repo
    # dla każdego wygenerowanego HTML: żadne href/src/srcset (poza http(s)://, mailto:, tel:) nie zaczyna się od "/"
    # i każda względna ścieżka (bez #/query) wskazuje na istniejący plik lub katalog z index.html
def test_nav_active_and_numbers(built):
    # w o-mnie/index.html link „O mnie” ma aria-current="page"; numery 01–04 w kolejności Sport, Reportaż, O mnie, Kontakt
def test_contact_copy(built):
    # kontakt/index.html zawiera href="tel:+48538392636", href="mailto:loch.kacper@gmail.com",
    # href="https://www.instagram.com/sq_photo__/", tekst „Nowy Sącz · Małopolska”
def test_about_copy_has_only_existing_facts(built):
    # o-mnie zawiera „KS Turbacz”, „MKS Limanovia”, „Cracovii”, „Ekipy Fantasy”; strona ma <title> i meta description
def test_404_base(built):
    # 404.html zawiera inline script ustawiający <base href> na "/kacperlochfoto.github.io/" gdy pathname od tego się zaczyna, inaczej "/"
def test_old_site_removed(repo_root):
    # nie istnieją: o-mnie.html, script.js, lightbox.js, zdjecia/, żaden projekt-*.html / realizacja-*.html; istnieje .nojekyll
```

- [ ] **Step 2: Uruchom testy i sprawdź, że padają**

Run: `py -m pytest tests/test_pages.py -q` → FAIL

- [ ] **Step 3: Utwórz `data/site.json`**

Zawartość:
- `site`: `title` = `"SQphoto — Kacper Loch"`, `base_url` = `"https://squennson.github.io/kacperlochfoto.github.io/"`, `name` = `"Kacper Loch"`, `tagline` = `"fotografia sportowa i reportaż"`, `location` = `"Nowy Sącz · Małopolska"`, `phone` = `"538 392 636"`, `phone_href` = `"tel:+48538392636"`, `email` = `"loch.kacper@gmail.com"`, `instagram` = `"https://www.instagram.com/sq_photo__/"`, `instagram_handle` = `"@sq_photo__"`.
- `pages`: dla każdego klucza `title` i `description` (≤ 155 znaków, PL).

Tekst O mnie bierzemy dosłownie z obecnego `o-mnie.html`, w 5 akapitach:
1. Lead (kursywa szeryfowa, duży): „Fotograf z Mszany Dolnej. 19 lat, aparat w ręce od najmłodszych lat — i to nigdy nie przeszło.”
2. „Fotografia to moja pasja od najmłodszych lat, a od niedawna również profesjonalne zajęcie. Specjalizuję się w fotografii sportowej, gdzie dynamika i emocje są kluczem do uchwycenia niezapomnianych chwil.”
3. „W mojej dotychczasowej karierze miałem przyjemność tworzyć pełne reportaże meczowe dla klubów takich jak KS Turbacz (V liga) i MKS Limanovia (IV liga). Doświadczenie zbierałem również na sparingu drużyny z Ekstraklasy — Cracovii.”
4. „Jednym z ciekawszych doświadczeń była obsługa fotograficzna charytatywnego meczu Ekipy Fantasy, w którym udział wzięły znane postacie ze świata internetu. Moje zdjęcia z tego wydarzenia można zobaczyć na profilach IG takich osób jak izak, Jakub Kiwior czy Tyszka, a także na oficjalnym koncie Ekipy Fantasy.”
5. „Poza sportem uwieczniam także imprezy okolicznościowe — od pikników rodzinnych po rocznice ślubów, dbając o to, by każda fotografia opowiadała Waszą wyjątkową historię.”

Nagłówek Kontaktu: „Porozmawiajmy”.

- [ ] **Step 4: Zaimplementuj generator, szablony, CSS i `main.js`**

**Head:**
- `<html lang="pl">`, `<title>`, description, canonical i `og:*` (absolutne z `base_url`),
- `<link rel="preload" as="font" type="font/woff2" crossorigin>` dla dwóch plików `-latin`,
- `<link rel="stylesheet" href="{{p}}assets/css/style.css">`, ikony.

**Layout desktop (> 900 px):**
- `body` to grid `clamp(260px, 27vw, 380px) 1fr`,
- `.side` ma `position: sticky; top: 0; height: 100dvh`, `border-right: 1px solid var(--line)`, padding `36px 30px 28px`,
- logo ma szerokość 150 px; „KACPER LOCH” to grotesk 600, 10.5 px, `letter-spacing: .24em`; podtytuł to Instrument Serif italic, 16 px, `--muted`.

**Menu (`.nav`):**
- odstęp od podtytułu 54 px,
- pozycja = numer (10 px, `--muted`) + `.roll` z dwiema warstwami: `<b>` (grotesk 600, 12.5 px, wersaliki, `.17em`) i `<em>` (Instrument Serif italic, 21 px),
- na `:hover`, `:focus-visible` i `[aria-current=page]` obie warstwy jadą `translateY(-100%)`, 0.6 s, `var(--ease)`.

**Mobile (≤ 900 px):**
- `.side` się chowa, a `.topbar` jest sticky, wysokość 56 px: logo 110 px po lewej, przycisk menu (dwie kreski) po prawej,
- menu otwiera pełnoekranową nakładkę `#nav` w kolorze `--bg`, z dużymi pozycjami (`<em>` widoczne, 34 px), stopką z kontaktem i fade + slide 12 px w 0.45 s,
- `main.js` przełącza `aria-expanded` i klasę `menu-open` na `<html>`, a Esc zamyka. Blokada przewijania przez `overflow: hidden` na `html.menu-open`, **nie** przez transform.

**O mnie:** kolumna treści max 62ch, padding `clamp(32px, 6vw, 96px)`; lead w Instrument Serif italic `clamp(28px, 3.2vw, 44px)`; akapity w groteskach 17 px / 1.65. Pod tekstem para zdjęć: miejsce z `pages["o-mnie"].photos` uzupełnia Task 4 (szablon używa makra wiersza z Task 4, więc na razie zostaw blok `{% block photos %}{% endblock %}`).

**Kontakt:** „Porozmawiajmy” w Instrument Serif italic `clamp(44px, 6vw, 88px)`, a pod spodem trzy duże linki (telefon, mail, Instagram) z podkreśleniem rozjeżdżającym się na hover i lokalizacją.

**404:** w `<head>`, przed czymkolwiek innym:

```html
<script>document.write('<base href="'+(location.pathname.indexOf('/kacperlochfoto.github.io/')===0?'/kacperlochfoto.github.io/':'/')+'">')</script>
```

Treść: „Nie ma takiej strony.” + link do strony głównej (prefiks `""`).

**Przejścia stron (CSS):**
- `@view-transition { navigation: auto; }`, `.side` i `.topbar` z `view-transition-name: chrome`, żeby pasek stał w miejscu,
- `::view-transition-old(root)` to fade-out 0.25 s, `::view-transition-new(root)` to fade-in + `translateY(10px → 0)` 0.5 s, `var(--ease)`,
- przy reduced motion: `animation: none`.

**Pozostałe:** fokus widoczny (`outline: 2px solid var(--ink); outline-offset: 3px`). Usuń stare pliki z listy Delete i dodaj pusty `.nojekyll`.

- [ ] **Step 5: Uruchom testy i sprawdź, że przechodzą**

Run: `py tools/build_pages.py && py -m pytest tests/test_pages.py -q` → PASS

Kontrola wizualna: serwer `py -m http.server 8080` w korzeniu repo, zrzuty headless Chrome `o-mnie/` i `kontakt/` przy 1440×900 i 390×844. Pasek, typografia i kolory mają odpowiadać makiecie A z `.superpowers/brainstorm/598-1792579544/content/wyglad.html`. Zrzuty załącz w raporcie.

- [ ] **Step 6: Commit**

```bash
git add -A   # obejmuje usunięcia starej strony; .superpowers/, node_modules i fonts-src są w .gitignore
git status --short | head -40   # sprawdź, że w commicie nie ma nic spoza tego taska
git commit -m "feat(shell): generator stron, pasek, menu, O mnie, Kontakt, 404; usunięcie starej strony"
```

---

### Task 4: Galerie, hero, strona główna i reveal

**Files:**
- Create: `tools/templates/home.html.j2`, `tools/templates/gallery.html.j2`
- Modify: `tools/build_pages.py`, `tools/templates/_macros.html.j2`, `tools/templates/about.html.j2`, `data/site.json`, `assets/css/style.css`, `assets/js/main.js`, `tests/test_pages.py`
- Generate: `index.html`, `sport/index.html`, `reportaz/index.html`, `o-mnie/index.html`

**Interfaces:**
- Consumes: `data/photos.json` (Task 1), `PAGES`, `prefix_for` i `base.html.j2` (Task 3)
- Produces:
  - `pair_rows(photos: list[dict]) -> list[list[dict]]`
  - `srcset(photo: dict, p: str) -> str`
  - Makro Jinja `row(photos, p, sizes, eager=False)`
  - Znaczniki dla lightboxa (Task 5):
    - każdy klikalny obraz to `<a class="ph" href="{{p}}<największy wariant>" data-lb data-srcset="<pełny srcset>" data-w data-h style="--c:<color>">`, a w środku `<img>`,
    - kolejność `[data-lb]` w DOM = kolejność w lightboxie,
    - hero też ma `data-lb` i jest pierwszy.

- [ ] **Step 1: Dopisz testy do `tests/test_pages.py`**

```python
def test_pair_rows_pairs_verticals():
    # wejście: [H1, V1, H2, H3, V2, H4] (V = h>w) → wiersze: [[H1, H2], [V1, V2], [H3, H4]]
    # każdy element występuje dokładnie raz; kolejność poziomych zachowana
def test_pair_rows_odd_tail():
    # 5 poziomych → ostatni wiersz ma 1 element
def test_galleries_complete(built):
    # sport/index.html: 84 elementy [data-lb] (hero + 83 w siatce, hero nie powtarza się w siatce);
    # reportaz: 97; index.html: hero + picks z site.json (każdy slug istnieje w manifeście)
def test_images_have_dimensions_and_lazy(built):
    # każdy <img> ma width, height i niepusty alt (zdjęcia: "Sport — fotografia Kacpra Locha" / "Reportaż — fotografia Kacpra Locha");
    # hero ma fetchpriority="high" i brak loading=lazy;
    # obrazy w siatce mają loading="lazy" decoding="async"; srcset zawiera tylko pliki z manifestu
def test_no_js_shows_content():
    # style.css: reguła ukrywająca reveal jest ograniczona selektorem html.js (np. "html.js [data-reveal]")
```

- [ ] **Step 2: Uruchom testy i sprawdź, że nowe padają**

Run: `py -m pytest tests/test_pages.py -q` → FAIL (`pair_rows` i galerie)

- [ ] **Step 3: Uzupełnij `data/site.json`**

Wybór kuratorski (zrobiony na podstawie arkuszy miniatur):
- `pages.home.hero` = `"sport-img-3723"`, `hero_focus` = `"50% 40%"`.
- `pages.home.picks` (16):

```json
["sport-dsc06898", "sport-dsc07659", "reportaz-dsc03639-2", "sport-2b9ae30e",
 "sport-dsc00109", "reportaz-dsc01846", "reportaz-dsc08315", "sport-dsc00420",
 "sport-dsc07751", "reportaz-dsc02953", "sport-dsc00488", "reportaz-dsc07310",
 "sport-dsc01751-2", "reportaz-dsc03784", "reportaz-dsc09157", "sport-dsc06892"]
```

- `pages.sport.hero` = `"sport-dsc05833"`, `hero_focus` = `"50% 35%"`.
- `pages.reportaz.hero` = `"reportaz-dsc08431"`, `hero_focus` = `"50% 45%"`.
- `pages["o-mnie"].photos` = `["sport-dsc01937", "reportaz-dsc03156"]`.

Jeśli kadr hero źle wygląda w proporcji 16:6.4, popraw `hero_focus` po obejrzeniu zrzutu.

- [ ] **Step 4: Zaimplementuj galerie**

**`pair_rows`:** idzie po kolejności. Gdy wiersz zaczyna się od pionowego, a następny element jest poziomy, wciąga najbliższy kolejny pionowy z okna 8 elementów (jeśli istnieje). Gdy wiersz zaczyna się od poziomego, a następny jest pionowy, odkłada pionowy na później i bierze najbliższy poziomy. Ostatni nieparzysty element ląduje sam w wierszu.

**Wiersz:**
- `<div class="row">` z `display: flex; gap: var(--gap)`,
- każde `a.ph` ma `flex: <w/h> 1 0`, `aspect-ratio: w/h`, `background: var(--c)` i `overflow: hidden`, a `img` ma `width: 100%; height: 100%; display: block`. Efekt: równa wysokość i brak przycięcia,
- `sizes` siatki: `"(max-width: 900px) 100vw, 37vw"`,
- `alt`: `"Sport — fotografia Kacpra Locha"` albo `"Reportaż — fotografia Kacpra Locha"`, zależnie od kategorii,
- ≤ 900 px: `.row { flex-direction: column }`, każdy element ma pełną szerokość i własną proporcję,
- pojedynczy element w wierszu ma szerokość 100% w ramach max-width kolumny.

**Hero:**
- `<a class="ph hero" …>` z `aspect-ratio: 16/6.4` (≤ 900 px: `5/4`), `img` z `object-fit: cover; object-position: <hero_focus>`,
- `loading="eager" fetchpriority="high"`, `sizes="(max-width: 900px) 100vw, 73vw"`,
- w `<head>` (blok `head_extra`): `<link rel="preload" as="image" type="image/avif" imagesrcset=… imagesizes=… fetchpriority="high">`.

**Strona główna:** hero + wiersze z `picks`, a na końcu dwa duże linki „Sport →” i „Reportaż →” (Instrument Serif italic, 32 px) z liczbą zdjęć (84 i 97) z manifestu.

**Galerie Sport i Reportaż:** hero + wszystkie zdjęcia kategorii poza hero, w kolejności manifestu, przez `pair_rows`.

**O mnie:** pod tekstem jeden wiersz z `pages["o-mnie"].photos`.

**Hover:**
- tylko `@media (hover: hover)`: `a.ph img` ma `transition: transform 1.1s var(--ease)`, a `a.ph:hover img` ma `transform: scale(1.035)`,
- bez cieni i bez poświaty.

**Reveal:**
- CSS: `html.js [data-reveal] { opacity: 0; transform: translateY(18px); transition: opacity .9s var(--ease) var(--d, 0s), transform .9s var(--ease) var(--d, 0s); }` oraz `html.js [data-reveal].in { opacity: 1; transform: none; }`,
- atrybut `data-reveal` dostają wiersze (`.row`) i bloki tekstu,
- w `main.js` jeden `IntersectionObserver` (`rootMargin: "0px 0px -8% 0px"`): elementy wchodzące w jednej partii dostają `--d` = 0, 0.08, 0.16 s… (max 0.32 s), klasę `in` i `unobserve`. Bez `IntersectionObserver` od razu dodaje `in` wszystkim,
- reduced motion: reguły reveal i hover wyłączone.

- [ ] **Step 5: Uruchom testy i sprawdź, że przechodzą**

Run: `py tools/build_pages.py && py -m pytest tests/test_pages.py -q` → PASS

Kontrola wizualna przy 1440×900 i 390×844: zrzuty `index.html`, `sport/` i `reportaz/` (pełna wysokość strony). Sprawdź brak przyciętych kadrów w siatce, pary pionowych zdjęć, kadr hero i brak luk. Zrzuty załącz.

- [ ] **Step 6: Commit**

```bash
git add tools data/site.json assets/css/style.css assets/js/main.js tests/test_pages.py index.html sport reportaz o-mnie
git commit -m "feat(galerie): hero, wiersze bez przycinania, strona główna, reveal"
```

---

### Task 5: Lightbox z zoomem

**Files:**
- Create: `assets/js/zoom-math.js`, `assets/js/lightbox.js`, `tests/js/zoom-math.test.mjs`, `tools/package.json`, `tools/e2e/lightbox.mjs`
- Modify: `assets/js/main.js` (leniwy import), `assets/css/style.css` (styl lightboxa)

**Interfaces:**
- Consumes: znaczniki `a.ph[data-lb]` z Task 4 (`href` = największy wariant, `data-srcset`, `data-w`, `data-h`)
- Produces:
  - `zoom-math.js`, gdzie stan to `{s, x, y}` (skala i przesunięcie w px względem środka):
    - `fitSize(imgW, imgH, vpW, vpH) -> {w, h}` (dopasowanie contain)
    - `clampScale(s, min = 1, max = 4) -> number`
    - `zoomAt(state, factor, px, py, vpW, vpH, fitW, fitH) -> state` (punkt pod kursorem stoi w miejscu)
    - `clampPan(state, vpW, vpH, fitW, fitH) -> state` (nie da się odsunąć krawędzi zdjęcia do środka ekranu; przy `s = 1` jest `x = y = 0`)
    - `pinch(state, d0, d1, cx, cy, vpW, vpH, fitW, fitH) -> state` (stosunek odległości palców d1/d0)
    - `isSwipe(dx, dy, dt, s) -> -1 | 0 | 1`: 1 = następne, -1 = poprzednie; tylko gdy `s === 1`, `|dx| > 60`, `|dx| > 1.5·|dy|` i `dt < 600`
  - `lightbox.js` eksportuje `open(index: number, items: Element[])`

- [ ] **Step 1: Napisz testy `tests/js/zoom-math.test.mjs` (node:test)**

```js
test("clampScale", () => { assert.equal(clampScale(0.5), 1); assert.equal(clampScale(9), 4); assert.equal(clampScale(2), 2); });
test("zoomAt keeps point under cursor", () => {
  const st = zoomAt({s:1,x:0,y:0}, 2, 300, 200, 1000, 800, 1000, 800);
  // punkt ekranu (300,200) przed i po zoomie mapuje na ten sam punkt obrazu: (px - vp/2 - x)/s stałe
});
test("clampPan at s=1 centers", () => { assert.deepEqual(clampPan({s:1,x:50,y:-20}, 1000, 800, 1000, 800), {s:1,x:0,y:0}); });
test("clampPan limits edges at s=2", () => { const st = clampPan({s:2,x:5000,y:0}, 1000, 800, 1000, 800); assert.equal(st.x, 500); });
test("pinch scales by distance ratio and clamps", () => { /* d0=100,d1=250 → s=2.5; d1=1000 → s=4 */ });
test("isSwipe ignores when zoomed", () => { assert.equal(isSwipe(-120, 10, 200, 1), 1); assert.equal(isSwipe(-120, 10, 200, 2), 0); assert.equal(isSwipe(30, 0, 200, 1), 0); assert.equal(isSwipe(-120, 100, 200, 1), 0); });
```

- [ ] **Step 2: Uruchom testy i sprawdź, że padają**

Run: `node --test tests/js/` → FAIL (moduł nie istnieje)

- [ ] **Step 3: Zaimplementuj `zoom-math.js`**

- [ ] **Step 4: Uruchom testy i sprawdź, że przechodzą**

Run: `node --test tests/js/` → PASS

- [ ] **Step 5: Zaimplementuj `lightbox.js` i podłączenie w `main.js`**

**`main.js`:** delegowany `click` na `a[data-lb]`. Bez modyfikatorów (ctrl/meta/shift, środkowy przycisk) robi `preventDefault` i `import("./lightbox.js").then(m => m.open(i, items))`. `pointerenter` na pierwszym `a.ph` dociąga moduł wcześniej.

**Okno:**
- `<dialog class="lb">` tworzony raz, `showModal()`, tło `rgba(244,242,238,.97)` (papier),
- `<img>` dopasowany (contain) z `srcset` = `data-srcset` i `sizes="100vw"`,
- licznik `12 / 84` (grotesk 11 px, `--muted`), przyciski ← → ✕ (aria-label po polsku: „Poprzednie”, „Następne”, „Zamknij”),
- tło za zdjęciem w kolorze `--c`, dopóki obraz się nie załaduje.

**Nawigacja:**
- klawisze ←, →, Esc; klik w tło zamyka,
- swipe pointer events przez `isSwipe`,
- dociąganie sąsiadów: `new Image()` z tym samym srcset i sizes,
- przy zmianie zdjęcia crossfade 0.35 s, bez reduced motion.

**Zoom:**
- `wheel` (z `preventDefault`) wywołuje `zoomAt` z `factor = Math.exp(-deltaY * 0.0015)`,
- przeciąganie przy `s > 1` wywołuje `clampPan`,
- dwa wskaźniki wywołują `pinch`,
- dwuklik albo double-tap przełącza 1 ↔ 2.5,
- transform na `<img>`: `translate(x, y) scale(s)`, `will-change` tylko w trakcie gestu,
- gdy `s > 1` po raz pierwszy, `img.sizes` = `${Math.ceil(vpW * s)}px`, żeby przeglądarka dobrała większy wariant, aż do pełnego 3072,
- `touch-action: none` na obszarze zdjęcia.

**Historia:** `open` robi `history.pushState({lb: 1}, "")`, `popstate` zamyka bez ponownego `back`, a zamknięcie przyciskiem lub Esc robi `history.back()`, jeśli stan to `lb`.

**Po zamknięciu:** reset zoomu, fokus wraca na kliknięty element, zdjęcie pod spodem przewija się do widoku (`scrollIntoView({block: "nearest"})`).

**Rozmiar:** `lightbox.js` + `zoom-math.js` + `main.js` łącznie ≤ 15 KB gzip.

- [ ] **Step 6: Test e2e lightboxa**

`tools/package.json`: `{"private": true, "type": "module", "devDependencies": {"playwright-core": "^1.48.0"}}`, potem `cd tools && npm install`.

`tools/e2e/lightbox.mjs` (`chromium.launch({ channel: "chrome" })`, serwer `py -m http.server 8080` w korzeniu repo):
- desktop 1440×900 na `sport/`:
  - klik w 3. `a[data-lb]` otwiera `dialog.lb[open]` z licznikiem `3 / 84`,
  - `ArrowRight` daje `4 / 84`,
  - `mouse.wheel(0, -500)` nad zdjęciem daje transform zawierający `scale(` > 1, a po chwili `currentSrc` kończy się na `-3072.avif`,
  - `Escape` zamyka, a `location.href` się nie zmienia.
- mobile 390×844 (`hasTouch: true`) na `reportaz/`:
  - otwórz, wywołaj `page.goBack()`: dialog się zamyka, URL dalej `…/reportaz/`,
  - otwórz ponownie, zasymuluj pinch (CDP `Input.dispatchTouchEvent` z dwoma punktami rozchodzącymi się w poziomie): licznik bez zmian, skala > 1.
- skrypt kończy się kodem 0 i wypisuje `LIGHTBOX OK`.

Run: `node tools/e2e/lightbox.mjs` → `LIGHTBOX OK`

- [ ] **Step 7: Commit**

```bash
git add assets/js tests/js tools/package.json tools/package-lock.json tools/e2e/lightbox.mjs assets/css/style.css
git commit -m "feat(lightbox): pełny ekran, swipe, historia, zoom kółkiem i pinch"
```

---

### Task 6: OG, budżety, Lighthouse i smoke pod podścieżką

**Files:**
- Create: `tests/test_budgets.py`, `tools/e2e/smoke.mjs`, `assets/img/og.jpg`
- Modify: `tools/build_pages.py` (og:image), ewentualnie `assets/css/style.css` i `assets/js/*` (poprawki wydajności)

**Interfaces:**
- Consumes: wszystko z Task 1–5

- [ ] **Step 1: Napisz `tests/test_budgets.py`**

```python
def test_photo_budget(repo_root):   # suma assets/photos/*.avif ≤ 300 * 1024**2
def test_js_css_gzip(repo_root):    # gzip(main.js)+gzip(lightbox.js)+gzip(zoom-math.js) ≤ 15*1024; gzip(style.css) ≤ 20*1024
def test_home_first_screen_weight(repo_root):
    # profil Lighthouse mobile (412 CSS px, DPR 1.75): index.html + style.css + main.js + 2 preloadowane woff2
    # + wariant hero dla sizes 100vw (≈721px → najmniejszy ≥: 800) + pierwszy wiersz picks (100vw → 800, 2 zdjęcia) ≤ 1.5 MB
    # desktop Retina (1440, DPR2: hero → 3072, wiersz → 1600) tylko wypisz informacyjnie (print), bez asercji —
    # świadoma decyzja: jakość na dużych ekranach > waga, a dodatkowy wariant 2400 przekroczyłby budżet repo
def test_manifest_files_exist(repo_root):  # każdy variants[].file istnieje, bytes się zgadza
```

- [ ] **Step 2: Uruchom testy budżetów**

Run: `py -m pytest tests/test_budgets.py -q` → PASS (albo napraw według wskazówki wyżej)

- [ ] **Step 3: OG image**

`build_pages.py` (albo osobna funkcja w `build_photos.py`) robi `assets/img/og.jpg`: 1200×630, JPEG q85, z hero strony głównej (`object-position` z `hero_focus`). Każda strona ma `og:image` = `base_url + "assets/img/og.jpg"`, `og:image:width` 1200 i `og:image:height` 630.

- [ ] **Step 4: Smoke e2e pod podścieżką `tools/e2e/smoke.mjs`**

Serwer: `py -m http.server 8081` uruchomiony w `B:\GITHUB`, baza `http://localhost:8081/kacperlochfoto.github.io/`.

Dla każdej strony (`""`, `sport/`, `reportaz/`, `o-mnie/`, `kontakt/`, `nie-ma-takiej/` dla 404) i każdej szerokości 1440, 900, 390, 320:
- zero odpowiedzi ≥ 400 poza samym dokumentem 404, zero błędów konsoli,
- `document.documentElement.scrollWidth <= innerWidth`,
- wszystkie linki z `.nav` i `.topbar` prowadzą do stron z kodem 200,
- przy 390 i 320 klik w `.menu-btn` otwiera menu (`aria-expanded="true"`), klik w „Reportaż” przenosi na `reportaz/`,
- na 404 link do strony głównej prowadzi do `/kacperlochfoto.github.io/`.

Na końcu wypisuje `SMOKE OK`.

Run: `node tools/e2e/smoke.mjs` → `SMOKE OK`

- [ ] **Step 5: Lighthouse**

Run (serwer z kroku 4):

```
npx -y lighthouse@12 http://localhost:8081/kacperlochfoto.github.io/ --only-categories=performance --form-factor=mobile --screenEmulation.mobile --chrome-flags="--headless=new" --output=json --output-path=<scratch>/lh-home.json
```

To samo dla `sport/`.

Expected: `categories.performance.score ≥ 0.95`, LCP < 2000 ms, CLS < 0.02 na obu. Lokalny serwer nie kompresuje gzipem, więc wynik jest pesymistyczny. Jeśli wychodzi < 0.95, popraw przyczynę wskazaną w `audits` (np. rozmiar hero, preload) i powtórz.

- [ ] **Step 6: Pełna regresja**

Run:

```
py -m pytest -q
node --test tests/js/
node tools/e2e/lightbox.mjs
node tools/e2e/smoke.mjs
```

Expected: wszystko PASS, `LIGHTBOX OK`, `SMOKE OK`.

- [ ] **Step 7: Commit**

```bash
git add tests/test_budgets.py tools/e2e/smoke.mjs assets/img/og.jpg tools/build_pages.py index.html sport reportaz o-mnie kontakt 404.html assets
git commit -m "perf: budżety, OG, smoke pod podścieżką, Lighthouse ≥ 95"
```
