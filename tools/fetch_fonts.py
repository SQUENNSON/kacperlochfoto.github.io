"""Google Fonts -> assets/fonts/*.woff2 + blok @font-face w assets/css/style.css; TTF-y do tools/fonts-src/."""
import re
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = ROOT / "assets" / "fonts"
CSS_PATH = ROOT / "assets" / "css" / "style.css"
SRC_DIR = Path(__file__).resolve().parent / "fonts-src"

CSS_URL = ("https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@1"
           "&family=Schibsted+Grotesk:wght@400..700&display=swap")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
TTFS = {
    "InstrumentSerif-Italic.ttf":
        "https://github.com/google/fonts/raw/main/ofl/instrumentserif/InstrumentSerif-Italic.ttf",
    "InterTight[wght].ttf":
        "https://github.com/google/fonts/raw/main/ofl/intertight/InterTight%5Bwght%5D.ttf",
}
SLUGS = {"Instrument Serif": "instrument-serif-italic", "Schibsted Grotesk": "schibsted-grotesk"}
MARK_START, MARK_END = "/* fonts:start */", "/* fonts:end */"


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def build_font_face() -> str:
    css = get(CSS_URL).decode("utf-8")
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    blocks = []
    for m in re.finditer(r"/\*\s*([\w-]+)\s*\*/\s*@font-face\s*\{(.*?)\}", css, re.S):
        subset, body = m.group(1), m.group(2)
        if subset not in ("latin", "latin-ext"):
            continue
        family = re.search(r"font-family:\s*'([^']+)'", body).group(1)
        url = re.search(r"url\((https://[^)]+\.woff2)\)", body).group(1)
        rng = re.search(r"unicode-range:\s*([^;]+);", body).group(1).strip()
        name = f"{SLUGS[family]}-{subset}.woff2"
        (FONTS_DIR / name).write_bytes(get(url))
        if family == "Instrument Serif":
            style, weight = "italic", "400"
        else:
            style, weight = "normal", "400 700"
        blocks.append(
            f"/* {family} {subset} */\n@font-face {{\n"
            f"  font-family: \"{family}\";\n  font-style: {style};\n  font-weight: {weight};\n"
            f"  font-display: swap;\n"
            f"  src: url(\"../fonts/{name}\") format(\"woff2\");\n"
            f"  unicode-range: {rng};\n}}\n")
    if len(blocks) != 4:
        raise SystemExit(f"oczekiwano 4 blokow @font-face, jest {len(blocks)}")
    return "\n".join(blocks)


def write_css(block: str) -> None:
    CSS_PATH.parent.mkdir(parents=True, exist_ok=True)
    section = f"{MARK_START}\n{block}{MARK_END}\n"
    old = CSS_PATH.read_text(encoding="utf-8") if CSS_PATH.exists() else ""
    if MARK_START in old:
        pre, rest = old.split(MARK_START, 1)
        post = rest.split(MARK_END, 1)[1].lstrip("\n")
        new = pre + section + ("\n" + post if post else "")
    else:
        new = section + ("\n" + old if old else "")
    CSS_PATH.write_text(new, encoding="utf-8")


def fetch_ttfs() -> None:
    SRC_DIR.mkdir(exist_ok=True)
    for name, url in TTFS.items():
        data = get(url)
        if not data.startswith(b"\x00\x01\x00\x00"):
            raise SystemExit(f"{name}: to nie TTF (zla sciezka?)")
        (SRC_DIR / name).write_bytes(data)
        print(f"{name}: {len(data)} B")


if __name__ == "__main__":
    write_css(build_font_face())
    fetch_ttfs()
    for p in sorted(FONTS_DIR.glob("*.woff2")):
        print(f"{p.name}: {p.stat().st_size} B")
