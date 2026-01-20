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

            logger.info(f"ANALIZ: track={track}, artist={artist}, title={title}, query={song_query}")

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
            
            # Audio fayl nomini aniqlash
            expected_audio = os.path.join(output_dir, f"{info['id']}_audio.mp3")
            
            try:
                with yt_dlp.YoutubeDL(audio_opts) as ydl_a:
                    ydl_a.download([url])
                    if os.path.exists(expected_audio):
                        audio_path = expected_audio
            except Exception as ae:
                logger.error(f"Direct audio download error: {ae}")

            # Agar direct audio bo'lmasa yoki fayl yaratilmagan bo'lsa - videodan ajratamiz
            if not audio_path or not os.path.exists(audio_path):
                if video_path and os.path.exists(video_path):
                    logger.info("Extracting audio from video file...")
                    audio_path = os.path.join(output_dir, f"{info['id']}_extracted.mp3")
                    import subprocess
                    # Windowsda panjara va boshqa simvollarni to'g'ri ishlash uchun list formatida yuboramiz
                    try:
                        subprocess.run([
                            'ffmpeg', '-i', video_path, 
                            '-vn', '-ar', '44100', '-ac', '2', '-b:a', '192k', 
                            audio_path, '-y'
                        ], capture_output=True, check=True)
                    except Exception as fe:
                        logger.error(f"FFmpeg extraction failed: {fe}")
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
        q = query.strip()
        search_variants = [f"{q} audio", f"{q} song", q]
        
        # Qidiruv variantlarini yig'amiz
        all_entries = []
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'nocheckcertificate': True}) as ydl:
            for sv in search_variants:
                try:
                    info = ydl.extract_info(f"ytsearch5:{sv}", download=False)
                    if info and 'entries' in info:
                        all_entries.extend([e for e in info['entries'] if e])
                except: continue
        
        if not all_entries: return None, None, None

        # unique entries
        unique_entries = {e['id']: e for e in all_entries}.values()
        
        def rate_entry(e):
            score = 0
            title = e.get('title', '').lower()
            uploader = e.get('uploader', '').lower()
            duration = e.get('duration', 0)
            
            # Duration score (ideal 2-5 mins)
            if 120 <= duration <= 360: score += 50
            elif 60 <= duration <= 600: score += 20
            
            # Title keywords score
            if any(k in title for k in ['official', 'original', 'full', 'audio']): score += 30
            if 'remix' in title: score -= 20
            if 'live' in title: score -= 10
            
            # Channel keywords score
            if any(k in uploader for k in ['official', 'vevo', 'topic', 'music']): score += 40
            
            # Query match score
            q_words = q.lower().split()
            match_count = sum(1 for w in q_words if w in title or w in uploader)
            score += (match_count / len(q_words)) * 50 if q_words else 0
            
            return score

        sorted_entries = sorted(unique_entries, key=rate_entry, reverse=True)

        for entry in list(sorted_entries)[:10]: # 10 tagacha sinab ko'ramiz
            video_id = entry['id']
            # Format tanlashda juda keng doirani olamiz: 'ba/b' (best audio yoki eng yaxshi video+audio)
            final_opts = {
                'format': 'bestaudio/best', # Avval audioni prob qilamiz
                'outtmpl': os.path.join(output_dir, f'{video_id}_yt.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
            }
            
            try:
                logger.info(f"YTDL: {video_id} ni yuklashga harakat...")
                with yt_dlp.YoutubeDL(final_opts) as ydl_final:
                    # Agar birinchi urinish (bestaudio) o'xshamasa, 'best' ni prob qilamiz
                    try:
                        ydl_final.download([f"https://www.youtube.com/watch?v={video_id}"])
                    except:
                        logger.info(f"YTDL: {video_id} ni 'best' formatda prob qilyapmiz...")
                        final_opts['format'] = 'best'
                        with yt_dlp.YoutubeDL(final_opts) as ydl_fallback:
                            ydl_fallback.download([f"https://www.youtube.com/watch?v={video_id}"])

                # Faylni tekshirish
                expected_mp3 = os.path.join(output_dir, f"{video_id}_yt.mp3")
                if not os.path.exists(expected_mp3):
                    for f in os.listdir(output_dir):
                        if f.startswith(video_id) and (f.endswith(".mp3") or f.endswith(".m4a") or f.endswith(".mp4")):
                            # Agar mp3 bo'lmasa lekin video kelsa, uni konvertatsiya qilamiz
                            actual_file = os.path.join(output_dir, f)
                            if not f.endswith(".mp3"):
                                expected_mp3 = os.path.splitext(actual_file)[0] + ".mp3"
                                import subprocess
                                subprocess.run(f'ffmpeg -i "{actual_file}" -vn -ar 44100 -ac 2 -b:a 192k "{expected_mp3}" -y', shell=True, capture_output=True)
                            else:
                                expected_mp3 = actual_file
                            break
                
                if os.path.exists(expected_mp3) and os.path.getsize(expected_mp3) > 1000:
                    raw_title = entry.get('title', 'Unknown')
                    uploader = entry.get('uploader', 'Unknown')
                    artist, title = uploader.replace(' - Topic', ''), raw_title
                    if " - " in raw_title:
                        p = raw_title.split(" - ", 1)
                        artist, title = p[0].strip(), p[1].strip()
                    
                    for junk in [r'\(official.*?\)', r'\[official.*?\]', r'audio', r'video', r'clip', r'klip', r'full', r'original']:
                        title = re.sub(junk, '', title, flags=re.IGNORECASE).strip()
                        artist = re.sub(junk, '', artist, flags=re.IGNORECASE).strip()
                    
                    return expected_mp3, title, artist
            except Exception as e:
                logger.warning(f"Failed {video_id}: {e}")
                continue
                
        return None, None, None
    except Exception as e:
        logger.error(f"Global download error: {e}")
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
