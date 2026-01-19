# config.py
# Bu faylda bot uchun muhim sozlamalar saqlanadi
import os
from dotenv import load_dotenv

# .env faylidan environment variablelarni yuklash
load_dotenv()

# TOKEN — Telegram botning maxfiy kaliti
# Bu token orqali bot Telegram serverlari bilan bog'lanadi
# Token .env faylidan olinadi (xavfsizlik uchun)

TOKEN = os.getenv('BOT_TOKEN')

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable o'rnatilmagan! .env faylida BOT_TOKEN ni o'rnating.")
