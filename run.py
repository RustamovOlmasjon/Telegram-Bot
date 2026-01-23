import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from config import TOKEN

# Keyboards faylidan klaviaturalarni import qilamiz
from keyboards import (
    main_menu_keyboard,       # Asosiy menyu tugmalari
)

# Instagram downloader modulini import qilamiz
from instagram_downloader import (
    is_instagram_url,
    download_instagram_content,
    download_youtube_audio,
    download_batch_youtube_audio,
    cleanup_files,
    get_file_size_mb
)

bot = Bot(token=TOKEN)
dp = Dispatcher()
logger = logging.getLogger(__name__)



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
    """
    await help_button_handler(message)



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
            # Video, audio va qo'shiq metadata yuklab olish
            video_path, audio_path, song_query = await download_instagram_content(text)
            
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
                if video_size <= MAX_SIZE_MB:
                    await status_msg.edit_text("📹 Video yuborilmoqda...")
                    await message.answer_video(FSInputFile(video_path), caption="✅ Instagram video")
            
            # Audio yuborish (Instagram'dan olingan variant)
            if audio_path:
                audio_size = get_file_size_mb(audio_path)
                if audio_size <= MAX_SIZE_MB:
                    await status_msg.edit_text("🎵 Audio yuborilmoqda...")
                    ig_title = song_query if song_query else "Instagram Audio"
                    await message.answer_audio(
                        FSInputFile(audio_path),
                        title=ig_title,
                        performer="Instagram",
                        caption=f"✅ Instagram audio"
                    )
            
            # ORIGINAL VARIANT qidiruv (agar metadata topilgan bo'lsa)
            yt_path = None
            if song_query:
                await status_msg.edit_text(f"🔍 '{song_query}' qo'shig'ining to'liq versiyasini YouTube'dan qidiryapman...")
                yt_path, yt_title, yt_artist = await download_youtube_audio(song_query)
                
                if yt_path:
                    yt_size = get_file_size_mb(yt_path)
                    if yt_size <= MAX_SIZE_MB:
                        await message.answer_audio(
                            FSInputFile(yt_path),
                            title=yt_title,
                            performer=yt_artist,
                            caption=f"🎧 '{song_query}'ning to'liq versiyasi."
                        )
            
            # Muvaffaqiyatli xabar
            await status_msg.edit_text("✅ Tayyor! Sizga kerakli barcha fayllar yuborildi.")
            
            # Vaqtinchalik fayllarni o'chirish
            cleanup_files(video_path, audio_path, yt_path)
            
        except Exception as e:
            logger.error(f"Instagram handler xatolik: {e}")
            await status_msg.edit_text("❌ Xatolik yuz berdi.")
            
    else:
        # Menyu tugmalariga javob berishni to'xtatish
        excluded_texts = ["ℹ️ Yordam", "Biz haqimizda", "Xizmatlar", "Bog'lanish", "Sozlamalar", "Orqaga", "Bekor qilish", "Assalomu alaykum"]
        if text.strip() in excluded_texts:
            return

        # Maxsus holat: Asl Wayne (19 ta qo'shiq)
        is_asl_wayne = "asl way" in text.lower()
        limit = 19 if is_asl_wayne else 10
        
        status_msg = await message.answer(f"🔍 '{text}' bo'yicha eng sara {limit} ta qo'shiq qidirilmoqda...")
        
        try:
            # YouTube'dan bir nechta audiolarni yuklash
            results = await download_batch_youtube_audio(text, limit=limit)
            
            if results:
                await status_msg.edit_text(f"🎵 {len(results)} ta qo'shiq topildi. Yuborilmoqda...")
                
                for path, title, artist in results:
                    try:
                        audio_size = get_file_size_mb(path)
                        if audio_size <= 100:
                            await message.answer_audio(
                                FSInputFile(path),
                                title=title,
                                performer=artist,
                                caption=f"✅ {artist} - {title}"
                            )
                    except Exception as send_err:
                        logger.error(f"Error sending batch audio: {send_err}")
                    
                    # Har bir faylni yuborgandan so'ng o'chirish (joy tejash uchun)
                    cleanup_files(path)
                
                await status_msg.edit_text(f"✅ Tayyor! {len(results)} ta qo'shiq yuborildi.")
            else:
                await status_msg.edit_text(
                    f"❌ Kechirasiz, '{text}' bo'yicha qo'shiqlar topilmadi.\n\n"
                    "💡 **Maslahat:** Ismni to'g'ri yozganingizga ishonch hosil qiling."
                )
                
        except Exception as e:
            logger.error(f"Batch search handler error: {e}")
            await status_msg.edit_text("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")




# MAIN


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("Siz klaviatura orqali dasturni to'xtatdingiz!\nGoodbye!")
