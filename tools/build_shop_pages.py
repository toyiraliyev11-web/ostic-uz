"""Builds the search-engine pages of the ostic.uz shop (RU / UZ / EN) from the platform's live catalogue.

    dist/shop/<lang>/<section>.html     one page per section: led, tica (fan coils), chillers, simon, interra
    dist/shop/<lang>/p/<slug>.html      one page per product (name, article, brand, photo, showroom price where
                                        the platform publishes one, stock, schema.org Product)
    dist/shop/sitemap.xml               every page above, with hreflang

The shop itself (dist/shop/index.html) stays the interactive page; these are plain HTML a crawler reads without
running scripts. Each product page refreshes its price and stock from the platform when a visitor opens it.

Run from the repo root:  python tools/build_shop_pages.py   (then repack zz-shop.zip)
Nothing here ever shows a cost or an agent price: the platform does not send them.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_brand_pages as B  # noqa: E402

API = "https://cloud.osticlinks.uz/api/v1/public"
DIST, SITE, LANGS, esc = B.DIST, B.SITE, B.LANGS, B.esc
OUT = DIST / "shop"
TODAY = __import__("datetime").date.today().isoformat()
TEL = "+998880669722"

SECTIONS = ["led", "tica", "chillers", "simon", "interra"]
T = {
    "ru": {
        "shop": "Магазин", "home": "OSTIC", "sum": "сум", "priceNote": "цена шоурума с НДС", "onRequest": "Цена по запросу",
        "inStock": "В наличии", "stockN": "На складе {n} {u}", "onOrder": "Под заказ", "add": "Добавить в корзину",
        "call": "Позвонить", "brand": "Бренд", "series": "Серия", "category": "Категория", "code": "Артикул", "unit": "Единица",
        "related": "Ещё в этой серии", "all": "Все товары", "count": "{n} товаров", "units": {"dona": "шт", "pcs": "шт"},
        "pTitle": "{name} — купить в Ташкенте | OSTIC", "pDescPrice": "{brand} {name}, артикул {code}. Цена шоурума {price} сум с НДС. Наличие: {stock}. Склад OSTIC в Ташкенте, доставка по Узбекистану.",
        "pDesc": "{brand} {name}, артикул {code}. Наличие: {stock}. Склад OSTIC в Ташкенте, цена и доставка по запросу.",
        "order": "Как заказать", "orderText": "Добавьте товар в корзину и отправьте заказ: менеджер OSTIC перезвонит, подтвердит цену, сроки и доставку. Или позвоните нам.",
        "sec": {
            "led": ("LED-освещение OSRAM / LEDVANCE в Ташкенте: лампы, даунлайты, панели", "LED-освещение", "Светодиодные лампы, даунлайты, панели 600×600, линейные и промышленные светильники OSRAM / LEDVANCE и Simon со склада в Ташкенте. Цены шоурума с НДС."),
            "tica": ("Фанкойлы TICA в Ташкенте: кассетные и напольно-потолочные, цена", "Фанкойлы TICA", "Кассетные и напольно-потолочные фанкойлы TICA, панели, пульты и контроллеры со склада OSTIC в Ташкенте. Цены шоурума с НДС."),
            "chillers": ("Чиллеры TICA в Ташкенте: винтовые, модульные, центробежные", "Чиллеры TICA", "Винтовые, модульные и центробежные чиллеры TICA для объектов в Узбекистане. Подбор под тепловую нагрузку, поставка под заказ, цена по запросу."),
            "simon": ("Розетки и выключатели Simon в Ташкенте: серии и наличие", "Simon", "Розетки, выключатели, рамки и электроустановочные изделия Simon со склада OSTIC в Ташкенте."),
            "interra": ("KNX Interra в Ташкенте: актуаторы, панели, модули", "Interra KNX", "Оборудование KNX Interra для умного здания: актуаторы, интерфейсы, панели управления. Склад OSTIC в Ташкенте."),
        },
        "chillerLead": "Чиллеры не держим на складе: подбираем модель под тепловую нагрузку объекта и привозим под заказ. Пришлите задачу или спецификацию.",
        "request": "Запросить подбор чиллера",
    },
    "uz": {
        "shop": "Do'kon", "home": "OSTIC", "sum": "so'm", "priceNote": "shourum narxi, QQS bilan", "onRequest": "Narxi so'rov bo'yicha",
        "inStock": "Omborda bor", "stockN": "Omborda {n} {u}", "onOrder": "Buyurtma asosida", "add": "Savatga qo'shish",
        "call": "Qo'ng'iroq qilish", "brand": "Brend", "series": "Seriya", "category": "Kategoriya", "code": "Artikul", "unit": "O'lchov",
        "related": "Shu seriyadan yana", "all": "Barcha mahsulotlar", "count": "{n} ta mahsulot", "units": {"dona": "dona", "pcs": "dona"},
        "pTitle": "{name} — Toshkentda sotib olish | OSTIC", "pDescPrice": "{brand} {name}, artikul {code}. Shourum narxi {price} so'm, QQS bilan. Mavjudligi: {stock}. Toshkentdagi OSTIC ombori, O'zbekiston bo'ylab yetkazib berish.",
        "pDesc": "{brand} {name}, artikul {code}. Mavjudligi: {stock}. Toshkentdagi OSTIC ombori, narx va yetkazib berish so'rov bo'yicha.",
        "order": "Qanday buyurtma qilinadi", "orderText": "Mahsulotni savatga qo'shib, buyurtmani yuboring: OSTIC menejeri qo'ng'iroq qilib, narx, muddat va yetkazib berishni tasdiqlaydi. Yoki bizga qo'ng'iroq qiling.",
        "sec": {
            "led": ("OSRAM / LEDVANCE LED yoritish Toshkentda: lampalar, downlightlar, panellar", "LED yoritish", "OSRAM / LEDVANCE va Simon LED lampalari, downlightlar, 600×600 panellar, chiziqli va sanoat chiroqlari Toshkentdagi ombordan. QQS bilan shourum narxlari."),
            "tica": ("TICA fankoyllari Toshkentda: kasseta va pol-shift, narxi", "TICA fankoyllari", "TICA kasseta va pol-shift fankoyllari, panellar, pultlar va kontrollerlar Toshkentdagi OSTIC omboridan. QQS bilan shourum narxlari."),
            "chillers": ("TICA chillerlari Toshkentda: vintli, modulli, markazdan qochma", "TICA chillerlari", "O'zbekistondagi obyektlar uchun TICA vintli, modulli va markazdan qochma chillerlari. Issiqlik yuklamasiga qarab tanlash, buyurtma asosida yetkazib berish, narxi so'rov bo'yicha."),
            "simon": ("Simon rozetka va viklyuchatellari Toshkentda", "Simon", "Simon rozetkalari, viklyuchatellari, ramkalari va elektr aksessuarlari Toshkentdagi OSTIC omboridan."),
            "interra": ("Interra KNX Toshkentda: aktuatorlar, panellar, modullar", "Interra KNX", "Aqlli bino uchun Interra KNX uskunalari: aktuatorlar, interfeyslar, boshqaruv panellari. Toshkentdagi OSTIC ombori."),
        },
        "chillerLead": "Chillerlarni omborda saqlamaymiz: obyektning issiqlik yuklamasiga qarab model tanlaymiz va buyurtma asosida olib kelamiz. Vazifa yoki spetsifikatsiyani yuboring.",
        "request": "Chiller tanlashni so'rash",
    },
    "en": {
        "shop": "Shop", "home": "OSTIC", "sum": "UZS", "priceNote": "showroom price, VAT included", "onRequest": "Price on request",
        "inStock": "In stock", "stockN": "{n} {u} in stock", "onOrder": "Made to order", "add": "Add to cart",
        "call": "Call", "brand": "Brand", "series": "Series", "category": "Category", "code": "Article", "unit": "Unit",
        "related": "More in this series", "all": "All products", "count": "{n} products", "units": {"dona": "pcs", "pcs": "pcs"},
        "pTitle": "{name} — buy in Tashkent | OSTIC", "pDescPrice": "{brand} {name}, article {code}. Showroom price {price} UZS incl. VAT. Availability: {stock}. OSTIC warehouse in Tashkent, delivery across Uzbekistan.",
        "pDesc": "{brand} {name}, article {code}. Availability: {stock}. OSTIC warehouse in Tashkent, price and delivery on request.",
        "order": "How to order", "orderText": "Add the product to the cart and send the order: an OSTIC manager calls back to confirm the price, lead time and delivery. Or call us.",
        "sec": {
            "led": ("OSRAM / LEDVANCE LED lighting in Tashkent: lamps, downlights, panels", "LED lighting", "OSRAM / LEDVANCE and Simon LED lamps, downlights, 600×600 panels, battens and high bays from stock in Tashkent. Showroom prices incl. VAT."),
            "tica": ("TICA fan coil units in Tashkent: cassette and floor-ceiling, prices", "TICA fan coils", "TICA cassette and floor-ceiling fan coil units, panels, remotes and controllers from the OSTIC warehouse in Tashkent. Showroom prices incl. VAT."),
            "chillers": ("TICA chillers in Tashkent: screw, modular, centrifugal", "TICA chillers", "TICA screw, modular and centrifugal chillers for projects in Uzbekistan. Selected for the cooling load, supplied to order, price on request."),
            "simon": ("Simon sockets and switches in Tashkent", "Simon", "Simon sockets, switches, frames and wiring accessories from the OSTIC warehouse in Tashkent."),
            "interra": ("Interra KNX in Tashkent: actuators, panels, modules", "Interra KNX", "Interra KNX equipment for smart buildings: actuators, interfaces and control panels. OSTIC warehouse in Tashkent."),
        },
        "chillerLead": "Chillers are not kept in stock: we select the model for the building's cooling load and bring it in to order. Send us the task or the specification.",
        "request": "Ask for a chiller selection",
    },
}
CHILLER_SERIES = ["TASFV", "TCA-XH / TCAV", "TASF / TASD", "TWSF / TWCF"]
CYR = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюяўқғҳ", "a b v g d e yo zh z i y k l m n o p r s t u f kh ts ch sh sch  y  e yu ya o q g h".split(" ")))

EXTRA_CSS = """
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:14px;margin:18px 0}
.pc{display:block;background:#fff;border:1px solid var(--line);border-radius:14px;overflow:hidden;text-decoration:none;color:inherit}
.pc img,.pc .ph{width:100%;aspect-ratio:1/1;object-fit:contain;background:#f3f1ec;display:block}
.pc .ph{display:grid;place-items:center;font:800 26px/1 Manrope,system-ui,sans-serif;color:rgba(15,34,51,.25)}
.pc div{padding:10px 12px 12px}.pc b{display:block;font-size:14px;line-height:1.35}.pc small{display:block;color:var(--mute);margin-top:4px}
.pc .pr{font-weight:800;margin-top:6px}.pc:hover b{text-decoration:underline}
.prod{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:28px;align-items:start}
.prod .pic{background:#f3f1ec;border-radius:16px;aspect-ratio:1/1;display:grid;place-items:center;overflow:hidden}
.prod .pic img{width:100%;height:100%;object-fit:contain}
.price{font:800 28px/1.2 Manrope,system-ui,sans-serif;margin:10px 0 2px}.price small{display:block;font:600 13px/1.4 Manrope,system-ui,sans-serif;color:var(--mute)}
.stock{font-weight:700;color:#1F7A4D}.stock.out{color:#8A5A00}
dl.facts{display:grid;grid-template-columns:auto 1fr;gap:6px 16px;margin:16px 0}dl.facts dt{color:var(--mute)}dl.facts dd{margin:0;font-weight:600}
.secnav{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 18px}.secnav a{border:1px solid var(--line);border-radius:999px;padding:6px 12px;text-decoration:none;font-weight:600;font-size:14px}
.secnav a[aria-current]{background:var(--navy);color:#fff;border-color:var(--navy)}
@media (max-width:720px){.prod{grid-template-columns:1fr}.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
"""


def fetch_catalog():
    req = urllib.request.Request(f"{API}/catalog.json", headers={"User-Agent": "ostic-site-build", "Origin": SITE})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def translit(s):
    return "".join(CYR.get(ch, ch) for ch in s.lower())


def slug_of(p):
    base = B.slugify(translit(p["name"]))[:70].strip("-") or "product"
    return f"{base}-{p['id'][:6]}"


def section_of(p):
    if (p.get("category") or "").strip().lower() == "led":
        return "led"
    return {"tica": "tica", "simon": "simon", "interra": "interra"}.get(p["brand"].lower(), p["brand"].lower())


def money(n, lang):
    return f"{n:,}".replace(",", " ") + " " + T[lang]["sum"]


def stock_text(p, lang):
    u = T[lang]
    if not p.get("in_stock"):
        return u["onOrder"]
    if p.get("qty"):
        return u["stockN"].format(n=f'{p["qty"]:,}'.replace(",", " "), u=u["units"].get((p["unit"] or "dona").lower(), p["unit"]))
    return u["inStock"]


def img_url(p, size):
    return f"{API}/products/{p['id']}/images/{p['images'][0]}?size={size}" if p["images"] else None


def page_head(lang, title, desc, path, alternates, jsonld, image=None):
    h = B.head(lang, title, desc, path, alternates, jsonld)
    if image:
        h = h.replace(f'<meta property="og:image" content="{SITE}/assets/og-cover.jpg">', f'<meta property="og:image" content="{esc(image)}">')
    return h.replace("</style>", EXTRA_CSS + "</style>", 1)


def secnav(lang, current):
    links = [f'<a href="/shop/?lang={lang}">{esc(T[lang]["all"])}</a>']
    for s in SECTIONS:
        cur = ' aria-current="page"' if s == current else ""
        links.append(f'<a href="/shop/{lang}/{s}.html"{cur}>{esc(T[lang]["sec"][s][1])}</a>')
    return f'<nav class="secnav" aria-label="{esc(T[lang]["shop"])}">{"".join(links)}</nav>'


def crumbs(lang, *parts):
    items = [f'<a href="{SITE}/?lang={lang}">OSTIC</a>', f'<a href="/shop/?lang={lang}">{esc(T[lang]["shop"])}</a>']
    items += [f'<a href="{href}">{esc(name)}</a>' if href else esc(name) for name, href in parts]
    return f'<p class="crumbs">{" › ".join(items)}</p>'


def card(p, lang):
    pic = f'<img src="{esc(img_url(p, "thumb"))}" alt="{esc(p["name"])}" width="320" height="320" loading="lazy" decoding="async">' if p["images"] else f'<span class="ph" aria-hidden="true">{esc(p["brand"][:2].upper())}</span>'
    price = money(p["price"], lang) if p.get("price") else T[lang]["onRequest"]
    return (f'<a class="pc" href="/shop/{lang}/p/{slug_of(p)}.html">{pic}<div><b>{esc(p["name"])}</b>'
            f'<small>{esc(p["brand"])}{", " + esc(p["series"]) if p.get("series") else ""}</small>'
            f'<span class="pr">{esc(price)}</span><small>{esc(stock_text(p, lang))}</small></div></a>')


LIVE_JS = """<script>
(function(){var id=document.body.getAttribute('data-id');if(!id||!window.fetch)return;
fetch('%s/catalog.json').then(function(r){return r.ok?r.json():null}).then(function(d){if(!d)return;
var p=(d.products||[]).filter(function(x){return x.id===id})[0];if(!p)return;
var pr=document.querySelector('[data-live=price]'),st=document.querySelector('[data-live=stock]');
if(pr&&p.price){pr.firstChild.textContent=Math.round(p.price).toLocaleString('ru-RU')+'\\u00a0'+pr.getAttribute('data-sum');}
if(st){st.textContent=!p.in_stock?st.getAttribute('data-out'):(p.qty?st.getAttribute('data-n').replace('{n}',p.qty.toLocaleString('ru-RU')):st.getAttribute('data-in'));st.className='stock'+(p.in_stock?'':' out');}
}).catch(function(){});})();
</script>""" % API


def product_page(p, lang, siblings):
    u = T[lang]
    sec = section_of(p)
    slug = slug_of(p)
    path = f"/shop/{lang}/p/{slug}.html"
    alternates = {l: f"/shop/{l}/p/{slug}.html" for l in LANGS}
    stock = stock_text(p, lang)
    code = p.get("code") or "—"
    desc = (u["pDescPrice"] if p.get("price") else u["pDesc"]).format(brand=p["brand"], name=p["name"], code=code, stock=stock,
                                                                    price=f'{p["price"]:,}'.replace(",", " ") if p.get("price") else "")
    named = p["name"] if p["brand"].lower() in p["name"].lower() else f'{p["brand"]} {p["name"]}'
    title = u["pTitle"].format(name=named)
    full = img_url(p, "full")
    product_ld = {"@type": "Product", "@id": f"{SITE}{path}#product", "name": p["name"], "url": f"{SITE}{path}",
                  "brand": {"@type": "Brand", "name": p["brand"]}, "description": desc}
    if p.get("code"):
        product_ld["sku"] = product_ld["mpn"] = p["code"]
    if p.get("category"):
        product_ld["category"] = p["category"]
    if full:
        product_ld["image"] = [full]
    if p.get("price"):
        product_ld["offers"] = {"@type": "Offer", "price": p["price"], "priceCurrency": "UZS", "url": f"{SITE}{path}",
                                "availability": "https://schema.org/InStock" if p.get("in_stock") else "https://schema.org/PreOrder",
                                "itemCondition": "https://schema.org/NewCondition",
                                "seller": {"@type": "Organization", "name": "OSTIC", "url": SITE}}
    jsonld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "OSTIC", "item": f"{SITE}/?lang={lang}"},
            {"@type": "ListItem", "position": 2, "name": u["shop"], "item": f"{SITE}/shop/?lang={lang}"},
            {"@type": "ListItem", "position": 3, "name": u["sec"][sec][1], "item": f"{SITE}/shop/{lang}/{sec}.html"},
            {"@type": "ListItem", "position": 4, "name": p["name"], "item": f"{SITE}{path}"}]},
        product_ld]}
    pic = f'<img src="{esc(full)}" alt="{esc(p["name"])}" width="800" height="800" decoding="async">' if full else f'<span class="ph" style="font:800 48px Manrope;color:rgba(15,34,51,.25)">{esc(p["brand"][:2].upper())}</span>'
    price_html = (f'<p class="price" data-live="price" data-sum="{esc(u["sum"])}">{esc(money(p["price"], lang))}<small>{esc(u["priceNote"])}</small></p>'
                  if p.get("price") else f'<p class="price">{esc(u["onRequest"])}</p>')
    unit_word = u["units"].get((p["unit"] or "dona").lower(), p["unit"])
    stock_html = (f'<p class="stock{"" if p.get("in_stock") else " out"}" data-live="stock" data-in="{esc(u["inStock"])}" '
                  f'data-out="{esc(u["onOrder"])}" data-n="{esc(u["stockN"].format(n="{n}", u=unit_word))}">{esc(stock)}</p>')
    facts = "".join(f"<dt>{esc(u[k])}</dt><dd>{esc(v)}</dd>" for k, v in
                    (("brand", p["brand"]), ("series", p.get("series")), ("category", p.get("category")), ("code", p.get("code")), ("unit", unit_word)) if v)
    rel = [s for s in siblings if s["id"] != p["id"]][:8]
    rel_html = f'<h2>{esc(u["related"])}</h2><div class="grid">{"".join(card(s, lang) for s in rel)}</div>' if rel else ""
    add = f"/shop/?lang={lang}&add={p['id']}"
    body = f"""<body data-id="{esc(p['id'])}">
<main><div class="wrap">
{crumbs(lang, (u["sec"][sec][1], f"/shop/{lang}/{sec}.html"), (p["name"], None))}
{secnav(lang, sec)}
<div class="prod"><div class="pic">{pic}</div><div>
<p class="k">{esc(p["brand"])}{" · " + esc(p["series"]) if p.get("series") else ""}</p><h1>{esc(p["name"])}</h1>
{price_html}{stock_html}
<div class="cta"><a class="btn primary" href="{add}" rel="nofollow">{esc(u["add"])}</a><a class="btn" href="tel:{TEL}">{esc(u["call"])}: {B.PHONES.split(" · ")[0]}</a></div>
<dl class="facts">{facts}</dl>
<h2>{esc(u["order"])}</h2><p>{esc(u["orderText"])}</p>
</div></div>
{rel_html}
</div></main>
{B.footer_html(lang)}
{LIVE_JS}
</body>
</html>
"""
    return path, alternates, page_head(lang, title, desc, path, alternates, jsonld, full) + body


def section_page(lang, sec, products, site_catalog):
    u = T[lang]
    title, h1, lead = u["sec"][sec]
    path = f"/shop/{lang}/{sec}.html"
    alternates = {l: f"/shop/{l}/{sec}.html" for l in LANGS}
    items_ld, chiller_html = [], ""
    if sec == "chillers":
        tica = next(b for b in site_catalog["catalog"] if b["brand"] == "TICA")
        blocks = []
        for i, it in enumerate([x for x in tica["items"] if x["series"] in CHILLER_SERIES], 1):
            img = f'/assets/catalog/{it["img"]}.jpg'
            items_ld.append({"@type": "ListItem", "position": i, "item": {
                "@type": "Product", "name": f'TICA {it["series"]} — {it["title"][lang]}', "brand": {"@type": "Brand", "name": "TICA"},
                "description": it["desc"][lang], "image": f"{SITE}{img}"}})
            blocks.append(f'<article class="series"><img src="{img}" alt="{esc("TICA " + it["series"])}" width="96" height="96" loading="lazy">'
                          f'<div><h3>{esc(it["title"][lang])}</h3><span class="meta">TICA · {esc(it["series"])} · {esc(it["meta"])}</span>'
                          f'<p>{esc(it["desc"][lang])}</p><p class="note">{esc(u["onOrder"])}, {esc(u["onRequest"].lower())}</p></div></article>')
        chiller_html = (f'<p>{esc(u["chillerLead"])}</p>{"".join(blocks)}'
                        f'<div class="cta"><a class="btn primary" href="{SITE}/?lang={lang}#contact">{esc(u["request"])}</a>'
                        f'<a class="btn" href="tel:{TEL}">{esc(u["call"])}: {B.PHONES.split(" · ")[0]}</a></div>')
    else:
        for i, p in enumerate(products, 1):
            items_ld.append({"@type": "ListItem", "position": i, "url": f'{SITE}/shop/{lang}/p/{slug_of(p)}.html', "name": p["name"]})
    jsonld = {"@context": "https://schema.org", "@graph": [
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "OSTIC", "item": f"{SITE}/?lang={lang}"},
            {"@type": "ListItem", "position": 2, "name": u["shop"], "item": f"{SITE}/shop/?lang={lang}"},
            {"@type": "ListItem", "position": 3, "name": h1, "item": f"{SITE}{path}"}]},
        {"@type": "CollectionPage", "url": f"{SITE}{path}", "name": title, "inLanguage": lang, "description": lead,
         "mainEntity": {"@type": "ItemList", "numberOfItems": len(items_ld), "itemListElement": items_ld}}]}
    grid = f'<p class="note">{esc(u["count"].format(n=len(products)))}</p><div class="grid">{"".join(card(p, lang) for p in products)}</div>' if products else ""
    body = f"""<body>
<main><div class="wrap">
{crumbs(lang, (h1, None))}
{secnav(lang, sec)}
<h1>{esc(h1)}</h1><p class="lead">{esc(lead)}</p>
{chiller_html}{grid}
</div></main>
{B.footer_html(lang)}
</body>
</html>
"""
    return path, alternates, page_head(lang, title + " | OSTIC", lead, path, alternates, jsonld) + body


def write_sitemap(pages):
    urls = []
    for path, alternates in pages:
        alts = "".join(f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{SITE}{p}"/>' for l, p in alternates.items())
        urls.append(f"  <url>\n    <loc>{SITE}{path}</loc>{alts}\n    <lastmod>{TODAY}</lastmod>\n  </url>")
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
                                     '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(urls) + "\n</urlset>\n", encoding="utf-8")


def main():
    catalog = fetch_catalog()
    site_catalog = B.load_data()
    products = sorted(catalog["products"], key=lambda p: (section_of(p), p.get("series") or "", p["name"]))
    # Inside a section: priced products first (OSRAM, TICA), then by brand, series and name.
    first = lambda p: (0 if p.get("price") else 1, p["brand"].lower(), p.get("series") or "", p["name"])  # noqa: E731
    by_section = {s: sorted((p for p in products if section_of(p) == s), key=first) for s in SECTIONS}
    by_series = {}
    for p in products:
        by_series.setdefault((section_of(p), p.get("series")), []).append(p)
    for lang in LANGS:
        for d in (OUT / lang / "p",):
            d.mkdir(parents=True, exist_ok=True)
            for old in d.glob("*.html"):
                old.unlink()  # a product that left the shop leaves no stale page behind
    pages = []
    for lang in LANGS:
        for sec in SECTIONS:
            path, alts, html = section_page(lang, sec, by_section[sec], site_catalog)
            (DIST / path.lstrip("/")).write_text(html, encoding="utf-8")
            if lang == "ru":
                pages.append((path, alts))
        for p in products:
            path, alts, html = product_page(p, lang, by_series[(section_of(p), p.get("series"))])
            (DIST / path.lstrip("/")).write_text(html, encoding="utf-8")
            if lang == "ru":
                pages.append((path, alts))
    for lang in ("uz", "en"):  # every language version gets its own <url> entry too
        pages += [(a[lang], a) for _, a in list(pages[: len(SECTIONS) + len(products)])]
    write_sitemap(pages)
    # The interactive shop links each card to its page: {product id: slug}.
    shop = OUT / "index.html"
    text = shop.read_text(encoding="utf-8")
    slugs = json.dumps({p["id"]: slug_of(p) for p in products}, separators=(",", ":"))
    text, n = re.subn(r'<script type="application/json" id="slugs">.*?</script>',
                      lambda _m: f'<script type="application/json" id="slugs">{slugs}</script>', text, flags=re.S)
    if n != 1:
        raise SystemExit("shop/index.html has no slugs block")
    shop.write_text(text, encoding="utf-8")
    print(f"{len(products)} products, {len(SECTIONS)} sections, {len(pages)} URLs in shop/sitemap.xml")


if __name__ == "__main__":
    main()
