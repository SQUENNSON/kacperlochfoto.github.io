# Rebuild portfolio SQphoto — projekt

Data: 2026-10-21 · Repo: `SQUENNSON/kacperlochfoto.github.io` (GitHub Pages, gałąź `main` = produkcja) · Praca na gałęzi `rebuild`

## Po co

Kacper Loch (SQphoto) to fotograf sportowy i reportażowy z okolic Nowego Sącza / Mszany Dolnej. Obecna strona ma „za dużo niepotrzebnych bajerów bez wyczucia”: canvas z cząsteczkami, własny kursor, loader, poświaty, karuzelę, przejścia na `transform`. Ma zostać przebudowana od zera.

Nowa strona ma wyglądać jak stare portfolio SQ photo (zrzuty ekranu poniżej), ale z mocno odświeżonym wyglądem. Ma być **prosta**, z **płynnymi animacjami**, **w pełni responsywna** i **szybka**. Zdjęcia są bohaterem, reszta tylko im nie przeszkadza.

Do czego służy (tak to rozumiem, użytkownik zaakceptował): klub albo organizator wydarzenia ogląda zdjęcia i od razu ma pod ręką telefon, mail i Instagram.

Punkt odniesienia, stare SQ photo (zrzuty: `C:\Users\lochk\Pictures\Screenshots\Zrzut ekranu 2026-10-21 123747.png` i `…123754.png`): biała strona, po lewej pasek z logo „Sq photo”, podpisem „KACPER LOCH” i menu SPORT / REPORTAŻ / O MNIE / KONTAKT, pod nim ikona Instagrama i ukośne linie w tle. Po prawej duże zdjęcia ciasno obok siebie, w dwóch kolumnach, bez podpisów.

## Cele

- Zdjęcia jako bohater: duże, ciasno obok siebie, bez podpisów.
- Płynne, spokojne animacje (lista niżej) i nic ponad nie.
- Responsywność: desktop, tablet, telefon. Żadnego poziomego scrolla.
- Szybkość jest **obowiązkowa** (budżety niżej).
- Brak widocznej straty jakości: pełny podgląd w natywnej rozdzielczości eksportu (3072 px), kolory bez przesunięć.

## Nie-cele

- Podstrony projektów. Obecne `projekt-*.html`, `realizacja-*.html`, `turniej-dobry-grajek.html` i `Projekt-turniej-żaków.html` **znikają**.
- Formularz kontaktowy, CMS, blog, filtry, wiele języków.
- Podpisy i opisy pod zdjęciami.

## Anty-cele (porażka, nawet jeśli „działa”)

- Wraca którykolwiek ze starych bajerów: cząsteczki, własny kursor, ekran ładowania, poświaty (glow), mocne gradienty, karuzela, napisy-podpowiedzi typu „DRAG”/„VIEW”.
- Animacje, które trzęsą stroną (np. `transform` na `body`), blokują przewijanie albo każą czekać na treść.
- Wolna strona, skoki układu przy ładowaniu zdjęć.
- Zdjęcia z widoczną kompresją, rozmyte na ekranach Retina albo z przesuniętymi kolorami.
- Przycięte kadry w galeriach. Zdjęcie pokazujemy w całości, wyjątkiem jest tylko duże zdjęcie na górze strony (hero).

## Ograniczenia

- **Hosting:** GitHub Pages, czyste pliki statyczne. Nie ma kroku build na serwerze. Skrypty (np. przygotowanie zdjęć) uruchamia się lokalnie, a ich wynik trafia do commita.
- **Źródło zdjęć:** `B:\NA STRONE\SPORT` (87 plików) i `B:\NA STRONE\REPORTAŻ` (102 pliki).
  - 180 plików ma 3072 px na dłuższym boku i profil sRGB IEC61966-2.1.
  - 9 plików (nazwy typu UUID, np. `2B9AE30E-….jpg`, oraz `FB6D52B0-….jpg`) ma 1440 × 1152 i nie ma profilu. Traktujemy je jako sRGB i niczego nie powiększamy.
  - Orientacja: 7 zdjęć jest pionowych, reszta pozioma. 161 plików ma proporcje 5:4, pozostałe 4:3, około 3:2 albo 4:5.
