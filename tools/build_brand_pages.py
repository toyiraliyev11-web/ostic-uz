"""Builds static, crawlable catalogue pages for ostic.uz.

Reads the catalogue data out of dist/index.html (via tools/dump_catalog.js) and the
brand descriptions out of the existing SEO pages, then writes:

    dist/catalog/<lang>/index.html          hub, one per language
    dist/catalog/<lang>/<brand>.html        brand page, 5 brands x 3 languages
    dist/sitemap.xml, dist/llms.txt         updated with the new pages
    brand links appended to about.html / o-kompanii.html / ostic-haqida.html

Run from the repo root:  python tools/build_brand_pages.py
No prices are written anywhere: the site quotes on request.
"""
import html
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
SITE = "https://ostic.uz"
TODAY = "2026-11-25"
LANGS = ["ru", "uz", "en"]
BRANDS = ["tica", "osram", "simon", "salto", "viking"]
SEO_PAGE = {"ru": "o-kompanii.html", "uz": "ostic-haqida.html", "en": "about.html"}
PHONES = "+998 88 066 97 22 · +998 98 007 88 24"

UI = {
    "ru": {
        "assortment": "Ассортимент", "articles": "Артикулы и модели", "colCode": "Артикул", "colModel": "Модель",
        "colPower": "Мощность", "colSpec": "Параметры", "order": "Как заказать", "allBrands": "Все бренды",
        "openCatalog": "Открыть каталог на сайте", "request": "Запросить коммерческое предложение",
        "price": "Цены указываются в коммерческом предложении под проект и объём.",
        "orderText": "Пришлите спецификацию или задачу — подберём оборудование, посчитаем и согласуем сроки поставки. Поставка со склада в Ташкенте и напрямую от производителя.",
        "catalogue": "Каталог", "title": "{b} в Ташкенте — {cat}: каталог и поставка | OSTIC",
        "h1": "{b} — {cat}: каталог OSTIC в Ташкенте", "hubTitle": "Каталог оборудования по брендам, Ташкент | OSTIC",
        "hubH1": "Каталог OSTIC: оборудование по брендам", "hubLead": "Пять направлений инженерных систем с единой точкой ответственности: климат, освещение, электрика, контроль доступа и пожаротушение.",
        "series": "серий", "contacts": "Контакты", "hours": "Пн–Сб 09:00–18:00, воскресенье — выходной",
        "address": "г. Ташкент, Алмазарский район, ул. Нурафшон, 51", "home": "OSTIC",
        "suffix": " Каталог серий, артикулы и поставка в Ташкенте.",
        "salto": "OSTIC — официальный партнёр SALTO в Республике Узбекистан, сертифицирован для платформ Salto (сертификат выдан 23.11.2026, срок — два года).",
    },
    "uz": {
        "assortment": "Assortiment", "articles": "Artikullar va modellar", "colCode": "Artikul", "colModel": "Model",
        "colPower": "Quvvat", "colSpec": "Parametrlar", "order": "Qanday buyurtma qilinadi", "allBrands": "Barcha brendlar",
        "openCatalog": "Katalogni saytda ochish", "request": "Tijoriy taklif so‘rash",
        "price": "Narxlar loyiha va hajmga qarab tijoriy taklifda ko‘rsatiladi.",
        "orderText": "Spetsifikatsiya yoki vazifani yuboring: uskunani tanlaymiz, hisoblaymiz va yetkazib berish muddatini kelishamiz. Toshkentdagi ombordan va to‘g‘ridan-to‘g‘ri ishlab chiqaruvchidan yetkazamiz.",
        "catalogue": "Katalog", "title": "{b} Toshkentda — {cat}: katalog va yetkazib berish | OSTIC",
        "h1": "{b} — {cat}: OSTIC katalogi, Toshkent", "hubTitle": "Brendlar bo‘yicha uskunalar katalogi, Toshkent | OSTIC",
        "hubH1": "OSTIC katalogi: brendlar bo‘yicha uskunalar", "hubLead": "Muhandislik tizimlarining besh yo‘nalishi, javobgarlik bitta nuqtada: iqlim, yoritish, elektrika, kirish nazorati va yong‘in o‘chirish.",
        "series": "seriya", "contacts": "Aloqa", "hours": "Du–Sha 09:00–18:00, yakshanba — dam olish kuni",
        "address": "Toshkent sh., Olmazor tumani, Nurafshon ko‘chasi, 51", "home": "OSTIC",
        "suffix": " Seriyalar katalogi, artikullar va Toshkentga yetkazib berish.",
        "salto": "OSTIC — SALTO ning O‘zbekiston Respublikasidagi rasmiy hamkori, Salto platformalari bo‘yicha sertifikatlangan (sertifikat 23.11.2026 da berilgan, muddati ikki yil).",
    },
    "en": {
        "assortment": "Product ranges", "articles": "Article numbers and models", "colCode": "Article", "colModel": "Model",
        "colPower": "Power", "colSpec": "Specs", "order": "How to order", "allBrands": "All brands",
        "openCatalog": "Open the catalogue on the site", "request": "Request a commercial proposal",
        "price": "Prices are given in a commercial proposal for the project and volume.",
        "orderText": "Send a specification or a brief: we select the equipment, price it and agree delivery times. Supply from the Tashkent warehouse and directly from the manufacturer.",
        "catalogue": "Catalogue", "title": "{b} in Tashkent — {cat}: catalogue and supply | OSTIC",
        "h1": "{b} — {cat}: OSTIC catalogue, Tashkent", "hubTitle": "Equipment catalogue by brand, Tashkent | OSTIC",
        "hubH1": "OSTIC catalogue: equipment by brand", "hubLead": "Five engineering-system lines with a single point of responsibility: climate, lighting, wiring devices, access control and fire protection.",
        "series": "ranges", "contacts": "Contacts", "hours": "Mon–Sat 09:00–18:00, Sunday closed",
        "address": "51 Nurafshon Street, Olmazor District, Tashkent, Uzbekistan", "home": "OSTIC",
        "suffix": " Product ranges, article numbers and supply in Tashkent.",
        "salto": "OSTIC is an official Salto partner in the Republic of Uzbekistan, certified for Salto platforms (certificate issued 23.11.2026, valid for two years).",
    },
}


