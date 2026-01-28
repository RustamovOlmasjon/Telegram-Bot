import asyncio
import logging
from instagram_downloader import download_batch_youtube_audio

async def test():
    logging.basicConfig(level=logging.INFO)
    query = "Sherali Jo'rayev"
    print(f"Testing batch download for: {query}")
    results = await download_batch_youtube_audio(query, limit=10)
    print(f"Found {len(results)} results")
    for i, (path, title, artist) in enumerate(results):
        print(f"{i+1}. {artist} - {title} ({path})")

if __name__ == "__main__":
    asyncio.run(test())
