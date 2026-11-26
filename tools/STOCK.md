# Ombor qoldig'ini Google Sheet'dan boshqarish

Sayt qoldiqni jadvaldan o'qiydi. Jadvalni yangilasangiz, sayt keyingi ochilishda yangi sonlarni ko'rsatadi: kodga tegish, zip yig'ish va push kerak emas.

## Bir martalik sozlash
1. Google Sheets'da yangi jadval oching va `tools/stock-template.csv` faylini import qiling (Fayl → Import → Yuklash). Ustunlar: `series`, `model`, `qty`.
2. **Fayl → Ulashish → Internetda nashr qilish** → varaq tanlang, format **CSV** → "Nashr qilish". Chiqqan havolani nusxalang.
3. Havolani menga yuboring. Men uni `index.html` dagi `this.STOCK_CSV` ga yozib, saytni yangilayman (bu bir marta push talab qiladi).

## Har kuni
- `qty` ustunidagi sonni o'zgartiring. Qator o'chirilsa, u model saytda "omborda" ko'rinmaydi.
- `#as_of` qatoridagi sanani yangilang (masalan `26.11.2026`): saytda "Остатки на складе ... на <sana>" shu sanani ko'rsatadi.
- Google nashr qilingan CSV'ni bir necha daqiqa keshlaydi, o'zgarish 5 daqiqagacha kechikishi mumkin.

## Qoidalar
- `series` qiymati katalogdagi seriya nomi bilan aynan bir xil bo'lishi kerak: `Lamps`, `Frameless`, `Downlight`, `Spotlight`, `Panel`, `Batten`, `Floodlight` va boshqalar (`dump_catalog.js` chiqaradigan nomlar).
- `model` qiymati artikul jadvalida "model + quvvat" ko'rinishida bo'lsa (masalan `R90 8W`, `A60 9W`, `R155 18W 4000K`), artikul oynasida ham "omborda" belgisi chiqadi.
- Narxni bu jadvalga yozmang: jadval ommaviy (nashr qilingan) bo'ladi.
- Jadvalni o'qib bo'lmasa, sayt ichidagi oxirgi ma'lum qoldiqni ko'rsatadi.
