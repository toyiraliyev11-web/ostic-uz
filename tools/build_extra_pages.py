"""Builds the downloads, projects and articles pages for ostic.uz (RU / UZ / EN).

    dist/downloads/<lang>/index.html     official documents and the OSTIC LED catalogue
    dist/projects/<lang>/index.html      project list (+ a page per project once
                                         tools/projects.json has its systems filled in)
    dist/articles/<lang>/index.html      article hub
    dist/articles/<lang>/<slug>.html     articles
    dist/sitemap.xml, dist/llms.txt      updated

Run from the repo root after build_brand_pages.py:  python tools/build_extra_pages.py
Facts in the articles come from the catalogue on the site and the 2026 LED catalogue
PDF. No prices anywhere.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_brand_pages as B  # noqa: E402

DIST, SITE, LANGS, TODAY = B.DIST, B.SITE, B.LANGS, B.TODAY
esc = B.esc

NAV = {
    "ru": [("catalog", "Каталог"), ("projects", "Проекты"), ("downloads", "Документы"), ("articles", "Статьи")],
    "uz": [("catalog", "Katalog"), ("projects", "Loyihalar"), ("downloads", "Hujjatlar"), ("articles", "Maqolalar")],
    "en": [("catalog", "Catalogue"), ("projects", "Projects"), ("downloads", "Documents"), ("articles", "Articles")],
}
COMMON = {
    "ru": {"request": "Отправить запрос", "calc": "Калькуляторы на сайте", "onRequest": "По запросу",
           "reqBim": "Нужны файлы Revit / BIM, IES или паспорта на конкретную модель? Отправьте запрос — пришлём то, что предоставляет производитель.",
           "source": "Источник: каталог OSTIC и каталог LED 2026 (OSRAM / LEDVANCE).", "read": "Читать"},
    "uz": {"request": "So‘rov yuborish", "calc": "Saytdagi kalkulyatorlar", "onRequest": "So‘rov bo‘yicha",
           "reqBim": "Aniq model uchun Revit / BIM, IES fayllari yoki pasport kerakmi? So‘rov yuboring — ishlab chiqaruvchi beradigan fayllarni yuboramiz.",
           "source": "Manba: OSTIC katalogi va LED katalog 2026 (OSRAM / LEDVANCE).", "read": "O‘qish"},
    "en": {"request": "Send a request", "calc": "Calculators on the site", "onRequest": "On request",
           "reqBim": "Need Revit / BIM, IES files or a datasheet for a specific model? Send a request and we will send what the manufacturer provides.",
           "source": "Source: the OSTIC catalogue and the 2026 LED catalogue (OSRAM / LEDVANCE).", "read": "Read"},
}


def nav(lang, section, path_for):
    links = "".join(
        f'<a href="/{key}/{lang}/"{" aria-current=\"page\"" if key == section else ""}>{esc(label)}</a>'
        for key, label in NAV[lang])
    sw = " · ".join(
        (f"<strong>{l.upper()}</strong>" if l == lang else f'<a href="{path_for(l)}" hreflang="{l}">{l.upper()}</a>')
        for l in LANGS)
    return (f'<header><div class="wrap"><a class="logo" href="{SITE}/?lang={lang}">OSTIC<span>Engineering Solutions</span></a>'
            f'<nav>{links}<span class="langs">{sw}</span></nav></div></header>')


def page(lang, section, path_tpl, title, desc, jsonld, inner):
    alternates = {l: path_tpl.format(lang=l) for l in LANGS}
    path = alternates[lang]
    body = (f"<body>\n{nav(lang, section, lambda l: alternates[l])}\n<main><div class=\"wrap\">\n{inner}\n</div></main>\n"
            f"{B.footer_html(lang)}\n</body>\n</html>\n")
    return path, alternates, B.head(lang, title, desc, path, alternates, jsonld) + body


def crumbs(lang, label):
    home = f'<a href="{SITE}/?lang={lang}">OSTIC</a>'
    return f'<p class="crumbs">{home} › {esc(label)}</p>'


def table(head, rows):
    h = "".join(f"<th>{esc(c)}</th>" for c in head)
    r = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in row) + "</tr>" for row in rows)
    return f'<div class="tbl"><table><tr>{h}</tr>{r}</table></div>'


# ------------------------------------------------------------------ downloads
DOCS = [
    # (brand, url, title per lang, kind)
    ("OSRAM / LEDVANCE", "/assets/catalog/OSTIC_LED_Katalog_OSRAM_2026_UZ.pdf",
     {"ru": "Каталог OSTIC LED 2026 (OSRAM / LEDVANCE), на узбекском", "uz": "OSTIC LED katalogi 2026 (OSRAM / LEDVANCE)", "en": "OSTIC LED catalogue 2026 (OSRAM / LEDVANCE), in Uzbek"}, "PDF · 2,4 MB"),
    ("OSRAM / LEDVANCE", "https://www.ledvance.com/00_Free_To_Use/asset-13369108_balkan_lum_catalogue_2026.pdf",
     {"ru": "Каталог светильников LEDVANCE 2026 (англ.)", "uz": "LEDVANCE yoritgichlar katalogi 2026 (ingl.)", "en": "LEDVANCE luminaires catalogue 2026"}, "PDF · ledvance.com"),
    ("OSRAM / LEDVANCE", "https://www.ledvance.com/00_Free_To_Use/asset-13198768_led_luminaires_assortment_professional_2024_03.pdf",
     {"ru": "Ассортимент профессиональных светильников LEDVANCE (англ.)", "uz": "LEDVANCE professional yoritgichlar assortimenti (ingl.)", "en": "LEDVANCE professional luminaires assortment"}, "PDF · ledvance.com"),
    ("SALTO", "https://cms.saltosystems.com/sites/default/files/downloads/datasheet-xs4-original-plus-ex6-eng-01-22.pdf",
     {"ru": "SALTO XS4 Original+ — технический паспорт (англ.)", "uz": "SALTO XS4 Original+ — texnik pasport (ingl.)", "en": "SALTO XS4 Original+ datasheet"}, "PDF · saltosystems.com"),
    ("VIKING", "https://www.vikinggroupinc.com/sites/default/files/migrated/070392_01.pdf",
     {"ru": "VIKING Model F-1 — сухой клапан, технические данные (англ.)", "uz": "VIKING Model F-1 — quruq klapan, texnik ma’lumot (ingl.)", "en": "VIKING Model F-1 dry valve, technical data"}, "PDF · vikinggroupinc.com"),
    ("VIKING", "https://www.vikinggroupinc.com/sites/default/files/2025-10/110524.pdf",
     {"ru": "VIKING VK850 — спринклер для чистых помещений (англ.)", "uz": "VIKING VK850 — toza xonalar uchun sprinkler (ingl.)", "en": "VIKING VK850 cleanroom sprinkler, technical data"}, "PDF · vikinggroupinc.com"),
    ("VIKING", "https://www.vikinggroupinc.com/sites/default/files/2025-03/042519.pdf",
     {"ru": "VIKING VK960 / VK962 — оконные спринклеры (англ.)", "uz": "VIKING VK960 / VK962 — deraza sprinklerlari (ingl.)", "en": "VIKING VK960 / VK962 window sprinklers, technical data"}, "PDF · vikinggroupinc.com"),
    ("TICA", "https://tica.ru/catalog/fankoyly/kanalnye-fankoyly/",
     {"ru": "TICA — канальные фанкойлы, каталог и документация (tica.ru)", "uz": "TICA — kanalli fankoyllar, katalog va hujjatlar (tica.ru, rus.)", "en": "TICA duct fan coils, catalogue and documents (tica.ru, Russian)"}, "tica.ru"),
]
DL = {
    "ru": {"title": "Документы и каталоги: OSRAM, SALTO, VIKING, TICA | OSTIC", "h1": "Документы для проектировщиков",
           "lead": "Каталоги и технические паспорта производителей, которых мы поставляем. Ссылки ведут на официальные файлы; цены в документах OSTIC не публикуются.",
           "doc": "Документ", "brand": "Бренд", "fmt": "Формат", "simon": "SIMON: каталоги серий M7, M3 и i7 — по запросу."},
    "uz": {"title": "Hujjatlar va kataloglar: OSRAM, SALTO, VIKING, TICA | OSTIC", "h1": "Loyihachilar uchun hujjatlar",
           "lead": "Biz yetkazib beradigan ishlab chiqaruvchilarning kataloglari va texnik pasportlari. Havolalar rasmiy fayllarga olib boradi; OSTIC hujjatlarida narxlar e’lon qilinmaydi.",
           "doc": "Hujjat", "brand": "Brend", "fmt": "Format", "simon": "SIMON: M7, M3 va i7 seriyalari kataloglari — so‘rov bo‘yicha."},
    "en": {"title": "Documents and catalogues: OSRAM, SALTO, VIKING, TICA | OSTIC", "h1": "Documents for designers",
           "lead": "Catalogues and datasheets from the manufacturers we supply. Links go to the official files; OSTIC documents carry no prices.",
           "doc": "Document", "brand": "Brand", "fmt": "Format", "simon": "SIMON: M7, M3 and i7 series catalogues on request."},
}


def downloads(lang):
    T, C = DL[lang], COMMON[lang]
    rows = []
    for brand, url, title, kind in DOCS:
        ext = url.startswith("http")
        rel = ' target="_blank" rel="noopener"' if ext else " download"
        rows.append(f'<tr><td>{esc(brand)}</td><td><a href="{esc(url)}"{rel}>{esc(title[lang])}</a></td><td>{esc(kind)}</td></tr>')
    inner = (f'{crumbs(lang, NAV[lang][2][1])}<h1>{esc(T["h1"])}</h1><p class="lead">{esc(T["lead"])}</p>'
             f'<div class="tbl"><table><tr><th>{T["brand"]}</th><th>{T["doc"]}</th><th>{T["fmt"]}</th></tr>{"".join(rows)}</table></div>'
             f'<p class="note">{esc(T["simon"])} {esc(C["reqBim"])}</p>'
             f'<div class="cta"><a class="btn primary" href="{SITE}/?lang={lang}#contact">{C["request"]}</a></div>')
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": T["title"], "inLanguage": lang,
          "url": f"{SITE}/downloads/{lang}/", "isPartOf": {"@id": f"{SITE}/#organization"}}
    return page(lang, "downloads", "/downloads/{lang}/", T["title"], T["lead"], ld, inner)


# ------------------------------------------------------------------- projects
PJ = {
    "ru": {"title": "Проекты OSTIC: аэропорт, склад, лицей, жильё, гостиница | Ташкент", "h1": "Проекты OSTIC",
           "lead": "Объекты, на которые поставлены инженерные системы и проведён шеф-монтаж, и объекты в работе.",
           "done": "Поставка выполнена", "progress": "В работе", "systems": "Поставленные системы", "brands": "Бренды", "year": "Год"},
    "uz": {"title": "OSTIC loyihalari: aeroport, ombor, litsey, uy-joy, mehmonxona | Toshkent", "h1": "OSTIC loyihalari",
           "lead": "Muhandislik tizimlari yetkazilgan va shef-montaj o‘tkazilgan obyektlar hamda ish jarayonidagi obyektlar.",
           "done": "Yetkazib berilgan", "progress": "Ish jarayonida", "systems": "Yetkazilgan tizimlar", "brands": "Brendlar", "year": "Yil"},
    "en": {"title": "OSTIC projects: airport, warehouse, lyceum, residential, hotel | Tashkent", "h1": "OSTIC projects",
           "lead": "Facilities supplied with engineering systems and installation supervision, and projects in progress.",
           "done": "Supplied", "progress": "In progress", "systems": "Systems supplied", "brands": "Brands", "year": "Year"},
}


def load_projects():
    return json.loads((B.ROOT / "tools" / "projects.json").read_text(encoding="utf-8"))["projects"]


def has_detail(p):
    return any(p["systems"].get(l) for l in LANGS)


def projects_hub(lang, projects):
    T = PJ[lang]
    cards = []
    for p in projects:
        status = T["done"] if p["status"] == "done" else T["progress"]
        name = esc(p["name"][lang])
        title = f'<a href="/projects/{lang}/{p["slug"]}.html">{name}</a>' if has_detail(p) else name
        cards.append(f'<article class="series"><img src="/assets/projects/{p["img"]}" alt="{name}" width="96" height="96" loading="lazy" decoding="async">'
                     f'<div><h3>{title}</h3><span class="meta">{esc(p["type"][lang])} · {esc(status)}</span></div></article>')
    inner = (f'{crumbs(lang, NAV[lang][1][1])}<h1>{esc(T["h1"])}</h1><p class="lead">{esc(T["lead"])}</p>{"".join(cards)}'
             f'<div class="cta"><a class="btn primary" href="{SITE}/?lang={lang}#contact">{COMMON[lang]["request"]}</a></div>')
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": T["title"], "inLanguage": lang,
          "url": f"{SITE}/projects/{lang}/", "isPartOf": {"@id": f"{SITE}/#organization"},
          "mainEntity": {"@type": "ItemList", "itemListElement": [
              {"@type": "ListItem", "position": i, "name": p["name"][lang]} for i, p in enumerate(projects, 1)]}}
    return page(lang, "projects", "/projects/{lang}/", T["title"], T["lead"], ld, inner)


def project_page(lang, p):
    T = PJ[lang]
    name = p["name"][lang]
    rows = []
    if p.get("year"):
        rows.append(f'<tr><th>{T["year"]}</th><td>{esc(p["year"])}</td></tr>')
    if p.get("brands"):
        rows.append(f'<tr><th>{T["brands"]}</th><td>{esc(", ".join(p["brands"]))}</td></tr>')
    systems = "".join(f"<li>{esc(s)}</li>" for s in p["systems"].get(lang, []))
    scope = p["scope"].get(lang, "")
    inner = (f'{crumbs(lang, name)}<p class="k">{esc(p["type"][lang])}</p><h1>{esc(name)}</h1>'
             f'<img src="/assets/projects/{p["img"]}" alt="{esc(name)}" style="width:100%;height:auto;border-radius:14px" loading="lazy">'
             + (f'<p class="lead">{esc(scope)}</p>' if scope else "")
             + (f'<table>{"".join(rows)}</table>' if rows else "")
             + (f'<h2>{T["systems"]}</h2><ul>{systems}</ul>' if systems else "")
             + f'<div class="cta"><a class="btn primary" href="{SITE}/?lang={lang}#contact">{COMMON[lang]["request"]}</a></div>')
    ld = {"@context": "https://schema.org", "@type": "WebPage", "name": name, "inLanguage": lang,
          "isPartOf": {"@id": f"{SITE}/#organization"}}
    return page(lang, "projects", "/projects/{lang}/" + p["slug"] + ".html", f'{name} — {T["h1"]}', scope or T["lead"], ld, inner)


# ------------------------------------------------------------------- articles
ART = {}

ART["choosing-led-lighting"] = {
    "ru": {"title": "Как выбрать светодиодный светильник: цветовая температура, IP и мощность",
           "desc": "Три вопроса при выборе LED-светильника: какая цветовая температура, какая степень защиты IP и сколько ватт заменят привычную лампу.",
           "intro": "Перед выбором модели достаточно ответить на три вопроса: какой нужен свет, в каких условиях он будет работать и сколько света нужно.",
           "sections": [
               ("1. Цветовая температура", "", (["Температура", "Свет", "Где применять"], [
                   ["3000 K", "Тёплый белый", "Дом, номера гостиниц, рестораны: уютная, спокойная обстановка"],
                   ["4000 K", "Нейтральный белый", "Офис, торговый зал, учебные помещения: помогает сосредоточиться"],
                   ["6500 K", "Холодный белый", "Склад, цех, техпомещения, паркинг: максимальная чёткость"]])),
               ("2. Степень защиты IP", "Выбирайте по условиям помещения.", (["IP", "Условия", "Примеры серий"], [
                   ["IP20", "Сухие помещения: офис, жилая комната, торговый зал", "Даунлайты, споты, панели"],
                   ["IP44", "Возможны брызги воды: ванная, кухня", "Влагозащищённые серии"],
                   ["IP65", "Защита от пыли и струй воды: коридор, крыльцо, склад", "Bulkhead, High Bay, Batten"],
                   ["IP66", "Улица, любая погода", "Садовые и уличные светильники"]])),
               ("3. Мощность и световой поток", "Сравнивайте не ватты, а люмены. Светодиод даёт тот же свет при в 6–8 раз меньшем потреблении.", (["LED VALUE", "Световой поток", "Эквивалент лампы накаливания"], [
                   ["5 W", "500 lm", "40 W"], ["7 W", "700 lm", "50–60 W"], ["9 W", "900 lm", "60–75 W"],
                   ["12 W", "1200 lm", "75–100 W"], ["14 W", "1400 lm", "100 W"]])),
           ],
           "after": "Сравнение по световому потоку ориентировочное. Сколько светильников нужно на помещение, можно оценить калькулятором на сайте, а точный светорасчёт мы делаем по проекту."},
    "uz": {"title": "LED yoritgichni qanday tanlash kerak: rang harorati, IP va quvvat",
           "desc": "LED yoritgich tanlashda uchta savol: qaysi rang harorati, qaysi IP himoya darajasi va odatiy lampani necha vatt almashtiradi.",
           "intro": "Model tanlashdan oldin uchta savolga javob berish kifoya: qanday yorug‘lik kerak, u qanday sharoitda ishlaydi va qancha yorug‘lik kerak.",
           "sections": [
               ("1. Rang harorati", "", (["Harorat", "Yorug‘lik", "Qayerda"], [
                   ["3000 K", "Iliq oq", "Uy, mehmonxona xonalari, restoran: qulay, sokin muhit"],
                   ["4000 K", "Neytral oq", "Ofis, savdo zali, ta’lim: diqqatni jamlashga yordam beradi"],
                   ["6500 K", "Sovuq oq", "Ombor, sex, texnik xonalar, parking: maksimal tiniqlik"]])),
               ("2. IP himoya darajasi", "Xona sharoitiga qarab tanlang.", (["IP", "Sharoit", "Seriya misollari"], [
                   ["IP20", "Quruq xonalar: ofis, yashash xonasi, savdo zali", "Downlight, spot, panel"],
                   ["IP44", "Suv sachrashi mumkin: hammom, oshxona", "Namlikka chidamli seriyalar"],
                   ["IP65", "Chang va suv oqimidan himoya: yo‘lak, ayvon, ombor", "Bulkhead, High Bay, Batten"],
                   ["IP66", "Ko‘cha, har qanday ob-havo", "Bog‘ va ko‘cha yoritgichlari"]])),
               ("3. Quvvat va yorug‘lik oqimi", "Vattni emas, lyumenni solishtiring. LED bir xil yorug‘likni 6–8 barobar kam energiya bilan beradi.", (["LED VALUE", "Yorug‘lik oqimi", "Cho‘g‘lanma lampa ekvivalenti"], [
                   ["5 W", "500 lm", "40 W"], ["7 W", "700 lm", "50–60 W"], ["9 W", "900 lm", "60–75 W"],
                   ["12 W", "1200 lm", "75–100 W"], ["14 W", "1400 lm", "100 W"]])),
           ],
           "after": "Yorug‘lik oqimi bo‘yicha taqqoslash taxminiy. Xonaga nechta yoritgich kerakligini saytdagi kalkulyator bilan baholash mumkin, aniq yoritish hisobini esa loyiha bo‘yicha qilamiz."},
    "en": {"title": "How to choose an LED luminaire: colour temperature, IP rating and power",
           "desc": "Three questions when choosing an LED luminaire: which colour temperature, which IP rating, and how many watts replace a familiar lamp.",
           "intro": "Before picking a model, answer three questions: what light you need, in what conditions it will work, and how much light is needed.",
           "sections": [
               ("1. Colour temperature", "", (["Temperature", "Light", "Where"], [
                   ["3000 K", "Warm white", "Homes, hotel rooms, restaurants: a calm, cosy atmosphere"],
                   ["4000 K", "Neutral white", "Offices, sales floors, classrooms: helps concentration"],
                   ["6500 K", "Cool white", "Warehouses, workshops, utility rooms, car parks: maximum clarity"]])),
               ("2. IP protection rating", "Choose by the conditions in the room.", (["IP", "Conditions", "Example ranges"], [
                   ["IP20", "Dry rooms: office, living room, sales floor", "Downlights, spots, panels"],
                   ["IP44", "Splashing water possible: bathroom, kitchen", "Damp-proof ranges"],
                   ["IP65", "Protected against dust and water jets: corridor, porch, warehouse", "Bulkhead, High Bay, Batten"],
                   ["IP66", "Outdoors, any weather", "Garden and street luminaires"]])),
               ("3. Power and luminous flux", "Compare lumens, not watts. LED gives the same light with 6–8 times less energy.", (["LED VALUE", "Luminous flux", "Incandescent equivalent"], [
                   ["5 W", "500 lm", "40 W"], ["7 W", "700 lm", "50–60 W"], ["9 W", "900 lm", "60–75 W"],
                   ["12 W", "1200 lm", "75–100 W"], ["14 W", "1400 lm", "100 W"]])),
           ],
           "after": "The flux comparison is approximate. The site calculator gives a rough count of luminaires per room; the exact lighting calculation is done per project."},
}

ART["fan-coil-types"] = {
    "ru": {"title": "Типы фанкойлов: канальный, кассетный или напольно-потолочный",
           "desc": "Чем отличаются канальные, кассетные и напольно-потолочные фанкойлы TICA и какой тип подходит для потолка, холла или номера.",
           "intro": "Фанкойл — внутренний блок системы, который охлаждает или нагревает воздух в помещении водой от чиллера или котла. Тип выбирают по тому, есть ли запотолочное пространство и как далеко нужно раздать воздух.",
           "sections": [
               ("Сравнение типов", "", (["Тип", "Серия TICA", "Главное"], [
                   ["Канальный скрытого монтажа", "TCR", "Толщина от 230 мм и глубина от 470 мм — под низкие потолки; статическое давление 12/30/50 Па переключается на объекте"],
                   ["Канальный высокого напора", "TFM", "800B–3000B, от 8,3 до 34,4 кВт холода и до 56 кВт тепла при 130 Па — длинные воздуховоды, холлы и залы"],
                   ["Кассетный", "TKM", "Раздача на 360°, семь скоростей от 22 дБ(А), встроенный дренажный насос, панели 750/850/950 мм"],
                   ["Напольно-потолочный", "TC", "Открытая установка без запотолочного пространства, автоматические жалюзи, обслуживание с одной стороны"]])),
               ("Тихая работа и экономия", "Версия TCR-DC на бесщёточном моторе работает от 20 дБ(А); семь скоростей и плавная регулировка снижают потребление на малой нагрузке до 6–8 Вт. Это важно для гостиничных номеров и переговорных.", None),
               ("Управление", "Термостат TA — с ЖК-экраном и тремя скоростями, сенсорный TE — для AC и DC фанкойлов; 2- и 4-трубные схемы. Опциональный интерфейс RS485 (у TCR-DC — RS485 и Modbus) подключает фанкойлы к диспетчеризации.", None),
               ("Как выбрать", "", (["Ситуация", "Подходящий тип"], [
                   ["Есть подшивной потолок, нужен скрытый монтаж", "Канальный TCR или кассетный TKM"],
                   ["Длинная разветвлённая сеть воздуховодов", "Канальный высокого напора TFM"],
                   ["Потолок без запотолочного пространства (бетон, дерево)", "Напольно-потолочный TC"],
                   ["Номера и переговорные, где важна тишина", "Версии на DC-моторе"]])),
           ],
           "after": "Холодопроизводительность ориентировочно можно оценить калькулятором на сайте. Подбор по нагрузкам и схеме (2 или 4 трубы) делаем по проекту."},
    "uz": {"title": "Fankoyl turlari: kanalli, kassetali yoki pol-shift",
           "desc": "TICA kanalli, kassetali va pol-shift fankoyllari nimasi bilan farq qiladi va shift, zal yoki xona uchun qaysi turi mos.",
           "intro": "Fankoyl — xonadagi havoni chiller yoki qozondan keladigan suv bilan sovutadigan yoki isitadigan ichki blok. Turi shift ostida bo‘sh joy borligi va havoni qanchalik uzoqqa tarqatish kerakligiga qarab tanlanadi.",
           "sections": [
               ("Turlarni solishtirish", "", (["Turi", "TICA seriyasi", "Asosiysi"], [
                   ["Yashirin montajli kanalli", "TCR", "Qalinligi 230 mm dan, chuqurligi 470 mm dan — past shiftlar uchun; statik bosim 12/30/50 Pa joyida almashtiriladi"],
                   ["Yuqori bosimli kanalli", "TFM", "800B–3000B, 8,3–34,4 kVt sovutish va 130 Pa da 56 kVt gacha isitish — uzun havo quvurlari, zal va hollar"],
                   ["Kassetali", "TKM", "360° tarqatish, 22 dB(A) dan yetti tezlik, ichki drenaj nasosi, 750/850/950 mm panellar"],
                   ["Pol-shift", "TC", "Shift ostida bo‘sh joy kerak emas, avtomatik jalyuzi, bir tomondan xizmat ko‘rsatish"]])),
               ("Jim ishlash va tejamkorlik", "Cho‘tkasiz motorli TCR-DC versiyasi 20 dB(A) dan ishlaydi; yetti tezlik va silliq rostlash past yuklamada iste’molni 6–8 Vt gacha tushiradi. Bu mehmonxona xonalari va muzokara xonalari uchun muhim.", None),
               ("Boshqaruv", "TA termostati — LCD ekran va uch tezlik, sensorli TE — AC va DC fankoyllar uchun; 2 va 4 quvurli sxemalar. Ixtiyoriy RS485 interfeysi (TCR-DC da RS485 va Modbus) fankoyllarni dispetcherlashga ulaydi.", None),
               ("Qanday tanlash kerak", "", (["Holat", "Mos turi"], [
                   ["Osma shift bor, yashirin montaj kerak", "Kanalli TCR yoki kassetali TKM"],
                   ["Uzun tarmoqlangan havo quvurlari", "Yuqori bosimli kanalli TFM"],
                   ["Shift ostida bo‘sh joy yo‘q (beton, yog‘och)", "Pol-shift TC"],
                   ["Jimjitlik muhim bo‘lgan xonalar", "DC motorli versiyalar"]])),
           ],
           "after": "Sovutish quvvatini saytdagi kalkulyator bilan taxminan baholash mumkin. Yuklama va sxema (2 yoki 4 quvur) bo‘yicha tanlovni loyiha bo‘yicha qilamiz."},
    "en": {"title": "Fan coil types: ducted, cassette or floor-and-ceiling",
           "desc": "How TICA ducted, cassette and floor-and-ceiling fan coils differ, and which type suits a ceiling void, a hall or a hotel room.",
           "intro": "A fan coil is the indoor unit that cools or heats room air with water from a chiller or boiler. The type is chosen by whether there is a ceiling void and how far the air has to be distributed.",
           "sections": [
               ("Types compared", "", (["Type", "TICA range", "Key points"], [
                   ["Ceiling-concealed ducted", "TCR", "From 230 mm thick and 470 mm deep for low ceilings; static pressure 12/30/50 Pa set on site"],
                   ["High static pressure ducted", "TFM", "800B–3000B, 8.3–34.4 kW cooling and up to 56 kW heating at 130 Pa: long ducts, halls"],
                   ["Cassette", "TKM", "360° air throw, seven speeds from 22 dB(A), built-in drain pump, 750/850/950 mm panels"],
                   ["Floor-and-ceiling", "TC", "Exposed mounting with no ceiling void, automatic louvres, service from one side"]])),
               ("Quiet running and savings", "The TCR-DC version with a brushless motor runs from 20 dB(A); seven speeds and smooth control bring consumption down to 6–8 W at low load. This matters in hotel rooms and meeting rooms.", None),
               ("Controls", "The TA thermostat has an LCD and three speeds; the touch TE works with AC and DC fan coils, for 2- and 4-pipe systems. An optional RS485 interface (RS485 and Modbus on TCR-DC) connects the units to building management.", None),
               ("How to choose", "", (["Situation", "Suitable type"], [
                   ["Suspended ceiling, concealed installation wanted", "Ducted TCR or cassette TKM"],
                   ["Long branched ductwork", "High static pressure ducted TFM"],
                   ["No ceiling void (concrete, timber)", "Floor-and-ceiling TC"],
                   ["Rooms where quiet matters", "DC-motor versions"]])),
           ],
           "after": "The site calculator gives a rough cooling capacity. Selection by loads and system (2- or 4-pipe) is done per project."},
}

ART["hotel-access-and-room-control"] = {
    "ru": {"title": "Гостиничный номер: электронные замки SALTO и управление номером SIMON",
           "desc": "Какие решения SALTO и SIMON ставят в гостиницах: накладки и цилиндры для дверей, считыватели для лифтов и беспроводное управление номером.",
           "intro": "В гостинице доступ и автоматика номера решаются разными системами: замки и считыватели SALTO отвечают за двери, лифты и проходы, а беспроводная система SIMON — за свет, климат и статус номера.",
           "sections": [
               ("Двери и проходы: SALTO", "", (["Решение", "Где применять"], [
                   ["XS4 Original+ — электронная накладка", "Двери номеров: ставится на существующую дверь без штробления и проводки; версии с механическим ключом, приватностью, двусторонним считывателем"],
                   ["XS4 One — компактная накладка", "Встроенный считыватель, квадратная геометрия, версия с клавиатурой для PIN-доступа"],
                   ["Neo — электронный цилиндр", "Где накладку поставить нельзя: техдвери, щитовые, шкафы; меняется только цилиндр"],
                   ["XS Readers — настенные считыватели", "Лифты, турникеты, шлагбаумы и раздвижные двери"]])),
               ("Номер: SIMON", "", (["Решение", "Что даёт"], [
                   ["Wireless RCU", "Zigbee-шлюз, термостат, кнопочные панели, дверной звонок и датчики — автоматика номера без прокладки шины управления"],
                   ["Simon i7", "Проектная серия: многопостовые рамки, TV, данные и мультимедиа в одном ряду"],
                   ["Footlight", "Ночная подсветка пола: включается по движению и гаснет автоматически"]])),
           ],
           "after": "OSTIC — официальный партнёр SALTO в Узбекистане и официальный проектный дилер Simon Asia Pacific. Состав системы под номерной фонд подбираем по проекту."},
    "uz": {"title": "Mehmonxona xonasi: SALTO elektron qulflari va SIMON xona boshqaruvi",
           "desc": "Mehmonxonalarda qaysi SALTO va SIMON yechimlari qo‘yiladi: eshik nakladkalari va silindrlar, lift o‘quvchilari va xonani simsiz boshqarish.",
           "intro": "Mehmonxonada kirish va xona avtomatikasi turli tizimlar bilan hal qilinadi: SALTO qulflari va o‘quvchilari eshiklar, liftlar va o‘tish joylari uchun, SIMON simsiz tizimi esa yoritish, iqlim va xona holati uchun javob beradi.",
           "sections": [
               ("Eshiklar va o‘tish joylari: SALTO", "", (["Yechim", "Qayerda"], [
                   ["XS4 Original+ — elektron nakladka", "Xona eshiklari: mavjud eshikka devorni o‘ymasdan va sim tortmasdan o‘rnatiladi; mexanik kalitli, maxfiylik va ikki tomonlama o‘quvchili versiyalar"],
                   ["XS4 One — ixcham nakladka", "Ichki o‘quvchi, kvadrat shakl, PIN-kirish uchun klaviaturali versiya"],
                   ["Neo — elektron silindr", "Nakladka qo‘yib bo‘lmaydigan joylar: texnik eshiklar, shitxonalar, shkaflar; faqat silindr almashtiriladi"],
                   ["XS Readers — devor o‘quvchilari", "Liftlar, turniketlar, shlagbaumlar va surma eshiklar"]])),
               ("Xona: SIMON", "", (["Yechim", "Nima beradi"], [
                   ["Wireless RCU", "Zigbee shlyuzi, termostat, tugmali panellar, eshik qo‘ng‘irog‘i va datchiklar — boshqaruv shinasini tortmasdan xona avtomatikasi"],
                   ["Simon i7", "Loyiha seriyasi: ko‘p postli ramkalar, TV, ma’lumot va multimedia bir qatorda"],
                   ["Footlight", "Tungi pol yoritgichi: harakatda yonadi va o‘zi o‘chadi"]])),
           ],
           "after": "OSTIC — SALTO ning O‘zbekistondagi rasmiy hamkori va Simon Asia Pacific ning rasmiy loyiha dileri. Xonalar soniga mos tizim tarkibini loyiha bo‘yicha tanlaymiz."},
    "en": {"title": "The hotel room: SALTO electronic locks and SIMON room control",
           "desc": "Which SALTO and SIMON solutions go into hotels: escutcheons and cylinders for doors, readers for lifts, and wireless room control.",
           "intro": "In a hotel, access and room automation are handled by different systems: SALTO locks and readers cover doors, lifts and passages, while the SIMON wireless system covers lighting, climate and room status.",
           "sections": [
               ("Doors and passages: SALTO", "", (["Solution", "Where"], [
                   ["XS4 Original+ electronic escutcheon", "Guest room doors: fits an existing door with no chasing or wiring; versions with mechanical key, privacy and double reader"],
                   ["XS4 One compact escutcheon", "Built-in reader, square design, keypad version for PIN access"],
                   ["Neo electronic cylinder", "Where an escutcheon cannot be fitted: utility doors, switch rooms, cabinets; only the cylinder is replaced"],
                   ["XS wall readers", "Lifts, turnstiles, barriers and sliding doors"]])),
               ("The room: SIMON", "", (["Solution", "What it does"], [
                   ["Wireless RCU", "Zigbee gateway, thermostat, button panels, doorbell and sensors: room automation without a control bus"],
                   ["Simon i7", "Project series: multi-gang frames with TV, data and multimedia in one row"],
                   ["Footlight", "Night floor light that switches on with movement and off automatically"]])),
           ],
           "after": "OSTIC is an official Salto partner in Uzbekistan and an official project dealer of Simon Asia Pacific. The system for a given number of rooms is selected per project."},
}

AH = {
    "ru": {"title": "Статьи OSTIC: освещение, климат, доступ | Ташкент", "h1": "Статьи", "lead": "Короткие руководства по выбору оборудования для коммерческих объектов."},
    "uz": {"title": "OSTIC maqolalari: yoritish, iqlim, kirish nazorati | Toshkent", "h1": "Maqolalar", "lead": "Tijoriy obyektlar uchun uskuna tanlash bo‘yicha qisqa qo‘llanmalar."},
    "en": {"title": "OSTIC articles: lighting, climate, access | Tashkent", "h1": "Articles", "lead": "Short guides to choosing equipment for commercial projects."},
}


def article(lang, slug):
    a = ART[slug][lang]
    C = COMMON[lang]
    parts = [f'{crumbs(lang, NAV[lang][3][1])}<h1>{esc(a["title"])}</h1><p class="lead">{esc(a["intro"])}</p>']
    for h, p, tbl in a["sections"]:
        parts.append(f"<h2>{esc(h)}</h2>")
        if p:
            parts.append(f"<p>{esc(p)}</p>")
        if tbl:
            parts.append(table(*tbl))
    parts.append(f'<p class="note">{esc(a["after"])}</p>')
    parts.append(f'<div class="cta"><a class="btn primary" href="{SITE}/?lang={lang}#tools">{C["calc"]}</a>'
                 f'<a class="btn" href="{SITE}/?lang={lang}#contact">{C["request"]}</a></div>')
    if slug == "choosing-led-lighting":
        parts.append(f'<p class="crumbs">{esc(C["source"])}</p>')
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": a["title"], "description": a["desc"],
          "inLanguage": lang, "datePublished": TODAY, "dateModified": TODAY,
          "author": {"@type": "Organization", "name": "OSTIC", "url": SITE},
          "publisher": {"@id": f"{SITE}/#organization"},
          "mainEntityOfPage": f"{SITE}/articles/{lang}/{slug}.html"}
    return page(lang, "articles", "/articles/{lang}/" + slug + ".html", a["title"] + " | OSTIC", a["desc"], ld, "".join(parts))


def articles_hub(lang):
    T = AH[lang]
    cards = "".join(
        f'<a class="card" href="/articles/{lang}/{s}.html"><h3>{esc(ART[s][lang]["title"])}</h3><p>{esc(ART[s][lang]["desc"])}</p></a>'
        for s in ART)
    inner = f'{crumbs(lang, T["h1"])}<h1>{esc(T["h1"])}</h1><p class="lead">{esc(T["lead"])}</p><div class="hub">{cards}</div>'
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": T["title"], "inLanguage": lang,
          "url": f"{SITE}/articles/{lang}/", "isPartOf": {"@id": f"{SITE}/#organization"}}
    return page(lang, "articles", "/articles/{lang}/", T["title"], T["lead"], ld, inner)


# ------------------------------------------------------------------ outputs
def write(path, html_text):
    out = DIST / path.lstrip("/")
    if path.endswith("/"):
        out = out / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html_text, encoding="utf-8")


def update_sitemap(entries):
    p = DIST / "sitemap.xml"
    s = p.read_text(encoding="utf-8")
    s = re.sub(r"\s*<url>\s*<loc>https://ostic\.uz/(downloads|projects|articles)/.*?</url>", "", s, flags=re.S)
    chunks = []
    for path, alts in entries:
        links = "".join(f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{SITE}{a}"/>' for l, a in alts.items())
        links += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}{alts["ru"]}"/>'
        chunks.append(f"  <url>\n    <loc>{SITE}{path}</loc>{links}\n    <lastmod>{TODAY}</lastmod>\n    <priority>0.7</priority>\n  </url>")
    p.write_text(s.replace("</urlset>", "\n".join(chunks) + "\n</urlset>"), encoding="utf-8")


def update_llms():
    p = DIST / "llms.txt"
    s = re.sub(r"\n## (Documents|Projects pages|Articles).*", "", p.read_text(encoding="utf-8"), flags=re.S).rstrip("\n")
    lines = ["", "", "## Documents", f"- [Documents for designers (English)]({SITE}/downloads/en/)",
             f"- [Документы (Русский)]({SITE}/downloads/ru/)", f"- [Hujjatlar (O‘zbekcha)]({SITE}/downloads/uz/)",
             "", "## Articles"]
    for slug in ART:
        lines.append(f"- [{ART[slug]['en']['title']}]({SITE}/articles/en/{slug}.html) · [RU]({SITE}/articles/ru/{slug}.html) · [UZ]({SITE}/articles/uz/{slug}.html)")
    p.write_text(s + "\n".join(lines) + "\n", encoding="utf-8")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    projects = load_projects()
    entries = []
    for lang in LANGS:
        for path, alts, html_text in [downloads(lang), projects_hub(lang, projects), articles_hub(lang)]:
            write(path, html_text); entries.append((path, alts))
        for slug in ART:
            path, alts, html_text = article(lang, slug)
            write(path, html_text); entries.append((path, alts))
        for p in projects:
            if has_detail(p):
                path, alts, html_text = project_page(lang, p)
                write(path, html_text); entries.append((path, alts))
    update_sitemap(entries)
    update_llms()
    print("pages:", len(entries), "| project pages with details:", sum(1 for p in projects if has_detail(p)))


if __name__ == "__main__":
    main()
