# 🤖 Anonim Bot — Xavfsiz versiya

## 🚨 BIRINCHI NAVBATDA (token o'g'irlangan bo'lsa)

1. [@BotFather](https://t.me/BotFather) → `/mybots` → botingiz → `API Token` → **Revoke current token**
2. Yangi tokenni `.env` fayliga yozing
3. GitHub repo'ni o'chiring yoki tokenni history'dan tozalang

---

## 📁 Fayl tuzilishi

```
anonim_bot/
├── bot.py            ← Asosiy kod
├── config.py         ← Token .env dan o'qiladi
├── .env              ← 🔐 MAXFIY (GitHub'ga chiqmasin!)
├── .gitignore        ← .env ni himoyalaydi
├── requirements.txt
└── README.md
```

---

## 🚀 Mahalliy ishga tushirish

```bash
# 1. Kutubxonalar
pip install -r requirements.txt

# 2. .env faylini tahrirlang
nano .env
# BOT_TOKEN=sizning_yangi_tokeningiz

# 3. Ishga tushirish
python bot.py
```

---

## ☁️ XAVFSIZ SERVER — VARIANTLAR

### ✅ 1. Railway.app (Eng oson, BEPUL)
1. [railway.app](https://railway.app) → GitHub bilan login
2. `New Project` → `Deploy from GitHub repo`
3. **Variables** bo'limiga: `BOT_TOKEN` = tokeningiz
4. `.env` fayl kerak emas — Railway o'zi boshqaradi

### ✅ 2. Render.com (BEPUL)
1. [render.com](https://render.com) → New → Web Service
2. GitHub repo ulang
3. **Environment** → `BOT_TOKEN` qo'shing
4. Start command: `python bot.py`

### ✅ 3. VPS (DigitalOcean / Hetzner)
```bash
# Serverga ulaning
ssh root@server_ip

# Botni ko'chiring
git clone https://github.com/sizning_repo
cd anonim_bot

# .env yarating (GitHub'da yo'q!)
nano .env
# BOT_TOKEN=tokeningiz

pip install -r requirements.txt

# Fonda ishlatish (o'chmasin)
nohup python bot.py &
# yoki
screen -S bot
python bot.py
# Ctrl+A, D — chiqish
```

---

## 🔐 XAVFSIZLIK QOIDALARI

| ✅ To'g'ri | ❌ Xato |
|---|---|
| Token `.env` da | Token `config.py` da yozilgan |
| `.gitignore` da `.env` bor | `.env` GitHub'ga push qilingan |
| Server env variables | Token kod ichida hardcoded |
| Tokenni muntazam yangilash | Bir token yillab ishlatish |

---

## ⚡ GitHub'ga push qilish (xavfsiz)

```bash
git init
git add bot.py config.py requirements.txt .gitignore README.md
# .env ni QO'SHMANG!
git commit -m "Anonim bot - xavfsiz versiya"
git push origin main
```
