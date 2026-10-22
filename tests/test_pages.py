import json
import re
import shutil
import subprocess
from html.parser import HTMLParser
from urllib.parse import unquote

import pytest

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
BASE_URL = "https://squennson.github.io/kacperlochfoto.github.io/"
EXTERNAL = re.compile(r"^(https?://|mailto:|tel:)")
BASE_SCRIPT = (
    "<script>document.write('<base href=\"'+(location.pathname.indexOf('/kacperlochfoto.github.io/')===0"
    "?'/kacperlochfoto.github.io/':'/')+'\">')</script>"
)
ABOUT_PARAGRAPHS = [
    "Fotograf z Mszany Dolnej. 19 lat, aparat w ręce od najmłodszych lat — i to nigdy nie przeszło.",
    "Fotografia to moja pasja od najmłodszych lat, a od niedawna również profesjonalne zajęcie. "
    "Specjalizuję się w fotografii sportowej, gdzie dynamika i emocje są kluczem do uchwycenia "
    "niezapomnianych chwil.",
    "W mojej dotychczasowej karierze miałem przyjemność tworzyć pełne reportaże meczowe dla klubów "
    "takich jak KS Turbacz (V liga) i MKS Limanovia (IV liga). Doświadczenie zbierałem również na "
    "sparingu drużyny z Ekstraklasy — Cracovii.",
    "Jednym z ciekawszych doświadczeń była obsługa fotograficzna charytatywnego meczu Ekipy Fantasy, "
    "w którym udział wzięły znane postacie ze świata internetu. Moje zdjęcia z tego wydarzenia można "
    "zobaczyć na profilach IG takich osób jak izak, Jakub Kiwior czy Tyszka, a także na oficjalnym "
    "koncie Ekipy Fantasy.",
    "Poza sportem uwieczniam także imprezy okolicznościowe — od pikników rodzinnych po rocznice ślubów, "
    "dbając o to, by każda fotografia opowiadała Waszą wyjątkową historię.",
]


class Node:
    def __init__(self, tag, attrs):
        self.tag, self.attrs, self.children = tag, attrs, []

    def iter(self):
        yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.iter()

    def find_all(self, tag, cls=None):
        return [n for n in self.iter() if n.tag == tag and (cls is None or cls in n.attrs.get("class", "").split())]

    def find(self, tag, cls=None):
        found = self.find_all(tag, cls)
        assert found, f"brak <{tag} class={cls}>"
        return found[0]

    def text(self):
        return "".join(c if isinstance(c, str) else c.text() for c in self.children)


class _TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {})
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, {k: (v or "") for k, v in attrs})
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, {k: (v or "") for k, v in attrs}))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def parse(path):
    builder = _TreeBuilder()
    builder.feed(path.read_text(encoding="utf-8"))
    return builder.root


def norm(text):
    return re.sub(r"\s+", " ", text.replace(" ", " ")).strip()


def pages():
    from build_pages import PAGES

    return PAGES


def meta(tree, name):
    for node in tree.find_all("meta"):
        if node.attrs.get("name") == name or node.attrs.get("property") == name:
            return node.attrs.get("content")
    return None


def test_prefix_for():
    from build_pages import prefix_for

    assert prefix_for("index.html") == ""
    assert prefix_for("sport/index.html") == "../"
    assert prefix_for("404.html") == ""


def test_internal_urls_are_relative(built):
    assert [p.key for p in pages()] == ["home", "sport", "reportaz", "o-mnie", "kontakt", "404"]
    for page in pages():
        html_path = built / page.out
        for node in parse(html_path).iter():
            urls = [node.attrs[a] for a in ("href", "src") if a in node.attrs]
            for attr in ("srcset", "imagesrcset", "data-srcset"):
                if attr in node.attrs:
                    urls += [part.split()[0] for part in node.attrs[attr].split(",") if part.strip()]
            for url in urls:
                where = f"{page.out}: <{node.tag}> {url!r}"
                if url.startswith(BASE_URL):
                    assert node.tag == "link" and node.attrs.get("rel") == "canonical", where
                    continue
                if EXTERNAL.match(url):
                    continue
                assert url, where
                assert not url.startswith("/"), where
                path = unquote(url.split("#")[0].split("?")[0])
                if not path:
                    assert url.startswith("#"), where
                    continue
                target = (html_path.parent / path).resolve()
                assert target.is_file() or (target / "index.html").is_file(), where


