"""
Instagram Downloader Module
Instagram'dan video va audio yuklab olish uchun modul
"""

import os
import re
import yt_dlp
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def is_instagram_url(url: str) -> bool:
    """
    URL Instagram linkimi tekshirish
    
    Args:
        url: Tekshiriladigan URL
        
    Returns:
        True agar Instagram link bo'lsa, aks holda False
    """
    instagram_patterns = [
        r'https?://(?:www\.)?instagram\.com/(?:p|reel|tv)/[\w-]+/?',
        r'https?://(?:www\.)?instagram\.com/[\w.-]+/(?:p|reel|tv)/[\w-]+/?',
    ]
    
    for pattern in instagram_patterns:
        if re.match(pattern, url):
            return True
    return False


async def download_instagram_content(url: str, output_dir: str = "downloads") -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Instagram'dan video va audio yuklab olish + qo'shiq ma'lumotlarini olish
    
    Args:
        url: Instagram video URL
        output_dir: Fayllarni saqlash uchun papka
        
    Returns:
        Tuple: (video_path, audio_path, song_query) yoki (None, None, None) xatolik bo'lsa
    """
    try:
        # Papkani yaratish
        os.makedirs(output_dir, exist_ok=True)
        
        # Umumiy sozlamalar (info olish uchun)
        base_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best',
        }
        
        video_path = None
        audio_path = None
        song_query = None
        
        # 1. Ma'lumotlarni bir marta olish
        with yt_dlp.YoutubeDL(base_opts) as ydl:
            logger.info(f"Instagram ma'lumotlari olinmoqda: {url}")
            info = ydl.extract_info(url, download=False)
            
            # Debug uchun barcha mavjud kalitlarni chiqarish (logda)
            logger.info(f"Mavjud metadata kalitlari: {list(info.keys())}")
            
            # Qo'shiq ma'lumotlarini qidirish
            track = info.get('track')
            artist = info.get('artist')
            alt_title = info.get('alt_title')
            description = info.get('description', '')
            title = info.get('title', '')
            
            if track and artist:
                song_query = f"{artist} - {track}"
            elif track:
                song_query = track
            elif alt_title:
                song_query = alt_title
            
            # Agar hali ham topilmasa, description dan qidiramiz
            if not song_query and description:
                # Instagram descriptionda ko'pincha "Music: Artist - Song" ko'rinishida bo'ladi
                music_match = re.search(r'(?:Music|Song|Musiqa):\s*([^\n|]+)', description, re.IGNORECASE)
                if music_match:
                    song_query = music_match.group(1).strip()
            
            # Oxirgi chora: title ni tekshirish (agar u generic bo'lmasa)
            if not song_query and title and "Instagram" not in title and "video" not in title.lower():
                song_query = title

            logger.info(f"Topilgan metadata: track={track}, artist={artist}, query={song_query}")

            # 2. Video yuklab olish
            video_opts = {
                **base_opts,
                'outtmpl': os.path.join(output_dir, '%(id)s_video.%(ext)s'),
            }
            with yt_dlp.YoutubeDL(video_opts) as ydl_v:
                ydl_v.download([url])
                video_path = ydl_v.prepare_filename(info)
                if not os.path.exists(video_path):
                    video_path = None

            # 3. Audio yuklab olish
            audio_opts = {
                **base_opts,
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(output_dir, '%(id)s_audio.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            with yt_dlp.YoutubeDL(audio_opts) as ydl_a:
                ydl_a.download([url])
                base_audio = ydl_a.prepare_filename(info)
                audio_path = os.path.splitext(base_audio)[0] + '.mp3'
                if not os.path.exists(audio_path):
                    audio_path = None
        
        return video_path, audio_path, song_query
        
    except Exception as e:
        logger.error(f"Instagram yuklab olishda xatolik: {e}")
        return None, None, None


async def download_youtube_audio(query: str, output_dir: str = "downloads") -> Optional[str]:
    """
    YouTube'dan qidiruv bo'yicha eng mos audio faylni yuklab olish
    
    Args:
        query: Qidiruv so'zi (qo'shiq nomi)
        output_dir: Fayllarni saqlash uchun papka
        
    Returns:
        Audio fayl yo'li yoki None xatolik bo'lsa
    """
    try:
        # Papkani yaratish
        os.makedirs(output_dir, exist_ok=True)
        
        # Audio yuklab olish uchun sozlamalar
        audio_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_dir, '%(id)s_yt.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch1', # Faqat 1-natijani olish
            'noplaylist': True,
        }
        
        logger.info(f"YouTube'da qidirilmoqda: {query}")
        with yt_dlp.YoutubeDL(audio_opts) as ydl:
            # ytsearch: orqali qidirish
            info = ydl.extract_info(f"ytsearch:{query}", download=True)
            
            if 'entries' in info and len(info['entries']) > 0:
                # Birinchi natijani olish
                info = info['entries'][0]
                
            base_filename = ydl.prepare_filename(info)
            audio_filename = os.path.splitext(base_filename)[0] + '.mp3'
            
            if os.path.exists(audio_filename):
                logger.info(f"YouTube'dan audio yuklandi: {audio_filename}")
                return audio_filename
                
        return None
        
    except Exception as e:
        logger.error(f"YouTube yuklab olishda xatolik: {e}")
        return None


def cleanup_files(*file_paths: str) -> None:
    """
    Vaqtinchalik fayllarni o'chirish
    
    Args:
        *file_paths: O'chiriladigan fayl yo'llari
    """
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Fayl o'chirildi: {file_path}")
            except Exception as e:
                logger.error(f"Faylni o'chirishda xatolik {file_path}: {e}")


def get_file_size_mb(file_path: str) -> float:
    """
    Fayl hajmini MB da olish
    
    Args:
        file_path: Fayl yo'li
        
    Returns:
        Fayl hajmi MB da
    """
    if file_path and os.path.exists(file_path):
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    return 0.0
