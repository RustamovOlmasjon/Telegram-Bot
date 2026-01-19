import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from config import TOKEN

# Keyboards faylidan klaviaturalarni import qilamiz
from keyboards import (
    main_menu_keyboard,       # Asosiy menyu tugmalari
    settings_keyboard,        # Sozlamalar tugmalari
    contact_keyboard,         # Kontakt so'rash tugmalari
    inline_menu,              # Inline tugmalar
    links_keyboard,           # Havolalar tugmalari
    product_keyboard,         # Mahsulot tugmalari
    remove_keyboard,          # Klaviaturani olib tashlash
    create_confirm_keyboard,  # Tasdiqlash tugmalarini yaratuvchi funksiya
)

# Instagram downloader modulini import qilamiz
from instagram_downloader import (
    is_instagram_url,
    download_instagram_content,
    download_youtube_audio,
    cleanup_files,
    get_file_size_mb
)

bot = Bot(token=TOKEN)
dp = Dispatcher()



# COMMAND HANDLERS (Buyruqlar)


@dp.message(CommandStart())
async def cmd_start(message: Message):
    """
    /start buyrug'iga javob.
    Bot imkoniyatlarini tushuntiradi.
    """
    welcome_text = (
        f"Assalomu alaykum, {message.from_user.full_name}!\n\n"
        "🤖 **Ushbu bot quyidagi imkoniyatlarga ega:**\n\n"
        "📹 **Instagram Downloader:**\n"
        "Instagram'dan video, reel yoki TV linkini yuboring va men uni sizga yuklab beraman.\n\n"
        "🎵 **Musiqa qidiruv:**\n"
        "Istalgan qo'shiq nomini yoki ijrochini yozing, men uni YouTube'dan topib, MP3 formatida yuboraman.\n\n"
        "Shunchaki link yoki matn yuboring!"
    )
    await message.answer(
        welcome_text,
        reply_markup=main_menu_keyboard,
        parse_mode="Markdown"
    )


@dp.message(Command('salom'))
async def cmd_salom(message: Message):
    await message.reply('Vaaleykum Assalom!')


@dp.message(Command('help'))
async def cmd_help(message: Message):
    """
    /help buyrug'iga javob.
    Inline tugmalar bilan yordam ko'rsatadi.
    """
    await message.answer(
        "Sizga qanday yordam kerak?\n\n"
        "Quyidagi tugmalardan birini tanlang:",
        reply_markup=links_keyboard  # Inline keyboard qo'shamiz
    )


@dp.message(Command('inline'))
async def cmd_inline(message: Message):
    """
    /inline buyrug'i - Inline tugmalarni ko'rsatish uchun.
    """
    await message.answer(
        "Bu xabarni baholang:",
        reply_markup=inline_menu
    )


@dp.message(Command('product'))
async def cmd_product(message: Message):
    """
    /product buyrug'i - Mahsulot tugmalarini ko'rsatish uchun.
    """
    await message.answer(
        "Mahsulot: iPhone 15 Pro\n"
        "Narxi: $999\n\n"
        "Miqdorni tanlang:",
        reply_markup=product_keyboard
    )


@dp.message(Command('contact'))
async def cmd_contact(message: Message):
    """
    /contact buyrug'i - Kontakt so'rash tugmalarini ko'rsatish.
    """
    await message.answer(
        "Iltimos, ma'lumotlaringizni yuboring:",
        reply_markup=contact_keyboard
    )


@dp.message(Command('remove'))
async def cmd_remove(message: Message):
    """
    /remove buyrug'i - Klaviaturani olib tashlash.
    """
    await message.answer(
        "Klaviatura olib tashlandi.",
        reply_markup=remove_keyboard
    )



# REPLY KEYBOARD HANDLERS (Tugma matnlariga javob)

# Reply keyboard bosilganda tugma matni xabar sifatida keladi
# Shuning uchun F.text filteri orqali ushlaymiz


@dp.message(F.text == "ℹ️ Yordam")
async def help_button_handler(message: Message):
    """'Yordam' tugmasi bosilganda"""
    help_text = (
        "❓ **Qanday foydalanish kerak?**\n\n"
        "1. **Instagram video:** Shunchaki linkni nusxalab botga yuboring.\n"
        "2. **Musiqa:** Qo'shiq nomini yozib yuboring (masalan: *Janob Rasul - Gulyuzim*).\n\n"
        "Bot avtomatik ravishda faylni yuklab beradi."
    )
    await message.answer(help_text, parse_mode="Markdown")



# CONTENT TYPE HANDLERS (Maxsus kontent turlari)


@dp.message(F.contact)
async def handle_contact(message: Message):
    """
    Foydalanuvchi telefon raqamini yuborganda.
    request_contact tugmasi orqali keladi.
    """
    phone = message.contact.phone_number
    await message.answer(
        f"Rahmat! Telefon raqamingiz: {phone}\n"
        f"Tez orada siz bilan bog'lanamiz.",
        reply_markup=main_menu_keyboard
    )