def esc(s):
    return html.escape(str(s), quote=True)


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def load_data():
    out = subprocess.run(["node", str(ROOT / "tools" / "dump_catalog.js"), str(DIST / "index.html")],
                         check=True, capture_output=True, encoding="utf-8").stdout
    return json.loads(out)


def load_seo_blocks():
    """Brand blurb, category and dealer status as the owner already published them."""
    blocks = {}
    for lang, fname in SEO_PAGE.items():
        s = (DIST / fname).read_text(encoding="utf-8")
        blocks[lang] = {}
        for m in re.finditer(r'<div class="brand" id="([a-z]+)">(.*?)</div>', s, re.S):
            slug, body = m.group(1), m.group(2)
            if slug not in BRANDS:
                continue
            cat = re.search(r'<span class="cat">(.*?)</span>', body, re.S)
            name = re.search(r"<h3>(.*?)</h3>", body, re.S)
            desc = re.search(r"<p>(.*?)</p>", body, re.S)
            st = re.search(r'<p class="st">(.*?)</p>', body, re.S)
            blocks[lang][slug] = {
                "cat": strip_tags(cat.group(1)), "name": strip_tags(name.group(1)),
                "desc": strip_tags(desc.group(1)), "status": strip_tags(st.group(1)) if st else "",
            }
    return blocks


