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
        
        # Video yuklab olish uchun sozlamalar
        video_opts = {
            'format': 'best',
            'outtmpl': os.path.join(output_dir, '%(id)s_video.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        
        # Audio yuklab olish uchun sozlamalar
        audio_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_dir, '%(id)s_audio.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
        }
        
        video_path = None
        audio_path = None
        song_query = None
        
        # Video yuklab olish va ma'lumotlarni olish
        logger.info(f"Video yuklab olinmoqda: {url}")
        with yt_dlp.YoutubeDL(video_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_filename = ydl.prepare_filename(info)
            if os.path.exists(video_filename):
                video_path = video_filename
                logger.info(f"Video yuklandi: {video_path}")
            
            # Qo'shiq ma'lumotlarini chiqarish
            track = info.get('track')
            artist = info.get('artist')
            if track and artist:
                song_query = f"{artist} - {track}"
            elif track:
                song_query = track
            elif info.get('title') and "Instagram video" not in info.get('title'):
                song_query = info.get('title')

        # Audio yuklab olish
        logger.info(f"Audio yuklab olinmoqda: {url}")
        with yt_dlp.YoutubeDL(audio_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # Audio fayl nomini topish (.mp3 kengaytmasi bilan)
            base_filename = ydl.prepare_filename(info)
            audio_filename = os.path.splitext(base_filename)[0] + '.mp3'
            
            if os.path.exists(audio_filename):
                audio_path = audio_filename
                logger.info(f"Audio yuklandi: {audio_path}")
        
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
