import math
import re

import pytest
from PIL import Image, ImageChops, ImageCms, ImageOps

from build_photos import (EXCLUDE, SOURCES, Source, collect_sources, encode_photo,
                          slugify, variant_widths)

needs_sources = pytest.mark.skipif(not all(p.exists() for p in SOURCES.values()),
                                   reason="brak folderow ze zdjeciami")


def test_variant_widths():
    assert variant_widths(3072) == [800, 1600, 3072]
    assert variant_widths(2458) == [800, 1600, 2458]
    assert variant_widths(1440) == [800, 1440]
    assert variant_widths(700) == [700]


def test_slugify():
    assert slugify("sport", "DSC00109-2.jpg") == "sport-dsc00109-2"
    assert slugify("reportaz", "DSC03170-3.jpg") == "reportaz-dsc03170-3"
    assert slugify("sport", "2B9AE30E-EB7B-4CBC-9673-F3754CC0FA64.jpg") == "sport-2b9ae30e"
    assert slugify("sport", "IMG_3722.JPG") == "sport-img-3722"


def _make_jpeg(path):
    im = Image.effect_noise((3072, 2458), 40).convert("RGB")
    icc = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    exif = Image.Exif()
    exif[0x010F] = "TestCam"
    exif.get_ifd(0x8825)[1] = "N"  # GPS
    im.save(path, "JPEG", quality=90, icc_profile=icc, exif=exif.tobytes())


def test_encode_photo_synthetic(tmp_path, capsys):
    src_dir = tmp_path / "sport"
    src_dir.mkdir()
    jpg = src_dir / "TEST1.jpg"
    _make_jpeg(jpg)
    src = Source("sport", jpg, "sport-test1")
    repo = tmp_path / "repo"
    repo.mkdir()

    entry = encode_photo(src, repo)

    assert "TEST1.jpg" in capsys.readouterr().out  # ostrzezenie o GPS
    assert entry["slug"] == "sport-test1"
    assert entry["category"] == "sport"
    assert entry["source"] == "TEST1.jpg"
    assert (entry["w"], entry["h"]) == (3072, 2458)
    assert re.match(r"^#[0-9a-f]{6}$", entry["color"])
    assert [v["w"] for v in entry["variants"]] == [800, 1600, 3072]
    mtimes = {}
    for v in entry["variants"]:
        assert v["h"] == round(v["w"] * 2458 / 3072)
        ext = "jpg" if v["w"] == 3072 else "avif"
        assert v["file"] == f"assets/photos/sport-test1-{v['w']}.{ext}"
        f = repo / v["file"]
        assert v["bytes"] == f.stat().st_size
        with Image.open(f) as im:
            assert im.size == (v["w"], v["h"])
            if ext == "avif":
                assert "icc_profile" in im.info
                assert "exif" not in im.info
        mtimes[f] = f.stat().st_mtime_ns
    full = repo / entry["variants"][-1]["file"]
    assert full.read_bytes() == jpg.read_bytes()

    encode_photo(src, repo)
    assert {f: f.stat().st_mtime_ns for f in mtimes} == mtimes


@needs_sources
def test_collect_sources_counts():
    sources = collect_sources(SOURCES)
    assert sum(s.category == "sport" for s in sources) == 85
    assert sum(s.category == "reportaz" for s in sources) == 98
    assert len({s.slug for s in sources}) == len(sources)
    excluded = {(c, n.lower()) for c, n in EXCLUDE}
    for s in sources:
        assert (s.category, s.path.name.lower()) not in excluded
    cats = [s.category for s in sources]
    assert cats == sorted(cats, key=lambda c: c != "sport")


@needs_sources
@pytest.mark.slow
def test_psnr_quality(tmp_path):
    path = SOURCES["sport"] / "IMG_3723.JPG"
    with Image.open(path) as im:
        ref = ImageOps.exif_transpose(im).convert("RGB")
    entry = encode_photo(Source("sport", path, "sport-img-3723"), tmp_path)
    v = next(v for v in entry["variants"] if v["w"] == 1600)
    dec = Image.open(tmp_path / v["file"]).convert("RGB")
    small = ref.resize(dec.size, Image.LANCZOS)
    hist = ImageChops.difference(small, dec).histogram()
    sq = sum((i % 256) ** 2 * c for i, c in enumerate(hist))
    mse = sq / (small.width * small.height * 3)
    assert 10 * math.log10(255 ** 2 / mse) >= 34.5