def base_css():
    s = (DIST / "about.html").read_text(encoding="utf-8")
    css = re.search(r"<style>(.*?)</style>", s, re.S).group(1)
    extra = """
.crumbs{font-size:14px;color:var(--mute);margin:0 0 18px}.crumbs a{color:var(--mute)}
.cta{display:flex;gap:12px;flex-wrap:wrap;margin:22px 0 0}
.btn{display:inline-block;padding:12px 20px;border-radius:999px;font:700 15px/1 Manrope,system-ui,sans-serif;text-decoration:none;border:1px solid var(--navy)}
.btn.primary{background:var(--navy);color:#fff}
.series{display:grid;grid-template-columns:96px 1fr;gap:6px 18px;padding:18px 0;border-bottom:1px solid var(--line)}
.series img{width:96px;height:96px;object-fit:contain;background:#fff;border:1px solid var(--line);border-radius:10px;grid-row:1 / span 2}
.series .meta{font:600 12px/1.4 Manrope,system-ui,sans-serif;color:var(--gold);letter-spacing:.06em}
.series p{margin:4px 0 0}.series .tbl{grid-column:1 / -1;overflow-x:auto}
.series table{font-size:14px;margin-top:6px}.series th{width:auto;font-size:13px}
.hub a.card{display:block;padding:16px 0;border-bottom:1px solid var(--line);text-decoration:none;color:inherit}
.hub a.card:hover h3{text-decoration:underline}
.langs a{margin-right:6px}
.sr{position:absolute;left:-9999px}
@media (max-width:560px){.series{grid-template-columns:72px 1fr}.series img{width:72px;height:72px}}
"""
    return css + extra


def footer_html(lang):
    u = UI[lang]
    return (f'<footer><div class="wrap">OSTIC · EIGHT DOORS · {esc(u["address"])} · {PHONES} · info@eightdoors.uz · '
            f'<a href="{SITE}/?lang={lang}">ostic.uz</a></div></footer>')


