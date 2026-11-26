# Arizalarni Google Sheet'da saqlash

Worker har arizani Telegram'ga yuborgach shu jadvalga ham yozadi. Telegram ishlamay qolsa ham ariza yo'qolmaydi.

1. Google Sheets'da yangi jadval oching (masalan "OSTIC arizalar").
2. **Kengaytmalar → Apps Script**. `Code.gs` mazmunini joylang, saqlang.
3. **Project Settings → Script properties**: `SHARED_SECRET` = uzun tasodifiy satr (o'zingiz o'ylab toping, hech kimga bermang).
4. **Deploy → New deployment → Web app**: "Execute as: Me", "Who has access: Anyone". Ruxsat so'raganda tasdiqlang. Web app manzilini nusxalang.
5. Worker'ga ikkita secret qo'shing (Cloudflare → Worker → Settings → Variables and Secrets, yoki `npx wrangler secret put ...`):
   - `SHEET_URL` = web app manzili
   - `SHEET_SECRET` = 3-qadamdagi satr
6. Saytdan sinov arizasi yuboring: Telegram'ga xabar, jadvalga yangi qator tushishi kerak.

Xavfsizlik: maxfiy satrsiz kelgan so'rov jadvalga yozilmaydi. `=`, `+`, `-`, `@` bilan boshlangan qiymatlar formula bo'lib ishlamasligi uchun matn sifatida yoziladi.
