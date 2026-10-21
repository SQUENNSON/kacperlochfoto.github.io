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
    env.globals["logo"] = _logo(repo_root)

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
        html = env.get_template(page.template).render(site=site, page=page_ctx, p=p, nav_items=nav_items)
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