@pytest.mark.parametrize("key", ["home", "sport", "reportaz", "o-mnie", "kontakt", "404"])
def test_nav_active_and_numbers(built, key):
    page = next(p for p in pages() if p.key == key)
    tree = parse(built / page.out)
    nav = tree.find("nav", "nav")
    assert nav.attrs.get("id") == "nav"
    links = nav.find_all("a")
    assert [norm(a.find("span", "num").text()) for a in links] == ["01", "02", "03", "04"]
    assert [norm(a.find("span", "label").text()) for a in links] == ["Sport", "Reportaż", "O mnie", "Kontakt"]
    assert [norm(a.text()) for a in links] == ["01Sport", "02Reportaż", "03O mnie", "04Kontakt"]  # bez drugiej kopii etykiety
    current = [norm(a.find("span", "label").text()) for a in links if a.attrs.get("aria-current") == "page"]
    expected = {"sport": ["Sport"], "reportaz": ["Reportaż"], "o-mnie": ["O mnie"], "kontakt": ["Kontakt"]}
    assert current == expected.get(key, [])
    btn = tree.find("header", "topbar").find("button", "menu-btn")
    assert btn.attrs.get("aria-expanded") == "false" and btn.attrs.get("aria-controls") == "nav"
    assert tree.find("aside", "side").find("nav", "nav") is nav
    assert tree.find("main").attrs.get("id") == "main"


def test_contact_copy(built):
    main = parse(built / "kontakt/index.html").find("main")
    hrefs = {a.attrs.get("href") for a in main.find_all("a")}
    assert {"tel:+48538392636", "mailto:loch.kacper@gmail.com", "https://www.instagram.com/sq_photo__/"} <= hrefs
    text = norm(main.text())
    for copy in ("Porozmawiajmy", "538 392 636", "loch.kacper@gmail.com", "@sq_photo__", "Nowy Sącz · Małopolska"):
        assert copy in text
    assert norm(main.find("h1").text()) == "Porozmawiajmy"


def test_about_copy_has_only_existing_facts(built):
    tree = parse(built / "o-mnie/index.html")
    main = tree.find("main")
    paragraphs = [norm(p.text()) for p in main.find_all("p")]
    assert paragraphs == ABOUT_PARAGRAPHS
    text = norm(main.text())
    for fact in ("KS Turbacz", "MKS Limanovia", "Cracovii", "Ekipy Fantasy"):
        assert fact in text
    assert norm(tree.find("title").text())
    assert meta(tree, "description")


def test_meta_every_page(built, repo_root):
    site = json.loads((repo_root / "data/site.json").read_text(encoding="utf-8"))
    assert site["site"]["base_url"] == BASE_URL
    for page in pages():
        tree = parse(built / page.out)
        assert tree.find("html").attrs.get("lang") == "pl"
        title, desc = norm(tree.find("title").text()), meta(tree, "description")
        assert title and desc and len(desc) <= 155, page.key
        links = tree.find_all("link")
        fonts = [l.attrs for l in links if l.attrs.get("rel") == "preload" and l.attrs.get("as") == "font"]
        assert sorted(f["href"].rsplit("/", 1)[-1] for f in fonts) == [
            "archivo-expanded-latin.woff2", "instrument-serif-italic-latin.woff2", "schibsted-grotesk-latin.woff2"], page.key
        assert all(f.get("type") == "font/woff2" and "crossorigin" in f for f in fonts), page.key
        # czcionka menu tylko na desktopie (na telefonie menu jest schowane w nakładce)
        assert {f["href"].rsplit("/", 1)[-1]: f.get("media") for f in fonts}["archivo-expanded-latin.woff2"] == "(width > 900px)"
        assert any(l.attrs.get("rel") == "stylesheet" and l.attrs["href"].endswith("assets/css/style.css") for l in links)
        scripts = [s for s in tree.find_all("script") if s.attrs.get("src", "").endswith("assets/js/main.js")]
        assert len(scripts) == 1 and scripts[0].attrs.get("type") == "module"
        if page.key == "404":
            continue
        url = BASE_URL + page.out.removesuffix("index.html")
        canonical = [l.attrs["href"] for l in links if l.attrs.get("rel") == "canonical"]
        assert canonical == [url]
        assert meta(tree, "og:url") == url and meta(tree, "og:title") == title
        assert meta(tree, "og:description") == desc


