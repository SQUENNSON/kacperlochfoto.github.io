"""Zdjecia zrodlowe (JPEG) -> warianty AVIF + data/photos.json."""
import argparse
import json
import multiprocessing
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps

CATEGORIES = {"SPORT": "sport", "REPORTAŻ": "reportaz"}
EXCLUDE = {
    ("SPORT", "DSC01355.jpg"), ("SPORT", "DSC04110.jpg"), ("SPORT", "DSC07121.jpg"),
    ("REPORTAŻ", "DSC01355.jpg"), ("REPORTAŻ", "DSC03143.jpg"), ("REPORTAŻ", "DSC03835.jpg"),
    ("REPORTAŻ", "DSC03504.jpg"), ("REPORTAŻ", "DSC03639.jpg"),
}
QUALITY = 72
SPEED = 6
UUID_RE = re.compile(r"^[0-9A-F]{8}-[0-9A-F]{4}-", re.I)


@dataclass
class Source:
    category: str
    path: Path
    slug: str


def slugify(category_dir: str, filename: str) -> str:
    stem = Path(filename).stem
    if UUID_RE.match(stem):
        stem = stem[:8]
    return f"{CATEGORIES[category_dir]}-{stem.lower().replace('_', '-')}"


def variant_widths(width: int) -> list[int]:
    return [w for w in (800, 1600) if w < width] + [width]


def collect_sources(root: Path) -> list[Source]:
    excluded = {(d, n.lower()) for d, n in EXCLUDE}
    sources = []
    for dirname, category in CATEGORIES.items():
        files = [p for p in (root / dirname).iterdir()
                 if p.suffix.lower() in (".jpg", ".jpeg")
                 and (dirname, p.name.lower()) not in excluded]
        for p in sorted(files, key=lambda p: p.name.lower()):
            sources.append(Source(category, p, slugify(dirname, p.name)))
    return sources


def encode_image(im: Image.Image, target, icc: bytes | None) -> None:
    kwargs = {"icc_profile": icc} if icc else {}
    im.save(target, "AVIF", quality=QUALITY, speed=SPEED, **kwargs)


def encode_photo(src: Source, repo_root: Path) -> dict:
    out_dir = repo_root / "assets" / "photos"
    out_dir.mkdir(parents=True, exist_ok=True)
    src_mtime = src.path.stat().st_mtime
    with Image.open(src.path) as raw:
        icc = raw.info.get("icc_profile")
        im = ImageOps.exif_transpose(raw).convert("RGB")
    W, H = im.size
    r, g, b = im.resize((1, 1), Image.BOX).getpixel((0, 0))
    variants = []
    for w in variant_widths(W):
        h = round(w * H / W)
        rel = f"assets/photos/{src.slug}-{w}.avif"
        out = repo_root / rel
        if not (out.exists() and out.stat().st_mtime > src_mtime):
            resized = im if w == W else im.resize((w, h), Image.LANCZOS)
            encode_image(resized, out, icc)
        variants.append({"w": w, "h": h, "file": rel, "bytes": out.stat().st_size})
    return {"slug": src.slug, "category": src.category, "source": src.path.name,
            "w": W, "h": H, "color": f"#{r:02x}{g:02x}{b:02x}", "variants": variants}


def _work(args):
    src, repo_root = args
    try:
        return encode_photo(src, repo_root)
    except Exception as e:
        raise RuntimeError(f"{src.path}: {e}") from e


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=r"B:\NA STRONE")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    args = ap.parse_args(argv)
    repo = Path(args.repo).resolve()
    sources = collect_sources(Path(args.source))
    print(f"zdjec: {len(sources)}, procesow: {args.jobs}", flush=True)

    photos = []
    with multiprocessing.Pool(args.jobs) as pool:
        for i, entry in enumerate(pool.imap(_work, [(s, repo) for s in sources]), 1):
            photos.append(entry)
            print(f"[{i}/{len(sources)}] {entry['slug']}", flush=True)

    manifest = {"generated": datetime.now().replace(microsecond=0).isoformat(), "photos": photos}
    data_dir = repo / "data"
    data_dir.mkdir(exist_ok=True)
    (data_dir / "photos.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    keep = {Path(v["file"]).name for p in photos for v in p["variants"]}
    removed = 0
    for f in (repo / "assets" / "photos").glob("*.avif"):
        if f.name not in keep:
            f.unlink()
            removed += 1
    print(f"gotowe: {len(photos)} wpisow, usunieto {removed} nieaktualnych", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
