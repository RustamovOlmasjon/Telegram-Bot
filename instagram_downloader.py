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
            is_original_audio = False
            for forbidden in ["original audio", "original music", "originalniy zvuk", "asl audio"]:
                if song_query and forbidden in song_query.lower():
                    is_original_audio = True
                    break
            
            if is_original_audio:
                # Agar faqat "Original audio" bo'lsa, uni qidirish foydasiz
                # Lekin foydalanuvchi uploader orqali topishni xohlashi mumkin
                if uploader:
                    song_query = f"{uploader} yangi klip"
                else:
                    song_query = None

            # Sarlavhani tahlil qilish (Agar hali ham yo'q bo'lsa)
            if not song_query and title:
                clean_title = re.sub(r'Instagram (?:video|reel|reels|post|TV).*', '', title, flags=re.IGNORECASE).strip()
                clean_title = re.sub(r'#\w+|@\w+|https?://\S+|www\.\S+', '', clean_title).strip()
                if clean_title and len(clean_title) > 5:
                    song_query = clean_title
            
            # Agar juda qisqa bo'lsa yoki topilmasa, uploader fallback
            if not song_query and uploader:
                clean_uploader = re.sub(r'[\._]', ' ', uploader).strip()
                song_query = f"{clean_uploader} qo'shiq"

            logger.info(f"ANALIZ: track={track}, artist={artist}, query={song_query}")

            # 2. Video yuklab olish
            video_opts = {
                **base_opts,
                'outtmpl': os.path.join(output_dir, '%(id)s_video.%(ext)s'),
            }
            with yt_dlp.YoutubeDL(video_opts) as ydl_v:
                ydl_v.download([url])
                # Fayl yo'lini aniq topish
                video_filename = ydl_v.prepare_filename(info)
                if not os.path.exists(video_filename):
                    actual_dir = os.path.dirname(video_filename)
                    basename = os.path.splitext(os.path.basename(video_filename))[0]
                    for f in os.listdir(actual_dir):
                        if f.startswith(basename):
                            video_path = os.path.join(actual_dir, f)
                            break
                else:
                    video_path = video_filename

            # 3. Audio yuklab olish (Guaranteed)
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
            try:
                with yt_dlp.YoutubeDL(audio_opts) as ydl_a:
                    ydl_a.download([url])
                    base_audio = ydl_a.prepare_filename(info)
                    audio_path = os.path.splitext(base_audio)[0] + '.mp3'
                    if not os.path.exists(audio_path):
                        # Agar topilmasa, videodan ajratamiz
                        if video_path and os.path.exists(video_path):
                            logger.info("Direct audio download failed, extracting from video...")
                            audio_path = os.path.splitext(video_path)[0] + ".mp3"
                            import subprocess
                            cmd = f'ffmpeg -i "{video_path}" -vn -ar 44100 -ac 2 -b:a 192k "{audio_path}" -y'
                            subprocess.run(cmd, shell=True, capture_output=True)
            except Exception as ae:
                logger.error(f"Audio download error: {ae}")
                if video_path and os.path.exists(video_path):
                    audio_path = os.path.splitext(video_path)[0] + ".mp3"
                    import subprocess
                    cmd = f'ffmpeg -i "{video_path}" -vn -ar 44100 -ac 2 -b:a 192k "{audio_path}" -y'
                    subprocess.run(cmd, shell=True, capture_output=True)
        
        # Yakuniy tekshiruv
        if audio_path and not os.path.exists(audio_path):
            audio_path = None
            
        return video_path, audio_path, song_query
        
    except Exception as e:
        logger.error(f"Instagram yuklab olishda xatolik: {e}")
        return None, None, None


async def download_youtube_audio(query: str, output_dir: str = "downloads") -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    YouTube'dan qidiruv bo'yicha audio faylni yuklab olish (100% natija uchun)
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # Qidiruv so'zini tozalash va boyitish
        clean_query = query.strip()
        search_variants = [
            f"{clean_query} official audio full",
            f"{clean_query} original audio",
            clean_query
        ]
        
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
            'noplaylist': True,
            'ignoreerrors': True,
            'nocheckcertificate': True,
        }

        best_entry = None
        all_entries = []

        for sv in search_variants:
            logger.info(f"YouTube searching variant: {sv}")
            with yt_dlp.YoutubeDL(audio_opts) as ydl:
                info = ydl.extract_info(f"ytsearch5:{sv}", download=False)
                if info and 'entries' in info:
                    entries = [e for e in info['entries'] if e]
                    all_entries.extend(entries)
                    
                    # Davomiylikka qarab saralash (120-400 sekund ideal)
                    for e in entries:
                        d = e.get('duration', 0)
                        if 120 < d < 480: # To'liq qo'shiq
                            best_entry = e
                            break
                if best_entry: break

        # Agar ideal topilmasa, eng yaxshi alternativani olamiz
        if not best_entry and all_entries:
            # Short (shorths) bo'lmagan birinchisini olamiz
            for e in all_entries:
                if e.get('duration', 0) > 60:
                    best_entry = e
                    break
            # Agar hammasi short bo'lsa, shunchaki birinchisini olamiz
            if not best_entry:
                best_entry = all_entries[0]

        if not best_entry:
            return None, None, None

        # Haqiqiy yuklab olish
        url = best_entry.get('webpage_url') or f"https://www.youtube.com/watch?v={best_entry['id']}"
        with yt_dlp.YoutubeDL(audio_opts) as ydl:
            logger.info(f"Downloading chosen audio: {url}")
            download_info = ydl.extract_info(url, download=True)
            audio_path = ydl.prepare_filename(download_info)
            audio_path = os.path.splitext(audio_path)[0] + '.mp3'
            
            if os.path.exists(audio_path):
                # Metadata tozalash
                raw_title = download_info.get('title', 'Unknown Title')
                uploader = download_info.get('uploader', 'Unknown Artist')
                
                title = raw_title
                artist = uploader.replace(' - Topic', '')
                
                if " - " in raw_title:
                    parts = raw_title.split(" - ", 1)
                    artist = parts[0].strip()
                    title = parts[1].strip()
                
                # Keraksiz so'zlarni artish
                junk_patterns = [
                    r'\(official.*?\)', r'\[official.*?\]', r'\|.*?official.*',
                    r'audio', r'video', r'clip', r'klip', r'hd', r'4k', r'full', r'original'
                ]
                for p in junk_patterns:
                    title = re.sub(p, '', title, flags=re.IGNORECASE).strip()
                    artist = re.sub(p, '', artist, flags=re.IGNORECASE).strip()
                
                return audio_path, title, artist
                
        return None, None, None
    except Exception as e:
        logger.error(f"Enhanced YouTube search error: {e}")
        return None, None, None
        
    except Exception as e:
        logger.error(f"YouTube yuklab olishda xatolik: {e}")
        return None, None, None


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