def test_404_base(built):
    html = (built / "404.html").read_text(encoding="utf-8")
    head = parse(built / "404.html").find("head")
    first = next(c for c in head.children if isinstance(c, Node))
    assert first.tag == "script" and BASE_SCRIPT in html
    main = parse(built / "404.html").find("main")
    assert "Nie ma takiej strony." in norm(main.text())
    assert "./" in {a.attrs.get("href") for a in main.find_all("a")}
    node = shutil.which("node")
    if node is None:
        pytest.skip("brak node — wykonanie skryptu <base> pominięte")
    script = first.text()
    for pathname, base in (
        ("/kacperlochfoto.github.io/nie-ma/", "/kacperlochfoto.github.io/"),
        ("/kacperlochfoto.github.io/", "/kacperlochfoto.github.io/"),
        ("/nie-ma/", "/"),
    ):
        js = (
            f"let out='';const location={{pathname:{json.dumps(pathname)}}};"
            f"const document={{write:s=>{{out+=s}}}};{script};process.stdout.write(out)"
        )
        out = subprocess.run([node, "-e", js], capture_output=True, text=True, check=True).stdout
        assert out == f'<base href="{base}">'


def test_css_shell_rules(repo_root):
    css = (repo_root / "assets/css/style.css").read_text(encoding="utf-8")
    assert css.startswith("/* fonts:start */") and css.count("/* fonts:end */") == 1
    assert re.search(r"@view-transition\s*{\s*navigation:\s*auto;?\s*}", css)
    assert "view-transition-name: chrome" in css
    assert "prefers-reduced-motion: reduce" in css
    assert re.search(r"html\.menu-open\s*{[^}]*overflow:\s*hidden", css)
    for block in re.findall(r"(?:^|[},])\s*body\s*{([^}]*)}", css):
        assert "transform" not in block


def test_old_site_removed(repo_root):
    for name in ("o-mnie.html", "script.js", "lightbox.js", "style.css", "zdjecia",
                 "Projekt-turniej-żaków.html", "turniej-dobry-grajek.html"):
        assert not (repo_root / name).exists(), name
    leftovers = [p.name for p in repo_root.iterdir() if re.match(r"(?i)(projekt|realizacja)-.*\.html$", p.name)]
    assert leftovers == []
    assert (repo_root / ".nojekyll").is_file()


# ---------- galerie, hero, strona główna, reveal ----------

GRID_SIZES = "(max-width: 900px) 100vw, 37vw"
HERO_SIZES = "(max-width: 900px) 100vw, 73vw"
ALT = {"sport": "Sport — fotografia Kacpra Locha", "reportaz": "Reportaż — fotografia Kacpra Locha"}
PHOTO_PAGES = {"home": "index.html", "sport": "sport/index.html", "reportaz": "reportaz/index.html",
               "o-mnie": "o-mnie/index.html"}


def _ph(slug):
    """Sztuczne zdjęcie: nazwa zaczynająca się od 'V' = pionowe."""
    w, h = (2000, 3000) if slug.startswith("V") else (3000, 2000)
    return {"slug": slug, "w": w, "h": h}


def _slugs(rows):
    return [[p["slug"] for p in row] for row in rows]


def _check_invariants(photos, rows):
    flat = [p["slug"] for row in rows for p in row]
    assert sorted(flat) == sorted(p["slug"] for p in photos)  # każdy dokładnie raz
    assert all(len(row) == 2 for row in rows[:-1]) and 1 <= len(rows[-1]) <= 2  # sam może być tylko ostatni
    horizontal = [p["slug"] for p in photos if p["w"] >= p["h"]]
    assert [s for s in flat if s in horizontal] == horizontal  # kolejność poziomych zachowana


def test_pair_rows_pairs_verticals():
    from build_pages import pair_rows

    photos = [_ph(s) for s in ("H1", "V1", "H2", "H3", "V2", "H4")]
    rows = pair_rows(photos)
    assert _slugs(rows) == [["H1", "H2"], ["V1", "V2"], ["H3", "H4"]]
    _check_invariants(photos, rows)

    # pionowy wciąga najbliższy kolejny pionowy
    photos = [_ph(s) for s in ("V1", "H1", "H2", "H3", "H4", "H5", "H6", "H7", "V2", "H8")]
    rows = pair_rows(photos)
    assert _slugs(rows)[0] == ["V1", "V2"]
    _check_invariants(photos, rows)


