import re
import xml.etree.ElementTree as ET

from PIL import Image

SVG = "{http://www.w3.org/2000/svg}"


def _viewbox(root):
    return [float(v) for v in root.attrib["viewBox"].replace(",", " ").split()]


def test_logo_svg(repo_root):
    root = ET.parse(repo_root / "assets/img/logo.svg").getroot()
    assert not list(root.iter(SVG + "text"))
    x, y, w, h = _viewbox(root)
    assert 3.2 <= w / h <= 4.2
    assert list(root.iter(SVG + "path"))
    assert 'fill="currentColor"' in (repo_root / "assets/img/logo.svg").read_text(encoding="utf-8")
    assert root.find(SVG + "title").text == "SQphoto"


def test_favicon_and_touch_icon(repo_root):
    root = ET.parse(repo_root / "assets/img/favicon.svg").getroot()
    x, y, w, h = _viewbox(root)
    assert w == h
    with Image.open(repo_root / "assets/img/apple-touch-icon.png") as im:
        assert im.size == (180, 180)


def test_glyph_path_returns_path_and_width():
    from fontTools.ttLib import TTFont
    from build_logo import glyph_path, FONTS_SRC

    font = TTFont(FONTS_SRC / "InstrumentSerif-Italic.ttf")
    d, width = glyph_path(font, "SQ", 100, 0, 100)
    assert d.startswith("M") and width > 0


def test_fonts_present(repo_root):
    names = ["instrument-serif-italic-latin", "instrument-serif-italic-latin-ext",
             "schibsted-grotesk-latin", "schibsted-grotesk-latin-ext",
             "archivo-expanded-latin", "archivo-expanded-latin-ext"]
    for n in names:
        assert (repo_root / f"assets/fonts/{n}.woff2").stat().st_size > 5 * 1024
    css = (repo_root / "assets/css/style.css").read_text(encoding="utf-8")
    assert css.count("@font-face") == 6
    assert css.count("unicode-range") == 6
    assert len(re.findall(r'src:\s*url\("\.\./fonts/[^"]+\.woff2"\)\s*format\("woff2"\)', css)) == 6
    fonts = css.split("/* fonts:end */", 1)[0]
    assert fonts.count("font-stretch: 125%;") == 2  # Archivo Expanded: tylko szeroka instancja
