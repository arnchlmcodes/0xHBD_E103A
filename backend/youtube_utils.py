import os
import requests
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def search_youtube_videos(query, max_results=6):
    """
    Search YouTube for a specific query.
    Returns a list of video dictionaries.
    """
    if not YOUTUBE_API_KEY:
        print("Error: YOUTUBE_API_KEY not found in .env file.")
        return []

    print(f"Searching YouTube for: '{query}'...")
    
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        'part': 'snippet',
        'q': query,
        'type': 'video',
        'key': YOUTUBE_API_KEY,
        'maxResults': max_results,
        'relevanceLanguage': 'en',
        'videoEmbeddable': 'true',
        'safeSearch': 'moderate'
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        videos = []
        for item in data.get('items', []):
            video_id = item['id']['videoId']
            snippet = item['snippet']
            
            video = {
                'id': video_id,
                'title': snippet['title'],
                'description': snippet['description'],
                'thumbnail': snippet['thumbnails']['medium']['url'],
                'channel': snippet['channelTitle'],
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'embed_url': f"https://www.youtube.com/embed/{video_id}"
            }
            videos.append(video)
            
        return videos

    except requests.exceptions.HTTPError as e:
        print(f"YouTube API Error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return []
