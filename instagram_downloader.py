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
        r'https?://(?:www\.)?instagram\.com/(?:p|reel|reels|tv)/[\w-]+/?',
        r'https?://(?:www\.)?instagram\.com/[\w.-]+/(?:p|reel|reels|tv)/[\w-]+/?',
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
            'ignoreerrors': True,
        }
        
        video_path = None
        audio_path = None
        song_query = None
        
        # 1. Ma'lumotlarni bir marta olish
        with yt_dlp.YoutubeDL(base_opts) as ydl:
            logger.info(f"Instagram ma'lumotlari olinmoqda: {url}")
            info = ydl.extract_info(url, download=False)
            
            if not info:
                return None, None, None

            # Qo'shiq ma'lumotlarini qidirish (Agressiv usul)
            track = info.get('track')
            artist = info.get('artist')
            creator = info.get('creator')
            uploader = info.get('uploader')
            alt_title = info.get('alt_title')
            description = info.get('description', '')
            title = info.get('title', '')
            tags = info.get('tags', [])
            
            # To'g'ridan-to'g'ri metadata bo'lsa (Eng ishonchli)
            if track and artist:
                song_query = f"{artist} - {track}"
            elif track:
                song_query = track
            elif alt_title:
                song_query = alt_title
            
            # Tavsifdan regex orqali qidirish
            if not song_query and description:
                patterns = [
                    r'(?:Music|Song|Musiqa|Trek|Nomi):\s*([^\n|]+)',
                    r'🎵\s*([^\n|]+)',
                    r'🎧\s*([^\n|]+)',
                    r'🎤\s*([^\n|]+)'
                ]
                for pattern in patterns:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        song_query = match.group(1).strip()
                        break
            
            # Keraksiz generic nomlarni filtrlash
            for forbidden in ["original audio", "original music", "originalniy zvuk", "asl audio"]:
                if song_query and forbidden in song_query.lower():
                    song_query = None
                    break

            # Sarlavhani tahlil qilish (Agar hali ham yo'q bo'lsa)
            if not song_query and title:
                # Instagram video/reel yozuvlarini va keraksiz belgilarni olib tashlaymiz
                clean_title = re.sub(r'Instagram (?:video|reel|reels|post|TV).*', '', title, flags=re.IGNORECASE).strip()
                clean_title = re.sub(r'#\w+|@\w+|https?://\S+|www\.\S+', '', clean_title).strip() # Hashtag, mention va linklarni olib tashlash
                if clean_title and len(clean_title) > 5:
                    song_query = clean_title
            
            # Teaglardan qidirish
            if not song_query and tags:
                music_tags = [t for t in tags if any(word in t.lower() for word in ['music', 'song', 'audio', 'cover'])]
                if music_tags:
                    song_query = music_tags[0]

            # Agar juda qisqa bo'lsa yoki topilmasa, uploader + title fallback (eng oxirgi chora)
            if not song_query and uploader:
                # Uploader nomidan ba'zi qismlarni olamiz
                clean_uploader = re.sub(r'[\._]', ' ', uploader).strip()
                song_query = f"{clean_uploader} yangi tarona"

            logger.info(f"YUNALISH: track={track}, artist={artist}, query={song_query}")

            # 2. Video yuklab olish
            video_opts = {
                **base_opts,
                'outtmpl': os.path.join(output_dir, '%(id)s_video.%(ext)s'),
            }
            with yt_dlp.YoutubeDL(video_opts) as ydl_v:
                ydl_v.download([url])
                video_filename = ydl_v.prepare_filename(info)
                if os.path.exists(video_filename):
                    video_path = video_filename
                else:
                    # Kengaytmani tekshirish (.mp4, .mov, .mkv)
                    actual_dir = os.path.dirname(video_filename)
                    basename = os.path.splitext(os.path.basename(video_filename))[0]
                    for f in os.listdir(actual_dir):
                        if f.startswith(basename):
                            video_path = os.path.join(actual_dir, f)
                            break

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
    YouTube'dan qidiruv bo'yicha eng mos TO'LIQ audio faylni yuklab olish
    
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
            'default_search': 'ytsearch1', # Eng yaxshi natijani olish
            'noplaylist': True,
            # TO'LIQ VERSIONI topish uchun filtrlar
            'match_filter': yt_dlp.utils.match_filter_func("duration > 60 & !is_live"),
            'ignoreerrors': True,
        }
        
        logger.info(f"YouTube'da TO'LIQ audio qidirilmoqda: {query}")
        with yt_dlp.YoutubeDL(audio_opts) as ydl:
            # ytsearch: orqali qidirish
            info = ydl.extract_info(f"ytsearch:{query}", download=True)
            
            if not info or 'entries' not in info or len(info['entries']) == 0:
                # Agar 60s dan kattalari topilmasa, cheklovsiz qidirib ko'ramiz
                logger.info(f"Yirik versiya topilmadi, cheklovsiz qidirilmoqda: {query}")
                audio_opts.pop('match_filter', None)
                with yt_dlp.YoutubeDL(audio_opts) as ydl_retry:
                    info = ydl_retry.extract_info(f"ytsearch:{query}", download=True)

            if info and 'entries' in info and len(info['entries']) > 0:
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
