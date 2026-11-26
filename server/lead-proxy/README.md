# Lead proxy: Telegram tokenini saytdan olib tashlash

Muammo: sayt formasi arizalarni Telegram'ga to'g'ridan-to'g'ri yuborar edi, bot tokeni esa
`index.html` ichida ochiq yozilgan edi. Repo public, shuning uchun token hammaga ko'rinadi.

Yechim: forma arizani shu Worker'ga yuboradi, Worker esa Telegram'ga o'zi yuboradi. Token faqat
Worker'ning maxfiy o'zgaruvchilarida (secrets) saqlanadi.

## 1. Eski tokenni bekor qiling (birinchi, shart)

Eski token repo tarixida qoladi, uni faqat almashtirish himoya qiladi.

1. Telegram'da `@BotFather` ni oching.
2. `/mybots` → botni tanlang → **API Token** → **Revoke current token**.
3. Yangi tokenni nusxalang. Uni hech kimga, hech qaysi chatga va faylga yozmang.

## 2. Worker'ni joylash (Cloudflare, bepul reja yetadi)

1. dash.cloudflare.com → **Workers & Pages** → **Create** → **Create Worker**, nom: `ostic-lead`.
2. **Edit code** → ichidagini o'chirib, `worker.js` mazmunini joylang → **Deploy**.
3. **Settings → Variables and Secrets** → **Add**, turi **Secret**:
   - `TG_TOKEN` = yangi bot tokeni
   - `TG_CHAT` = arizalar tushadigan chat id (oldingi saytdagi bilan bir xil)
4. Qayta **Deploy** qiling. Worker manzili chiqadi, masalan `https://ostic-lead.<akkaunt>.workers.dev`.
5. (Ixtiyoriy, tavsiya) Spam'ga qarshi: **Security → WAF → Rate limiting rules** da shu manzilga
   daqiqasiga 5 ta POST dan ko'p bo'lmasin degan qoida qo'shing.

### 2-variant: buyruq qatori orqali (Node o'rnatilgan bo'lsa)

`C:\ostic.uz\server\lead-proxy` papkasida:

```
npx wrangler login
npx wrangler secret put TG_TOKEN
npx wrangler secret put TG_CHAT
npx wrangler deploy
```

`secret put` so'raganda tokenni o'zingiz yozasiz (ekranda ko'rinmaydi). Oxirgi buyruq Worker manzilini chiqaradi.

### Arizalar OSTIC platformaga ham tushsin (ixtiyoriy)

Worker arizani `cloud.ostic.uz` dagi "Saytdan arizalar" bo'limiga ham yuboradi. So'rov serverdan serverga boradi,
kalit saytda turmaydi. Batafsil ma'lumot platforma repo'sidagi `docs/public-site.md` faylida.

1. Kamida 32 belgili tasodifiy qator yarating (masalan parol menejerida). Uni chatga yoki faylga yozmang.
2. Platforma serverining `backend/.env` fayliga `SITE_LEAD_SECRET=<shu qator>` va `PUBLIC_SITE_COMPANY_TIN=<EIGHT DOORS STIR>`
   ni qo'shing, API'ni qayta ishga tushiring.
3. Worker'ga ikkita **Secret** qo'shing:
   - `PLATFORM_LEAD_URL` = `https://cloud.ostic.uz/api/v1/public/site-leads`
   - `PLATFORM_LEAD_SECRET` = o'sha qator
4. Qayta **Deploy** qiling. Saytdan sinov arizasini yuboring: u platformadagi "Saytdan arizalar" sahifasida ko'rinishi kerak.

Telegram, Google Sheet yoki platformadan kamida biri arizani qabul qilsa, tashrif buyuruvchi "yuborildi" deb ko'radi.

## 3. Saytni ulash

Worker manzilini menga yuboring. Men `index.html` dagi `LEAD_WEBHOOK` ga qo'yaman va saytni qayta
yig'aman. Shundan keyingina yangi versiyani joylash kerak, aks holda Telegram'ga arizalar bormay qoladi.

## 4. Tekshirish

Saytdan sinov arizasini yuboring, Telegram'da kelganini ko'ring. Eski token bilan
`https://api.telegram.org/bot<eski_token>/getMe` ishlamasligi kerak.

## Nima tekshiriladi (worker.js)

- Faqat `https://ostic.uz` va `https://www.ostic.uz` manzillaridan kelgan so'rovlar qabul qilinadi.
- So'rov hajmi 8 KB gacha, maydonlar uzunligi cheklangan, boshqaruv belgilari olib tashlanadi.
- "О проекте" kamida 8 belgi (formadagi qoida bilan bir xil).
- Ruxsat etilmagan maydonlar xabarga kirmaydi.
- Ixtiyoriy `RL` rate-limit binding bo'lsa, IP bo'yicha cheklaydi.