@dp.message(F.location)
async def handle_location(message: Message):
    """
    Foydalanuvchi joylashuvini yuborganda.
    request_location tugmasi orqali keladi.
    """
    lat = message.location.latitude
    lon = message.location.longitude
    await message.answer(
        f"Rahmat! Joylashuvingiz:\n"
        f"Kenglik: {lat}\n"
        f"Uzunlik: {lon}",
        reply_markup=main_menu_keyboard
    )


@dp.message(F.text)
async def handle_text_messages(message: Message):
    """
    Instagram linki yoki qo'shiq qidirish uchun matnli xabarlarni qayta ishlash.
    """
    text = message.text
    
    # Instagram link ekanligini tekshirish
    if is_instagram_url(text):
        # Yuklab olish jarayoni boshlandi
        status_msg = await message.answer("⏳ Instagram'dan yuklab olinmoqda...")
        
        try:
            # Video va audio yuklab olish
            video_path, audio_path = await download_instagram_content(text)
            
            if not video_path and not audio_path:
                await status_msg.edit_text(
                    "❌ Yuklab olishda xatolik yuz berdi.\n"
                    "Iltimos, linkni tekshiring va qayta urinib ko'ring."
                )
                return
            
            # Fayl hajmlarini tekshirish (Telegram Bot API 100 MB limit)
            MAX_SIZE_MB = 100
            
            # Video yuborish
            if video_path:
                video_size = get_file_size_mb(video_path)
                
                if video_size > MAX_SIZE_MB:
                    await message.answer(
                        f"⚠️ Video juda katta ({video_size:.1f} MB).\n"
                        f"Telegram orqali yuborish uchun maksimal hajm {MAX_SIZE_MB} MB."
                    )
                else:
                    await status_msg.edit_text("📹 Video yuborilmoqda...")
                    video_file = FSInputFile(video_path)
                    await message.answer_video(
                        video_file,
                        caption="✅ Instagram video"
                    )
            
            # Audio yuborish
            if audio_path:
                audio_size = get_file_size_mb(audio_path)
                
                if audio_size > MAX_SIZE_MB:
                    await message.answer(
                        f"⚠️ Audio juda katta ({audio_size:.1f} MB).\n"
                        f"Telegram orqali yuborish uchun maksimal hajm {MAX_SIZE_MB} MB."
                    )
                else:
                    await status_msg.edit_text("🎵 Audio yuborilmoqda...")
                    audio_file = FSInputFile(audio_path)
                    await message.answer_audio(
                        audio_file,
                        caption="✅ Instagram audio (musiqa)"
                    )
            
            # Muvaffaqiyatli xabar
            await status_msg.edit_text("✅ Tayyor! Video va audio yuborildi.")
            
            # Vaqtinchalik fayllarni o'chirish
            cleanup_files(video_path, audio_path)
            
        except Exception as e:
            logger.error(f"Instagram handler xatolik: {e}")
            await status_msg.edit_text("❌ Xatolik yuz berdi.")
            
    else:
        # Agar menyu tugmalari bo'lmasa, uni qo'shiq nomi deb hisoblaymiz
        excluded_texts = ["Biz haqimizda", "Xizmatlar", "Bog'lanish", "Sozlamalar", "Orqaga", "Bekor qilish", "Assalomu alaykum"]
        if text in excluded_texts:
            return

        # Qo'shiq qidirish
        status_msg = await message.answer(f"🔍 '{text}' qidirilmoqda (original variant)...")
        
        try:
            # YouTube'dan original audioni qidirib yuklash
            audio_path = await download_youtube_audio(text)
            
            if audio_path:
                audio_size = get_file_size_mb(audio_path)
                MAX_SIZE_MB = 100
                
                if audio_size > MAX_SIZE_MB:
                    await status_msg.edit_text(f"⚠️ Qo'shiq juda katta ({audio_size:.1f} MB).")
                else:
                    await status_msg.edit_text("🎵 Original audio topildi, yuborilmoqda...")
                    audio_file = FSInputFile(audio_path)
                    await message.answer_audio(
                        audio_file,
                        caption=f"✅ '{text}' qo'shig'ining original varianti."
                    )
                    await status_msg.delete()
            else:
                await status_msg.edit_text("❌ Afsuski, bu qo'shiqning original variantini topa olmadim.")
                
            # Faylni tozalash
            cleanup_files(audio_path)
            
        except Exception as e:
            logger.error(f"YouTube search handler xatolik: {e}")
            await status_msg.edit_text("❌ Qidiruvda xatolik yuz berdi.")




# MAIN


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("Siz klaviatura orqali dasturni to'xtatdingiz!\nGoodbye!")
