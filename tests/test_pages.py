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
    assert [norm(a.find("b").text()) for a in links] == ["Sport", "Reportaż", "O mnie", "Kontakt"]
    current = [norm(a.find("b").text()) for a in links if a.attrs.get("aria-current") == "page"]
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
            "instrument-serif-italic-latin.woff2", "schibsted-grotesk-latin.woff2"], page.key
        assert all(f.get("type") == "font/woff2" and "crossorigin" in f for f in fonts), page.key
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
