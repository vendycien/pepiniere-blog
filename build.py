#!/usr/bin/env python3
"""Génère le blog statique de La Pépinière des Élites.

Usage :  pip install markdown pyyaml
         python3 build.py            -> articles publiés seulement
         python3 build.py --drafts   -> inclut les brouillons (aperçu)

Résultat : dist/blog/  (à téléverser dans public_html/blog sur Namecheap)
           pepiniere-blog.zip (même contenu, zippé)
"""
import html, re, shutil, sys, zipfile
from datetime import date, datetime
from email.utils import format_datetime
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "articles"
ASSETS = ROOT / "assets"
OUT = ROOT / "dist" / "blog"
# Mode sous-domaine (GitHub Pages) : python3 build.py --subdomain
SUBDOMAIN = "--subdomain" in sys.argv
MAIN = "https://pepinieredeselites.org"
SITE = "https://blog.pepinieredeselites.org" if SUBDOMAIN else MAIN
BASE = "" if SUBDOMAIN else "/blog"
INCLUDE_DRAFTS = "--drafts" in sys.argv

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
        "août", "septembre", "octobre", "novembre", "décembre"]
RUBRIQUES = ["État et institutions", "Économie et ressources", "Capital humain",
             "Numérique et avenir", "Doctrine et méthode"]


def slugify(s):
    import unicodedata
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def date_fr(d):
    return f"{d.day}{'er' if d.day == 1 else ''} {MOIS[d.month - 1]} {d.year}"


def load():
    posts = []
    for f in sorted(SRC.glob("*.md")):
        raw = f.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
        meta, body = yaml.safe_load(m.group(1)), m.group(2)
        statut = str(meta.get("statut", "publié")).split("#")[0].strip()
        if statut == "brouillon" and not INCLUDE_DRAFTS:
            continue
        # le titre et le chapô sont rendus par le gabarit
        body = re.sub(r"^\s*# .*\n", "", body, count=1)
        body = re.sub(r"^\s*\*[^*\n].*\*\s*\n", "", body, count=1)
        d = meta["date"] if isinstance(meta["date"], date) else datetime.fromisoformat(str(meta["date"])).date()
        text = re.sub(r"<[^>]+>", "", body)
        posts.append({
            **meta,
            "date": d,
            "slug": f.stem[11:],
            "html": markdown.markdown(body, extensions=["extra", "sane_lists"]),
            "minutes": max(1, round(len(text.split()) / 200)),
            "brouillon": statut == "brouillon",
        })
    return sorted(posts, key=lambda p: p["date"], reverse=True)


def e(s):
    return html.escape(str(s), quote=True)


def layout(title, description, content, canonical, og_type="website"):
    M = MAIN if SUBDOMAIN else ""
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{SITE}{canonical}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{SITE}{canonical}">
<meta property="og:site_name" content="La Pépinière des Élites">
<meta name="twitter:card" content="summary">
<link rel="alternate" type="application/rss+xml" title="Le blog de la Pépinière" href="{BASE}/rss.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{BASE}/style.css">
</head>
<body>
<header class="top">
  <div class="wrap top-in">
    <a class="brand" href="{M}/">La Pépinière <span>des Élites</span></a>
    <nav>
      <a href="{BASE}/">Blog</a>
      <a href="{M}/podcasts">Podcast</a>
      <a href="{M}/#lettres">Lettres</a>
      <a class="cta" href="{M}/#candidature">Rejoindre le cercle</a>
    </nav>
  </div>
</header>
<main>
{content}
</main>
<section class="newsletter">
  <div class="wrap">
    <h2>Les Lettres de la Pépinière</h2>
    <p>Deux fois par mois, nos analyses et nos propositions pour le Congo de demain, directement dans votre boîte mail.</p>
    <a class="btn" href="{M}/#lettres">S'abonner gratuitement</a>
  </div>
</section>
<footer class="foot">
  <div class="wrap foot-in">
    <p><strong>La Pépinière des Élites</strong> · Penser le Congo de demain, aujourd'hui.</p>
    <p>
      <a href="{M}/">Accueil</a> · <a href="{M}/#vision">Vision</a> · <a href="{M}/#axes">12 axes</a> ·
      <a href="{M}/#faq">FAQ</a> · <a href="https://wa.me/243821143796">WhatsApp</a> ·
      <a href="mailto:contacts@pepinieredeselites.org">Contact</a> · <a href="{BASE}/rss.xml">RSS</a>
    </p>
  </div>
</footer>
</body>
</html>
"""


def card(p):
    return f"""<article class="card" data-rubrique="{e(slugify(p['rubrique']))}">
  <p class="meta"><span class="tag">{e(p['format'])}</span> {e(p['rubrique'])}</p>
  <h2><a href="{BASE}/{p['slug']}/">{e(p['titre'])}</a></h2>
  <p class="chapo">{e(p['chapo'])}</p>
  <p class="meta">{date_fr(p['date'])} · {p['minutes']} min de lecture{' · <strong>brouillon</strong>' if p['brouillon'] else ''}</p>
