"""Generuje statyczne strony HTML z szablonow Jinja2 (tools/templates) i data/site.json."""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markupsafe import Markup

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Page:
    key: str
    out: str
    template: str
    nav: str | None


PAGES: list[Page] = [
    Page("home", "index.html", "home.html.j2", None),
    Page("sport", "sport/index.html", "gallery.html.j2", "sport"),
    Page("reportaz", "reportaz/index.html", "gallery.html.j2", "reportaz"),
    Page("o-mnie", "o-mnie/index.html", "about.html.j2", "o-mnie"),
    Page("kontakt", "kontakt/index.html", "contact.html.j2", "kontakt"),
    Page("404", "404.html", "404.html.j2", None),
]

NAV = [("sport", "Sport"), ("reportaz", "Reportaż"), ("o-mnie", "O mnie"), ("kontakt", "Kontakt")]
NAV_OUT = {page.key: page.out for page in PAGES}

GRID_SIZES = "(max-width: 900px) 100vw, 37vw"
HERO_SIZES = "(max-width: 900px) 100vw, 73vw"


def _vertical(photo: dict) -> bool:
    return photo["h"] > photo["w"]


def pair_rows(photos: list[dict]) -> list[list[dict]]:
    """Wiersze po 2 zdjecia; pionowe laczy w pary z pionowymi, ostatnie nieparzyste zostaje samo.

    Wiersz od pionowego, a dalej poziomy: wciaga najblizszy pozniejszy pionowy (gdziekolwiek jest).
    Wiersz od poziomego, a dalej pionowy: bierze najblizszy poziomy, pionowy otwiera nastepny wiersz.
    """
    rest = list(photos)
    rows = []
    while rest:
        first = rest.pop(0)
        if not rest:
            rows.append([first])
            break
        pick = 0
        if _vertical(first) and not _vertical(rest[0]):
            pick = next((i for i, ph in enumerate(rest) if _vertical(ph)), 0)
        elif not _vertical(first) and _vertical(rest[0]):
            pick = next((i for i, ph in enumerate(rest) if not _vertical(ph)), 0)
        rows.append([first, rest.pop(pick)])
    return rows


def srcset(photo: dict, p: str) -> str:
    """Wszystkie warianty zdjecia z manifestu jako srcset (sciezki wzgledne od strony)."""
    return ", ".join(f"{p}{v['file']} {v['w']}w" for v in photo["variants"])


def _photos_word(n: int) -> str:
    if n == 1:
        return "zdjęcie"
    return "zdjęcia" if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14) else "zdjęć"


def _gallery_ctx(key: str, cfg: dict, photos: list[dict], p: str) -> dict:
    """Hero, wiersze i linki do galerii dla stron ze zdjeciami (wybor z data/site.json)."""
    by_slug = {ph["slug"]: ph for ph in photos}

    def get(slug: str) -> dict:
        if slug not in by_slug:
            raise KeyError(f"site.json pages.{key}: nie ma zdjecia {slug!r} w data/photos.json")
        return by_slug[slug]

    if key == "home":
        labels = dict(NAV)
        more = []
        for k in ("sport", "reportaz"):
            n = sum(ph["category"] == k for ph in photos)
            more.append({"href": p + _dir_url(NAV_OUT[k]), "label": labels[k], "count": n, "word": _photos_word(n)})
        return {"hero": get(cfg["hero"]), "rows": pair_rows([get(s) for s in cfg["picks"]]), "more": more}
    if key in ("sport", "reportaz"):
        hero = get(cfg["hero"])
        if hero["category"] != key:
            raise ValueError(f"site.json pages.{key}.hero {hero['slug']!r} jest z kategorii {hero['category']!r}")
        return {"hero": hero, "rows": pair_rows([ph for ph in photos if ph["category"] == key and ph is not hero])}
    if key == "o-mnie":
        return {"rows": [[get(s) for s in cfg["photos"]]]}
    return {}


def prefix_for(out: str) -> str:
    """Prefiks wzgledny od pliku `out` do korzenia strony."""
    return "../" * out.count("/")


def _dir_url(out: str) -> str:
    """'sport/index.html' -> 'sport/', 'index.html' -> '', '404.html' -> '404.html'."""
    return out.removesuffix("index.html")


def nbsp(text: str) -> str:
    """Polska typografia: jednoliterowe slowa i pauza nie zostaja same na koncu wiersza."""
    text = re.sub(r"(?<!\w)([aiouwzAIOUWZ]) ", "\\1\u00a0", text)
    return text.replace(" — ", "\u00a0— ")


def _logo(repo_root: Path) -> dict:
    svg = (repo_root / "assets/img/logo.svg").read_text(encoding="utf-8")
    viewbox = re.search(r'viewBox="([^"]+)"', svg).group(1)
    body = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1)
    body = re.sub(r"<title>.*?</title>", "", body, flags=re.S).strip()
    w, h = viewbox.split()[2:]
    # symbol ma oryginalny viewBox; <svg> z <use> dostaje "0 0 w h", zeby nie przesuwac go drugi raz
    return {"viewbox": viewbox, "use_viewbox": f"0 0 {w} {h}", "body": Markup(body), "ratio": float(w) / float(h)}


def render_all(repo_root: Path) -> list[Path]:
    data = json.loads((repo_root / "data/site.json").read_text(encoding="utf-8"))
    photos = json.loads((repo_root / "data/photos.json").read_text(encoding="utf-8"))["photos"]
    site = data["site"]
    env = Environment(
        loader=FileSystemLoader(repo_root / "tools" / "templates"),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        undefined=StrictUndefined,
    )
    env.filters["nbsp"] = nbsp
    env.globals.update(
        logo=_logo(repo_root),
        srcset=srcset,
        photo_alt=site["photo_alt"],
        GRID_SIZES=GRID_SIZES,
        HERO_SIZES=HERO_SIZES,
    )

    written = []
    for page in PAGES:
        p = prefix_for(page.out)
        nav_items = [
            {"key": key, "label": label, "href": p + _dir_url(NAV_OUT[key]), "num": f"{i:02d}"}
            for i, (key, label) in enumerate(NAV, start=1)
        ]
        page_ctx = {
            "key": page.key,
            "out": page.out,
            "nav": page.nav,
            "url": site["base_url"] + _dir_url(page.out),
            **data["pages"][page.key],
        }
        gallery = _gallery_ctx(page.key, data["pages"][page.key], photos, p)
        html = env.get_template(page.template).render(site=site, page=page_ctx, p=p, nav_items=nav_items, **gallery)
        target = repo_root / page.out
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8", newline="\n")
        written.append(target)
    return written


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    for path in render_all(ROOT):
        print(path.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
