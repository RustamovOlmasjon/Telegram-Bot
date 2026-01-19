# 🤖 Telegram Instagram Downloader Bot

Instagram'dan video va audio yuklab oluvchi Telegram bot.

## ✨ Imkoniyatlar

- 📹 Instagram video yuklab olish
- 🎵 Instagram audio (musiqa) yuklab olish
- 🔄 Avtomatik fayl hajmini tekshirish
- 🧹 Vaqtinchalik fayllarni avtomatik tozalash
- 📱 Reply va Inline klaviaturalar
- 📞 Kontakt va joylashuv so'rash

## 🚀 Tez Boshlash

### 1. Bot Token Olish

1. Telegram'da [@BotFather](https://t.me/BotFather) ga boring
2. `/newbot` buyrug'ini yuboring
3. Bot nomini va username'ini kiriting
4. Token olasiz

### 2. Sozlash

1. `.env` faylini oching
2. `YOUR_BOT_TOKEN_HERE` o'rniga tokenni yozing:
   ```
   BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

### 3. Kutubxonalarni O'rnatish

```bash
pip install -r requirements.txt
```

### 4. Ishga Tushirish

```bash
python run.py
```

## 📋 Buyruqlar

- `/start` - Botni boshlash
- `/help` - Yordam
- `/salom` - Salom aytish
- `/inline` - Inline tugmalar
- `/product` - Mahsulot ko'rsatish
- `/contact` - Kontakt so'rash
- `/remove` - Klaviaturani olib tashlash

## 🎯 Foydalanish

1. Botni ishga tushiring
2. Instagram link yuboring:
   ```
   https://www.instagram.com/reel/ABC123/
   ```
3. Bot video va audio yuboradi

## 📦 Texnologiyalar

- **Python 3.8+**
- **aiogram 3.24.0** - Telegram Bot API
- **yt-dlp** - Video yuklab olish
- **python-dotenv** - Environment variables

## 📁 Fayl Tuzilishi

```
Telegram-Bot/
├── run.py                 # Asosiy bot fayli
├── config.py              # Sozlamalar
├── keyboards.py           # Klaviaturalar
├── instagram_downloader.py # Instagram yuklovchi
├── requirements.txt       # Kutubxonalar
├── .env                   # Token (maxfiy)
├── .gitignore            # Git ignore
└── README.md             # Qo'llanma
```

## ⚠️ Muhim

- `.env` faylini GitHub'ga yuklamang!
- Token'ni hech kimga bermang!
- Maksimal fayl hajmi: 50 MB

## 🐛 Xatoliklar

Agar muammo bo'lsa:
1. Token to'g'ri ekanligini tekshiring
2. Kutubxonalar o'rnatilganligini tekshiring
3. Python versiyasi 3.8+ ekanligini tekshiring

## 📝 Litsenziya

MIT License

## 👨‍💻 Muallif

O'lmasbek
