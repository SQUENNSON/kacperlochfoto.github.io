"""Logo SQphoto jako SVG (sciezki z fontow) + favicon.svg + apple-touch-icon.png."""
import sys
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
FONTS_SRC = Path(__file__).resolve().parent / "fonts-src"
IMG = ROOT / "assets" / "img"
SERIF_TTF = FONTS_SRC / "InstrumentSerif-Italic.ttf"
SANS_TTF = FONTS_SRC / "InterTight[wght].ttf"

BG, INK = "#f4f2ee", "#141413"
OVERLAP_EM = 0.05      # zakladka ogonka Q pod "p" (w em rozmiaru SQ)
TRACK_PHOTO = -0.02    # tracking "photo" (em)
SANS_WGHT = 660        # grubosc "photo" (dobrana wizualnie do 1.png)
SQ_XSCALE = 1.25       # "SQ" w 1.png jest szersze niz Instrument Serif (S: 66x81 px vs 0.60 proporcji fontu)
CAP_RATIO = 1.08       # wysokosc wersalikow SQ / wysokosc wydluzenia "h" (pomiar 1.png: 81/75)
PAD = 4                # margines viewBox


def _fmt(v: float) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".")


def glyph_path(font: TTFont, text: str, size: float, x: float, baseline: float,
               tracking_em: float = 0, xscale: float = 1.0) -> tuple[str, float]:
    """SVG path `d` dla tekstu (bez kerningu) oraz jego szerokosc w jednostkach SVG.

    xscale > 1 rozciaga glify w poziomie (szerokosc liczona razem z rozciagnieciem).
    """
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    upm = font["head"].unitsPerEm
    scale = size / upm
    pen = SVGPathPen(gs, ntos=_fmt)
    cx = x
    for ch in text:
        name = cmap[ord(ch)]
        tp = TransformPen(pen, (scale * xscale, 0, 0, -scale, cx, baseline))
        gs[name].draw(tp)
        cx += gs[name].width * scale * xscale + tracking_em * size
    return pen.getCommands(), cx - x


def _bounds(font: TTFont, text: str):
    """(xmin, ymin, ymax, advance) w jednostkach fontu, bez trackingu."""
    gs, cmap = font.getGlyphSet(), font.getBestCmap()
    xmin = ymin = ymax = None
    adv = 0
    for ch in text:
        bp = BoundsPen(gs)
        gs[cmap[ord(ch)]].draw(bp)
        if bp.bounds:
            x0, y0, x1, y1 = bp.bounds
            xmin = adv + x0 if xmin is None else min(xmin, adv + x0)
            ymin = y0 if ymin is None else min(ymin, y0)
            ymax = y1 if ymax is None else max(ymax, y1)
        adv += gs[cmap[ord(ch)]].width
    return xmin, ymin, ymax, adv


def _ink_right(font: TTFont, text: str) -> float:
    """Prawa krawedz tuszu ostatniego glifu, w jednostkach fontu od poczatku tekstu."""
    gs, cmap = font.getGlyphSet(), font.getBestCmap()
    adv = sum(gs[cmap[ord(c)]].width for c in text[:-1])
    bp = BoundsPen(gs)
    gs[cmap[ord(text[-1])]].draw(bp)
    return adv + bp.bounds[2]


def _o_xmax(font: TTFont) -> float:
    bp = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()["o"].draw(bp)
    return bp.bounds[2]


def load_fonts():
    serif = TTFont(SERIF_TTF)
    sans = instantiateVariableFont(TTFont(SANS_TTF), {"wght": SANS_WGHT})
    return serif, sans


def build_logo(serif: TTFont, sans: TTFont, sans_size: float = 100.0) -> str:
    # wysokosc wersalikow SQ == wysokosc wydluzenia "h"
    h_top = _bounds(sans, "h")[2] * sans_size / sans["head"].unitsPerEm
    s_top = _bounds(serif, "S")[2]
    serif_size = CAP_RATIO * h_top / s_top * serif["head"].unitsPerEm
    # lewa krawedz S i prawa krawedz Q (bez zakladki)
    sq_xmin, _, _, sq_adv = _bounds(serif, "SQ")
    k = serif_size / serif["head"].unitsPerEm
    ph_xmin = _bounds(sans, "p")[0] * sans_size / sans["head"].unitsPerEm

    baseline = 0.0
    x_sq = -sq_xmin * k * SQ_XSCALE
    sq_d, _ = glyph_path(serif, "SQ", serif_size, x_sq, baseline, xscale=SQ_XSCALE)
    q_ink_right = x_sq + _ink_right(serif, "SQ") * k * SQ_XSCALE
    x_ph = q_ink_right - OVERLAP_EM * serif_size - ph_xmin
    ph_d, ph_w = glyph_path(sans, "photo", sans_size, x_ph, baseline, TRACK_PHOTO)

    # prawa krawedz: ostatnie "o" bez bocznego marginesu i bez koncowego trackingu
    upm_s = sans["head"].unitsPerEm
    o_right_gap = (sans["hmtx"]["o"][0] - _o_xmax(sans)) * sans_size / upm_s
    right = x_ph + ph_w - TRACK_PHOTO * sans_size - o_right_gap
    top = -max(h_top, _bounds(serif, "SQ")[2] * k)
    bottom = max(-_bounds(serif, "SQ")[1] * k, -_bounds(sans, "photo")[1] * sans_size / sans["head"].unitsPerEm)
    x0, y0 = -PAD, top - PAD
    w, h = right + 2 * PAD, bottom - top + 2 * PAD
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{_fmt(x0)} {_fmt(y0)} {_fmt(w)} {_fmt(h)}" '
            f'role="img" fill="currentColor">\n<title>SQphoto</title>\n'
            f'<path d="{sq_d}"/>\n<path d="{ph_d}"/>\n</svg>\n')


def build_favicon(serif: TTFont) -> str:
    size = 100.0
    xmin, ymin, ymax, adv = _bounds(serif, "SQ")
    k = size / serif["head"].unitsPerEm
    box = 100.0
    target_w = box * 0.70
    scale = target_w / ((adv - xmin) * k)
    size *= scale
    k *= scale
    x = (box - (adv - xmin) * k) / 2 - xmin * k
    cap = ymax * k
    baseline = (box + cap) / 2 - 0
    d, _ = glyph_path(serif, "SQ", size, x, baseline)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">\n'
            f'<title>SQphoto</title>\n<rect width="100" height="100" fill="{BG}"/>\n'
            f'<path d="{d}" fill="{INK}"/>\n</svg>\n')


def build_touch_icon(path: Path) -> None:
    px = 180
    im = Image.new("RGB", (px, px), BG)
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(str(SERIF_TTF), 100)
    l, t, r, b = d.textbbox((0, 0), "SQ", font=f)
    f = ImageFont.truetype(str(SERIF_TTF), int(100 * (px * 0.70) / (r - l)))
    l, t, r, b = d.textbbox((0, 0), "SQ", font=f)
    d.text(((px - (r - l)) / 2 - l, (px - (b - t)) / 2 - t), "SQ", font=f, fill=INK)
    im.save(path)


def main() -> None:
    IMG.mkdir(parents=True, exist_ok=True)
    serif, sans = load_fonts()
    (IMG / "logo.svg").write_text(build_logo(serif, sans), encoding="utf-8")
    (IMG / "favicon.svg").write_text(build_favicon(serif), encoding="utf-8")
    build_touch_icon(IMG / "apple-touch-icon.png")
    print("ok")


if __name__ == "__main__":
    main()