</article>"""


def index_page(posts):
    present = [r for r in RUBRIQUES if any(p["rubrique"] == r for p in posts)]
    filtres = "".join(f'<button data-f="{slugify(r)}">{e(r)}</button>' for r in present)
    cards = "\n".join(card(p) for p in posts) or "<p>Premiers articles très bientôt.</p>"
    content = f"""<section class="hero">
  <div class="wrap">
    <p class="kicker">Le blog</p>
    <h1>Penser le Congo de demain, aujourd'hui.</h1>
    <p>Analyses, tribunes et explications sur les 12 chantiers de la nation. Pour comprendre, concevoir et transmettre.</p>
  </div>
</section>
<section class="wrap">
  <div class="filters"><button class="on" data-f="">Tout</button>{filtres}</div>
  <div class="grid">
{cards}
  </div>
</section>
<script>
document.querySelectorAll('.filters button').forEach(b => b.addEventListener('click', () => {{
  document.querySelectorAll('.filters button').forEach(x => x.classList.toggle('on', x === b));
  document.querySelectorAll('.card').forEach(c => c.hidden = b.dataset.f && c.dataset.rubrique !== b.dataset.f);
}}));
</script>"""
    return layout("Le blog · La Pépinière des Élites",
                  "Analyses, tribunes et explications sur les 12 chantiers du Congo de demain.",
                  content, f"{BASE}/")


def article_page(p, posts):
    autres = [q for q in posts if q is not p][:2]
    suite = "".join(card(q) for q in autres)
    share = f"{SITE}{BASE}/{p['slug']}/"
    wa = "https://wa.me/?text=" + html.escape(f"{p['titre']} {share}").replace(" ", "%20")
    content = f"""<article class="post wrap-narrow">
  <p class="meta"><a href="{BASE}/">← Le blog</a> · <span class="tag">{e(p['format'])}</span> {e(p['rubrique'])}</p>
  <h1>{e(p['titre'])}</h1>
  <p class="lede">{e(p['chapo'])}</p>
  <p class="meta">{e(p.get('auteur') or '')}{' · ' if p.get('auteur') else ''}{date_fr(p['date'])} · {p['minutes']} min de lecture</p>
  <div class="body">
{p['html']}
  </div>
  <p class="share">Partager : <a href="{wa}">WhatsApp</a> ·
    <a href="https://www.linkedin.com/sharing/share-offsite/?url={share}">LinkedIn</a> ·
    <a href="https://www.facebook.com/sharer/sharer.php?u={share}">Facebook</a></p>
</article>
{f'<section class="wrap"><h2 class="more">À lire aussi</h2><div class="grid">{suite}</div></section>' if suite else ''}"""
    return layout(f"{p['titre']} · La Pépinière des Élites", p["chapo"], content,
                  f"{BASE}/{p['slug']}/", "article")


def rss(posts):
    items = "".join(f"""
  <item>
    <title>{e(p['titre'])}</title>
    <link>{SITE}{BASE}/{p['slug']}/</link>
    <guid>{SITE}{BASE}/{p['slug']}/</guid>
    <pubDate>{format_datetime(datetime(p['date'].year, p['date'].month, p['date'].day, 8))}</pubDate>
    <description>{e(p['chapo'])}</description>
  </item>""" for p in posts)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>Le blog de la Pépinière des Élites</title>
  <link>{SITE}{BASE}/</link>
  <description>Penser le Congo de demain, aujourd'hui.</description>
  <language>fr</language>{items}
</channel></rss>
"""


def sitemap(posts):
    urls = [f"{SITE}{BASE}/"] + [f"{SITE}{BASE}/{p['slug']}/" for p in posts]
    body = "".join(f"\n  <url><loc>{u}</loc></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}\n</urlset>\n'


def main():
    posts = load()
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    shutil.copy(ASSETS / "style.css", OUT / "style.css")
    (OUT / "index.html").write_text(index_page(posts), encoding="utf-8")
    for p in posts:
        d = OUT / p["slug"]
        d.mkdir()
        (d / "index.html").write_text(article_page(p, posts), encoding="utf-8")
    (OUT / "rss.xml").write_text(rss(posts), encoding="utf-8")
    (OUT / "sitemap-blog.xml").write_text(sitemap(posts), encoding="utf-8")
    if SUBDOMAIN:
        (OUT / "CNAME").write_text("blog.pepinieredeselites.org\n")
    z = ROOT / "pepiniere-blog.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in OUT.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(OUT.parent))
    print(f"{len(posts)} article(s) -> {OUT}  |  archive : {z}")


if __name__ == "__main__":
    main()