def test_pair_rows_pairs_far_apart_verticals():
    """Pionowe łączą się z pionowymi bez względu na odległość (jak sport-dsc00109 i sport-dsc06738)."""
    from build_pages import pair_rows

    hs = [f"H{i}" for i in range(1, 41)]
    photos = [_ph(s) for s in ["V1", *hs[:30], "V2", *hs[30:], "V3", "H41", "V4"]]
    rows = pair_rows(photos)
    assert ["V1", "V2"] in _slugs(rows) and ["V3", "V4"] in _slugs(rows)
    assert all(not (r[0].startswith("V") ^ r[-1].startswith("V")) for r in _slugs(rows))
    _check_invariants(photos, rows)


def test_pair_rows_odd_tail():
    from build_pages import pair_rows

    photos = [_ph(f"H{i}") for i in range(1, 6)]
    assert _slugs(pair_rows(photos)) == [["H1", "H2"], ["H3", "H4"], ["H5"]]
    assert pair_rows([]) == []


def _manifest(repo_root):
    return json.loads((repo_root / "data/photos.json").read_text(encoding="utf-8"))["photos"]


def _site_pages(repo_root):
    return json.loads((repo_root / "data/site.json").read_text(encoding="utf-8"))["pages"]


def _lb_slugs(tree, out, manifest):
    """Slugi kolejnych [data-lb] w DOM (href = największy wariant) + kontrola znaczników dla lightboxa."""
    from build_pages import prefix_for, srcset

    p = prefix_for(out)
    by_href = {p + photo["variants"][-1]["file"]: photo for photo in manifest}
    slugs = []
    for a in (n for n in tree.iter() if "data-lb" in n.attrs):
        assert a.tag == "a" and "ph" in a.attrs.get("class", "").split(), out
        photo = by_href[a.attrs["href"]]
        assert a.attrs["data-srcset"] == srcset(photo, p)
        assert (a.attrs["data-w"], a.attrs["data-h"]) == (str(photo["w"]), str(photo["h"]))
        assert f"--c:{photo['color']}" in a.attrs.get("style", "").replace(" ", "")
        assert len(a.find_all("img")) == 1
        slugs.append(photo["slug"])
    return slugs


def test_galleries_complete(built):
    from build_pages import pair_rows

    manifest, site = _manifest(built), _site_pages(built)
    by_slug = {p["slug"]: p for p in manifest}
    for key, count in (("sport", 85), ("reportaz", 98)):
        out = PHOTO_PAGES[key]
        tree = parse(built / out)
        slugs = _lb_slugs(tree, out, manifest)
        category = [p for p in manifest if p["category"] == key]
        hero = site[key]["hero"]
        assert len(slugs) == count == len(category)
        assert slugs[0] == hero and "hero" in tree.find("a", "ph").attrs["class"].split()
        grid = [p for p in category if p["slug"] != hero]
        assert slugs[1:] == [p["slug"] for row in pair_rows(grid) for p in row]  # hero nie powtarza się
        rows = tree.find("main").find_all("div", "row")
        assert [len(r.find_all("a", "ph")) for r in rows] == [len(r) for r in pair_rows(grid)]
        assert all("data-reveal" in r.attrs for r in rows)

    tree = parse(built / "index.html")
    # strona główna = układ starej strony 1:1: pas u góry + rzędy z site.json w tej kolejności, bez pair_rows
    home = site["home"]
    picks = [s for row in home["rows"] for s in row]
    assert len(home["rows"]) == 20 and all(1 <= len(row) <= 2 for row in home["rows"])
    assert len(picks) == len(set(picks)) == 40
    assert home["hero"] in by_slug and all(s in by_slug for s in picks)
    slugs = _lb_slugs(tree, "index.html", manifest)
    assert slugs[0] == home["hero"] and home["hero"] not in picks
    assert slugs[1:] == picks
    assert "strip" in tree.find("a", "hero").attrs["class"].split()
    rows = tree.find("main").find("div", "rows")
    assert "spaced" in rows.attrs["class"].split()
    assert [len(r.find_all("a", "ph")) for r in rows.find_all("div", "row")] == [len(r) for r in home["rows"]]
    more = {a.attrs["href"]: norm(a.text()) for a in tree.find("main").find_all("a") if "data-lb" not in a.attrs}
    assert more["sport/"].startswith("Sport →") and "85" in more["sport/"]
    assert more["reportaz/"].startswith("Reportaż →") and "98" in more["reportaz/"]

    tree = parse(built / "o-mnie/index.html")
    assert _lb_slugs(tree, "o-mnie/index.html", manifest) == site["o-mnie"]["photos"]
    assert len(tree.find("main").find_all("div", "row")) == 1


