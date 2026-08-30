import urllib.parse
import webbrowser
import requests
import re

def play_youtube(query):
    """Search and auto-open YouTube video or song in browser"""
    if not query:
        query = "Uzbek music"

    search_encoded = urllib.parse.quote(query)
    search_url = f"https://www.youtube.com/results?search_query={search_encoded}"

    try:
        # Try fetching first video ID directly from YouTube search HTML
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
        response = requests.get(search_url, headers=headers, timeout=4)
        if response.status_code == 200:
            video_ids = re.findall(r"watch\?v=(\w{11})", response.text)
            if video_ids:
                first_video_url = f"https://www.youtube.com/watch?v={video_ids[0]}&autoplay=1"
                webbrowser.open(first_video_url)
                return True, f"Youtubedan '{query}' qo'shig'i ijro etilmoqda."
    except Exception:
        pass

    # Fallback to search results page
    webbrowser.open(search_url)
    return True, f"Youtubedan '{query}' bo'yicha qidiruv natijalari ochildi."
