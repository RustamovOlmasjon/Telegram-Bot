import asyncio
from instagram_downloader import download_youtube_audio, download_instagram_content
import logging

logging.basicConfig(level=logging.INFO)

async def test():
    print("Testing YouTube download...")
    path, title, artist = await download_youtube_audio("Janob Rasul Gulyuzim")
    print(f"YouTube Result: {path}, {title}, {artist}")
    
    print("\nTesting Instagram download...")
    # Using a known public reel for testing if possible, or just checking if it fails gracefully
    url = "https://www.instagram.com/reels/C2f9l4vM8zP/" # Example
    v_path, a_path, query = await download_instagram_content(url)
    print(f"Instagram Result: {v_path}, {a_path}, {query}")

if __name__ == "__main__":
    asyncio.run(test())