def test_images_have_dimensions_and_lazy(built):
    from build_pages import prefix_for

    manifest = _manifest(built)
    for key, out in PHOTO_PAGES.items():
        p = prefix_for(out)
        files = {p + v["file"]: (photo, v) for photo in manifest for v in photo["variants"]}
        tree = parse(built / out)
        imgs = tree.find("main").find_all("img")
        assert imgs, out
        for img in imgs:
            photo, _ = files[img.attrs["src"]]
            assert img.attrs["width"] == str(photo["w"]) and img.attrs["height"] == str(photo["h"])
            assert img.attrs["alt"] == ALT[photo["category"]]
            candidates = [c.split() for c in img.attrs["srcset"].split(", ")]
            assert len(candidates) == len(photo["variants"])
            # srcset: tylko pliki z manifestu tego zdjęcia, z prawdziwymi szerokościami
            assert [(files[url][0]["slug"], f"{files[url][1]['w']}w") for url, _ in candidates] == [
                (photo["slug"], w) for _, w in candidates]
        heroes = tree.find_all("a", "hero")
        if key == "o-mnie":
            assert heroes == []
        else:
            assert len(heroes) == 1
            hero = heroes[0].find("img")
            assert hero.attrs.get("fetchpriority") == "high" and hero.attrs.get("loading") != "lazy"
            assert hero.attrs["sizes"] == HERO_SIZES
            preload = [l.attrs for l in tree.find("head").find_all("link") if l.attrs.get("as") == "image"]
            assert len(preload) == 1 and preload[0]["rel"] == "preload"
            assert preload[0]["imagesrcset"] == hero.attrs["srcset"] and preload[0]["imagesizes"] == HERO_SIZES
            assert preload[0].get("fetchpriority") == "high" and preload[0].get("type") == "image/avif"
        grid = [img for img in imgs if not heroes or img is not heroes[0].find("img")]
        assert grid, out
        # spec: loading="lazy" poza pierwszym ekranem; pierwszy wiersz pod hero jest na nim (1440×900 i 390×844)
        first_screen = tree.find("main").find("div", "row").find_all("img") if heroes else []
        for img in grid:
            eager = any(img is f for f in first_screen)
            assert img.attrs.get("loading") == (None if eager else "lazy"), out
            # pierwszy wiersz nie konkuruje z hero o pasmo (Lighthouse LCP)
            assert img.attrs.get("fetchpriority") == ("low" if eager else None), out
            assert img.attrs.get("decoding") == "async" and img.attrs["sizes"] == GRID_SIZES


def test_no_js_shows_content(repo_root):
    css = re.sub(r"/\*.*?\*/", "", (repo_root / "assets/css/style.css").read_text(encoding="utf-8"), flags=re.S)
    reveal = [(sel, body) for sel, body in re.findall(r"([^{}]+){([^{}]*)}", css) if "[data-reveal]" in sel]
    assert any(re.search(r"opacity:\s*0\s*(;|$)", body.strip()) for _, body in reveal)
    for sel, _ in reveal:
        for part in sel.split(","):
            if "[data-reveal]" in part:
                assert part.strip().startswith("html.js "), part  # bez klasy js nic nie jest ukryte
    for out in PHOTO_PAGES.values():
        for node in parse(repo_root / out).iter():
            style = node.attrs.get("style", "").replace(" ", "")
            assert "opacity:0" not in style and "display:none" not in style, out


def test_og_image(built, repo_root):
    from PIL import Image

    with Image.open(repo_root / "assets/img/og.jpg") as im:
        assert im.format == "JPEG" and im.size == (1200, 630)
    for page in pages():
        if page.key == "404":
            continue
        tree = parse(built / page.out)
        assert meta(tree, "og:image") == BASE_URL + "assets/img/og.jpg", page.key
        assert meta(tree, "og:image:width") == "1200" and meta(tree, "og:image:height") == "630", page.key
