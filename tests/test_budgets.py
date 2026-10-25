"""Budzety: zdjecia w repo, JS/CSS po gzip, waga pierwszego ekranu strony glownej, kompletnosc manifestu."""
import gzip
import json
import sys
from pathlib import Path

MB = 1024**2


def _gz(path: Path) -> int:
    return len(gzip.compress(path.read_bytes(), 9))


def _pick(photo: dict, need: float) -> dict:
    """Wariant, ktory wybierze przegladarka: najmniejszy o szerokosci >= need, inaczej najwiekszy."""
    return next((v for v in photo["variants"] if v["w"] >= need), photo["variants"][-1])


def _home(repo_root):
    photos = {p["slug"]: p for p in json.loads((repo_root / "data/photos.json").read_text(encoding="utf-8"))["photos"]}
    home = json.loads((repo_root / "data/site.json").read_text(encoding="utf-8"))["pages"]["home"]
    return photos[home["hero"]], [photos[s] for s in home["rows"][0]]


def test_photo_budget(repo_root):
    total = sum(f.stat().st_size for f in (repo_root / "assets/photos").iterdir() if f.suffix in (".avif", ".jpg"))
    print(f"assets/photos: {total / MB:.1f} MB")
    assert total <= 300 * MB


def test_js_css_gzip(repo_root):
    js = sum(_gz(repo_root / "assets/js" / n) for n in ("main.js", "lightbox.js", "zoom-math.js"))
    css = _gz(repo_root / "assets/css/style.css")
    print(f"JS gzip {js} B, CSS gzip {css} B")
    assert js <= 15 * 1024
    assert css <= 20 * 1024


def test_home_first_screen_weight(repo_root):
    sys.stdout.reconfigure(encoding="utf-8")
    hero, row = _home(repo_root)
    # Archivo (menu) też: schowana nakładka menu jest układana, więc przeglądarka pobiera ją od razu (z Ż = latin-ext)
    fonts = ["schibsted-grotesk-latin.woff2", "instrument-serif-italic-latin.woff2",
             "archivo-expanded-latin.woff2", "archivo-expanded-latin-ext.woff2"]
    base = sum((repo_root / f).stat().st_size for f in ("index.html", "assets/css/style.css", "assets/js/main.js"))
    base += sum((repo_root / "assets/fonts" / f).stat().st_size for f in fonts)

    # profil Lighthouse mobile: 412 CSS px, DPR 1.75; hero i wiersz (kolumna) maja sizes 100vw
    need = 412 * 1.75
    mobile = base + _pick(hero, need)["bytes"] + sum(_pick(p, need)["bytes"] for p in row)
    # desktop Retina 1440 px, DPR 2: hero 73vw, wiersz 37vw (tylko informacyjnie — swiadoma decyzja)
    desktop = base + _pick(hero, 1440 * 0.73 * 2)["bytes"] + sum(_pick(p, 1440 * 0.37 * 2)["bytes"] for p in row)
    print(f"pierwszy ekran: mobile {mobile / MB:.2f} MB, desktop Retina {desktop / MB:.2f} MB (bez asercji)")
    assert mobile <= 1.5 * MB


def test_manifest_files_exist(repo_root):
    photos = json.loads((repo_root / "data/photos.json").read_text(encoding="utf-8"))["photos"]
    assert len(photos) == 200
    for photo in photos:
        for v in photo["variants"]:
            f = repo_root / v["file"]
            assert f.is_file(), v["file"]
            assert f.stat().st_size == v["bytes"], v["file"]