- **Wielkość repo:** `.git` ma już 804 MB, głównie przez historię zdjęć. Budżet na **wszystkie** nowe pliki graficzne łącznie to **około 300 MB**. Test na 4 zdjęciach: AVIF q72 dla trzech rozmiarów (800/1600/3072) to około 277 MB na 189 zdjęć. Jeśli budżet koliduje z jakością, wygrywa jakość. Historii repo nie przepisujemy. Stary folder `zdjecia/` (161 MB) wychodzi z drzewa plików.
- **Logo:** plik `1.png` z `B:\POBRANE\Black and White Minimalist Elegant Modern Typography  Creative Studio Brand Logo.zip` (500×500, czarne na białym). „SQ” to pochylony szeryf, „photo” to gruby grotesk. Drugi plik w zipie („lightlab.”) jest przykładem z szablonu i go ignorujemy.
- **Dane kontaktowe** (z obecnej strony): tel. 538 392 636, mail loch.kacper@gmail.com, Instagram `@sq_photo__` (https://www.instagram.com/sq_photo__/). Lokalizacja: „Nowy Sącz · Małopolska”.

## Decyzje użytkownika

1. **Układ jak w starym SQ photo:** stały pasek po lewej (logo + menu), po prawej duże zdjęcia ciasno obok siebie, bez zbędnych dodatków.
2. **Wygląd: wersja A „Papier”** z makiet (wybrana spośród A „Papier”, B „Noc”, C „Linie”). Parametry z makiety:
   - Kolory: tło `#f4f2ee`, tekst `#141413`, przygaszony `#8b877e`, linia oddzielająca pasek `rgba(20,20,19,.08)`.
   - Fonty: **Instrument Serif** (kursywa) + **Schibsted Grotesk** (400–700). To echo logo: kursywa szeryfowa jak „SQ”, grotesk jak „photo”.
   - Pasek (~27% szerokości na desktopie): logo, pod nim „KACPER LOCH” (grotesk 600, wersaliki, rozstrzelenie .24em). Dalej menu, a na dole Instagram. (2026-10-22, decyzja użytkownika: bez podtytułu „fotografia sportowa i reportaż” i bez lokalizacji na dole paska; lokalizacja zostaje na stronie Kontakt.)
   - Menu: numer `01–04` (mały, przygaszony) + nazwa wersalikami (grotesk 500, 15px, rozstrzelenie .16em). **Najechanie i aktywna strona:** czcionka się nie zmienia (2026-10-22, decyzja użytkownika: bez zamiany na kursywę). Pod nazwą wysuwa się od lewej cienka linia, a numer ciemnieje. Czas ~0.6 s, krzywa `cubic-bezier(.16,1,.3,1)`. Na telefonie menu w nakładce zostaje kursywą Instrument Serif 34px.
   - Tło: delikatny pionowy gradient papieru `#f7f5f1 → #f4f2ee → #ebe7df`, przypięty do okna (warstwa `body::before` z `position: fixed`).
   - Hero: szerokie zdjęcie u góry prawej kolumny (w makiecie proporcja 16:6.4).
   - Siatka: dwie kolumny, przerwa 6px.
   - Najechanie na zdjęcie: powolne powiększenie do ~1.035 w ~1.1 s, ta sama krzywa.
3. **Logo SQphoto** z `1.png`.
4. **Menu:** Sport, Reportaż, O mnie, Kontakt. Stare podstrony znikają.
5. **Wszystkie** zdjęcia z `B:\NA STRONE` trafiają na stronę, każde w swojej kategorii, z wyjątkiem duplikatów (pkt 9).
6. **Bez utraty jakości:** pełny podgląd w 3072 px, w siatce mniejsze wersje.
7. **Optymalizacja szybkości jest obowiązkowa.**
8. Zaakceptowane w podsumowaniu („wszystko jest”):
   - **Strona główna:** hero + wybór najlepszych kadrów z obu kategorii. **Zmiana 2026-10-22:** układ 1:1 jak stara strona główna (Adobe Portfolio): niski pas `sport-dsc05833` (4:1, na telefonie 5:4) i 20 rzędów po 2 zdjęcia w kolejności ze starej strony (`pages.home.rows` w `data/site.json`, pary ręcznie, bez `pair_rows`); wąsko w rzędzie, szeroko między rzędami.
   - **Sport / Reportaż:** pełne galerie.
   - **O mnie:** odświeżony tekst z obecnej strony.
   - **Kontakt:** telefon, mail, Instagram.
   - **Kliknięcie zdjęcia:** pełny ekran w 3072 px, strzałki, na telefonie przesunięcie palcem.
   - **Animacje:** płynne pojawianie się zdjęć przy przewijaniu, „przewijane” menu, powolne powiększenie po najechaniu, miękkie przejścia między stronami. Nic poza tym.
   - **Telefon:** lewy pasek zamienia się w górny pasek z logo i przyciskiem menu, siatka ma jedną kolumnę.
9. **Duplikaty:** z praktycznie identycznych kopii zostaje jedna. DSC01355 (drużyna w koszulkach „Awans”) jest tylko w Sporcie. Przy DSC03504 i DSC03639 bierzemy wersje `-2`. Zdjęcia, które naprawdę się różnią, zostają w całości: `SPORT/DSC00109` i `-2` (pion/poziom), `REPORTAŻ/DSC03170`, `-2` i `-3` oraz `REPORTAŻ/DSC03784` i `-2`.
   - Pomijamy te pliki: `SPORT/DSC01355.jpg`, `SPORT/DSC04110.jpg`, `SPORT/DSC07121.jpg`, `REPORTAŻ/DSC01355.jpg`, `REPORTAŻ/DSC03143.jpg`, `REPORTAŻ/DSC03835.jpg`, `REPORTAŻ/DSC03504.jpg`, `REPORTAŻ/DSC03639.jpg`.
   - Wynik: **Sport 84, Reportaż 97, razem 181 zdjęć.** Od 2026-10-22 doszły 2 kadry ze starej strony głównej (`DSC07497` z meczu Cracovia–Motor, `DSC03703` z koncertu przy choince), skompresowane tak jak reszta eksportu (3072 px, JPEG q80 4:2:0, sRGB, bez EXIF): **Sport 85, Reportaż 98, razem 183.**
   - Przy identycznych kopiach zawsze zostaje wersja `-2`, żeby reguła była jedna (moja decyzja, kopie się nie różnią).
10. **Zoom w pełnym podglądzie zostaje**, tak jak na obecnej stronie:
    - komputer: kółko myszy przybliża, przeciąganie przesuwa przybliżone zdjęcie,
    - telefon: przybliżanie dwoma palcami i przesuwanie.

    Przy przybliżaniu dociąga się wersja 3072 px, jeśli nie była jeszcze załadowana. Przesunięcie palcem przełącza zdjęcia tylko wtedy, gdy zdjęcie nie jest przybliżone.

## Moje decyzje (do sprawdzenia przez użytkownika)

- **Stack:** czysty HTML/CSS/JS bez frameworków, jak obecnie. Galerie są w HTML-u od razu (generowane lokalnie skryptem), a nie składane w przeglądarce przez JS.
- **Logo jako SVG** (wektor odtworzony z `1.png`), żeby było ostre na każdym ekranie. PNG ma tylko ~400 px szerokości. SVG ma wyglądać jak `1.png`; jeśli fonty z biblioteki nie dadzą zgodności, trzeba je obrysować.
- **Siatka bez przycinania:** wiersze po 2 zdjęcia o równej wysokości, szerokość wynika z proporcji. Pionowe zdjęcia łączymy w pary z pionowymi. Na telefonie jedna kolumna z pełnym kadrem.
- **Fonty hostowane lokalnie** (woff2, podzbiór łaciński z polskimi znakami), bez Google Fonts w produkcji.
- **Budżety szybkości:**
  - Lighthouse (mobile) Performance ≥ 95, LCP < 2.0 s, CLS < 0.02.
  - JS ≤ 15 KB po gzip, CSS ≤ 20 KB po gzip.
  - Przy wejściu na stronę główną przed pierwszym przewinięciem ładuje się ≤ 1.5 MB.
- **Wybór na stronę główną:** od 2026-10-22 to 40 kadrów ze starej strony (rzędy w `pages.home.rows`). Rząd 1 prawe to `sport-dsc07497` (Cracovia, gest serca), rząd 5 lewe to `reportaz-dsc03703` (skrzypaczki przy choince).
- **Aktualizacja 2026-10-21 (decyzja użytkownika):** pełne zdjęcia kompresuje użytkownik. Eksport (JPEG sRGB, bez EXIF) leży w `B:\NA STRONE\sport compressed\bic-compressed` i `B:\NA STRONE\reportaz compressed\bic-compressed`: 189 plików, nazwy 1:1 z oryginałami, 7 plików ma 2918 px. Plik użytkownika trafia na pełny ekran **bez zmian**. AVIF (poniżej) dotyczy tylko mniejszych wersji do siatki (800/1600), robionych z tego eksportu.
- **Format:** AVIF dla wszystkich wersji, bez zapasowego JPEG-a. Obsługują go wszystkie przeglądarki od 2023 roku (Safari 16.4+). Jakość dobiera builder, zaczynając od q≈72. Przed przetworzeniem całości trzeba porównać wycinki 1:1 z oryginałem (twarze, tłum, ciemne partie) i nie może być widocznej różnicy. Profil sRGB zostaje zachowany.
- **Telefony w pełnym podglądzie:** wersja dopasowana do ekranu (`srcset`/`sizes`). 3072 px dostają duże ekrany i Retina, a każdy przy przybliżeniu (pkt 10).
- **Adres:** strona działa teraz pod `https://squennson.github.io/kacperlochfoto.github.io/`. Domena `kacperlochfoto.pl` nie jest podpięta (DNS wskazuje Cloudflare, plik `CNAME` usunięty 2026-04-12). Wszystkie linki i ścieżki są **względne**, żeby działały i pod podścieżką, i pod ewentualną domeną. Nie ruszamy `CNAME` ani ustawień domeny. Adresy w OG i canonical prowadzą do adresu github.io.

## Zostawione builderowi

- Struktura plików i adresów (np. `sport/`, `reportaz/`, `o-mnie/`, `kontakt/`) i skrypt przygotowania zdjęć.
- Formaty i rozmiary wersji zdjęć (AVIF/WebP/JPEG, progi `srcset`). Warunek: mieszczą się w budżetach, pełny podgląd ma natywną rozdzielczość źródła, kolory sRGB zostają zachowane.
- Technika ładowania: `loading="lazy"` poza pierwszym ekranem, wymiary zapisane w HTML-u (brak skoków układu), `fetchpriority="high"` dla hero, wcześniejsze dociąganie sąsiednich zdjęć w podglądzie.
- Implementacja podglądu pełnoekranowego: zamykanie (Esc, klik w tło, przycisk), klawiatura, gest przesunięcia, zoom (pkt 10, w budżecie JS), opcjonalnie licznik.
- Technika przejść między stronami. Pasek ma nie mrugać, np. View Transitions między dokumentami, z natychmiastową zmianą tam, gdzie przeglądarka tego nie wspiera.
- Wybór hero dla każdej strony i kolejność zdjęć w galeriach.
- Redakcja tekstu O mnie: tylko fakty z obecnej strony, nic nowego nie dopisujemy.
- `prefers-reduced-motion` wyłącza pojawianie się zdjęć, powiększenie i przejścia.
- Meta/OG, favicon z logo, strona 404, `alt` dla zdjęć.
- Wdrożenie: merge `rebuild` → `main` dopiero po akceptacji użytkownika.