def head(lang, title, desc, path, alternates, jsonld):
    alts = "".join(f'<link rel="alternate" hreflang="{l}" href="{SITE}{p}">' for l, p in alternates.items())
    alts += f'<link rel="alternate" hreflang="x-default" href="{SITE}{alternates["ru"]}">'
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{SITE}{path}">
{alts}
<meta property="og:type" content="website"><meta property="og:site_name" content="OSTIC">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{SITE}{path}"><meta property="og:image" content="{SITE}/assets/og-cover.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>{base_css()}</style>
<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False, indent=1)}</script>
</head>
"""


def nav_html(lang, current_slug, blocks):
    links = "".join(
        f'<a href="/catalog/{lang}/{s}.html"{" aria-current=\"page\"" if s == current_slug else ""}>{esc(blocks[lang][s]["name"])}</a>'
        for s in BRANDS)
    sw = " · ".join(
        (f"<strong>{l.upper()}</strong>" if l == lang else
         f'<a href="/catalog/{l}/{current_slug + ".html" if current_slug else ""}" hreflang="{l}">{l.upper()}</a>')
        for l in LANGS)
    return (f'<header><div class="wrap"><a class="logo" href="{SITE}/?lang={lang}">OSTIC<span>Engineering Solutions</span></a>'
            f'<nav>{links}<span class="langs">{sw}</span></nav></div></header>')


def article_table(lang, fams):
    u = UI[lang]
    pick = lambda v: v[lang] if isinstance(v, dict) else v
    rows = []
    for f in fams:
        rows.append(f'<tr><th colspan="4">{esc(pick(f["fam"]))} — {esc(pick(f["note"]))}</th></tr>')
        for code, model, watts, spec in f["rows"]:
            rows.append(f"<tr><td>{esc(code)}</td><td>{esc(model)}</td><td>{esc(watts)} W</td><td>{esc(pick(spec))}</td></tr>")
    head_row = (f'<tr><th>{u["colCode"]}</th><th>{u["colModel"]}</th><th>{u["colPower"]}</th><th>{u["colSpec"]}</th></tr>')
    return f'<div class="tbl"><table><caption class="sr">{u["articles"]}</caption>{head_row}{"".join(rows)}</table></div>'


def brand_page(lang, slug, data, blocks):
    u = UI[lang]
    b = next(x for x in data["catalog"] if x["slug"] == slug)
    blk = blocks[lang][slug]
    name, cat = blk["name"], blk["cat"]
    desc_plain = blk["desc"]
    status = blk["status"] or (u["salto"] if slug == "salto" else "")
    path = f"/catalog/{lang}/{slug}.html"
    alternates = {l: f"/catalog/{l}/{slug}.html" for l in LANGS}
    meta_desc = (desc_plain[:158].rsplit(" ", 1)[0] + "…" if len(desc_plain) > 160 else desc_plain) + u["suffix"]
    title = u["title"].format(b=name, cat=cat)
    arts = data["articles"] if slug == "osram" else {}
    items_ld, series_html = [], []
    for i, it in enumerate(b["items"], 1):
        sid = "s-" + slugify(it["series"])
        t, d = it["title"][lang], it["desc"][lang]
        img = f'/assets/catalog/{it["img"]}.jpg'
        items_ld.append({"@type": "ListItem", "position": i, "name": f'{it["series"]} — {t}', "description": d,
                         "url": f"{SITE}{path}#{sid}", "image": f"{SITE}{img}"})
        table = article_table(lang, arts[it["series"]]) if it["series"] in arts else ""
        series_html.append(
            f'<article class="series" id="{sid}"><img src="{img}" alt="{esc(name + " " + it["series"] + " — " + t)}" '
            f'width="96" height="96" loading="lazy" decoding="async">'
            f'<div><h3>{esc(t)}</h3><span class="meta">{esc(name)} · {esc(it["series"])} · {esc(it["meta"])}</span><p>{esc(d)}</p></div>{table}</article>')
    jsonld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "OSTIC", "item": f"{SITE}/?lang={lang}"},
                {"@type": "ListItem", "position": 2, "name": u["catalogue"], "item": f"{SITE}/catalog/{lang}/"},
                {"@type": "ListItem", "position": 3, "name": name, "item": f"{SITE}{path}"}]},
            {"@type": "CollectionPage", "@id": f"{SITE}{path}#page", "url": f"{SITE}{path}", "name": title,
             "inLanguage": lang, "description": meta_desc, "isPartOf": {"@id": f"{SITE}/#organization"},
             "about": {"@type": "Brand", "name": name},
             "mainEntity": {"@type": "ItemList", "numberOfItems": len(items_ld), "itemListElement": items_ld}},
        ],
    }
    open_url = f"{SITE}/?lang={lang}&brand={slug}#catalog"
    body = f"""<body>
{nav_html(lang, slug, blocks)}
<main><div class="wrap">
<p class="crumbs"><a href="{SITE}/?lang={lang}">OSTIC</a> › <a href="/catalog/{lang}/">{u["catalogue"]}</a> › {esc(name)}</p>
<p class="k">{esc(cat)}</p><h1>{esc(u["h1"].format(b=name, cat=cat))}</h1>
<p class="lead">{esc(desc_plain)}</p>{f'<p class="note">{esc(status)}</p>' if status else ''}
<div class="cta"><a class="btn primary" href="{open_url}">{u["openCatalog"]}</a><a class="btn" href="tel:+998880669722">{PHONES.split(" · ")[0]}</a></div>
<h2>{u["assortment"]}: {esc(name)} ({len(items_ld)} {u["series"]})</h2>
{"".join(series_html)}
<h2>{u["order"]}</h2><p>{u["orderText"]}</p><p class="note">{u["price"]}</p>
<div class="cta"><a class="btn primary" href="{open_url}">{u["request"]}</a><a class="btn" href="https://t.me/OSTIC_uz">Telegram @OSTIC_uz</a></div>
<h2>{u["contacts"]}</h2><p>{esc(u["address"])}<br>{PHONES}<br>info@eightdoors.uz<br>{u["hours"]}</p>
</div></main>
{footer_html(lang)}
</body>
</html>
"""
    return path, alternates, head(lang, title, meta_desc, path, alternates, jsonld) + body


def hub_page(lang, data, blocks):
    u = UI[lang]
    path = f"/catalog/{lang}/"
    alternates = {l: f"/catalog/{l}/" for l in LANGS}
    cards = []
    for s in BRANDS:
        b = next(x for x in data["catalog"] if x["slug"] == s)
        blk = blocks[lang][s]
        cards.append(f'<a class="card" href="/catalog/{lang}/{s}.html"><p class="k">{esc(blk["cat"])}</p>'
                     f'<h3>{esc(blk["name"])} — {len(b["items"])} {u["series"]}</h3><p>{esc(blk["desc"])}</p></a>')
    jsonld = {"@context": "https://schema.org", "@type": "CollectionPage", "@id": f"{SITE}{path}#page",
              "url": f"{SITE}{path}", "name": u["hubTitle"], "inLanguage": lang, "isPartOf": {"@id": f"{SITE}/#organization"},
              "mainEntity": {"@type": "ItemList", "itemListElement": [
                  {"@type": "ListItem", "position": i, "name": blocks[lang][s]["name"], "url": f"{SITE}/catalog/{lang}/{s}.html"}
                  for i, s in enumerate(BRANDS, 1)]}}
    body = f"""<body>
{nav_html(lang, "", blocks)}
<main><div class="wrap hub">
<p class="crumbs"><a href="{SITE}/?lang={lang}">OSTIC</a> › {u["catalogue"]}</p>
<h1>{esc(u["hubH1"])}</h1><p class="lead">{esc(u["hubLead"])}</p>
{"".join(cards)}
<p class="note">{u["price"]}</p>
</div></main>
{footer_html(lang)}
</body>
</html>
"""
    return path, head(lang, u["hubTitle"], u["hubLead"], path, alternates, jsonld) + body


def update_sitemap(pages):
    p = DIST / "sitemap.xml"
    s = p.read_text(encoding="utf-8")
    s = re.sub(r"\s*<url>\s*<loc>https://ostic\.uz/catalog/.*?</url>", "", s, flags=re.S)
    entries = []
    for path, alts, prio in pages:
        links = "".join(f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{SITE}{a}"/>' for l, a in alts.items())
        links += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}{alts["ru"]}"/>'
        entries.append(f"  <url>\n    <loc>{SITE}{path}</loc>{links}\n    <lastmod>{TODAY}</lastmod>\n    <priority>{prio}</priority>\n  </url>")
    s = s.replace("</urlset>", "\n".join(entries) + "\n</urlset>")
    p.write_text(s, encoding="utf-8")


def update_llms(blocks):
    p = DIST / "llms.txt"
    s = p.read_text(encoding="utf-8")
    s = re.sub(r"\n## Catalogue pages.*", "", s, flags=re.S).rstrip("\n")
    lines = ["", "", "## Catalogue pages (no prices: quoted per project)"]
    for lang, label in (("en", "English"), ("ru", "Русский"), ("uz", "O‘zbekcha")):
        lines.append(f"- [Catalogue hub ({label})]({SITE}/catalog/{lang}/)")
        for slug in BRANDS:
            lines.append(f"  - [{blocks[lang][slug]['name']} ({label})]({SITE}/catalog/{lang}/{slug}.html)")
    p.write_text(s + "\n".join(lines) + "\n", encoding="utf-8")


def link_from_seo_pages(blocks):
    label = {"ru": "Каталог {n} →", "uz": "{n} katalogi →", "en": "{n} catalogue →"}
    for lang, fname in SEO_PAGE.items():
        p = DIST / fname
        s = p.read_text(encoding="utf-8")
        s = re.sub(r'<p class="cat-link">.*?</p>', "", s)
        for slug in BRANDS:
            n = blocks[lang][slug]["name"]
            link = f'<p class="cat-link"><a href="/catalog/{lang}/{slug}.html">{esc(label[lang].format(n=n))}</a></p>'
            pat = re.compile(r'(<div class="brand" id="' + slug + r'">.*?)(</div>)', re.S)
            s = pat.sub(lambda m: m.group(1) + link + m.group(2), s, count=1)
        p.write_text(s, encoding="utf-8")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    data = load_data()
    blocks = load_seo_blocks()
    for lang in LANGS:
        missing = [s for s in BRANDS if s not in blocks[lang]]
        assert not missing, (lang, missing)
    sitemap_pages = []
    for lang in LANGS:
        out_dir = DIST / "catalog" / lang
        out_dir.mkdir(parents=True, exist_ok=True)
        path, page = hub_page(lang, data, blocks)
        (out_dir / "index.html").write_text(page, encoding="utf-8")
        sitemap_pages.append((path, {l: f"/catalog/{l}/" for l in LANGS}, "0.8"))
        for slug in BRANDS:
            path, alts, page = brand_page(lang, slug, data, blocks)
            (out_dir / f"{slug}.html").write_text(page, encoding="utf-8")
            sitemap_pages.append((path, alts, "0.8"))
    update_sitemap(sitemap_pages)
    update_llms(blocks)
    link_from_seo_pages(blocks)
    print("pages:", len(sitemap_pages))


if __name__ == "__main__":
    main()
