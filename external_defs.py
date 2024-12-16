import os
import json
import requests


from typing import Dict
from collections import deque
from dotenv import load_dotenv

class ExternalDefs():
    load_dotenv()

    def initialize():
        load_dotenv()


    def load_playlist_from_json(file_path: str) -> Dict[int, deque]:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                return {int(k): deque(v) for k, v in data.items()}
        except FileNotFoundError:
            return {}

    def save_playlist_to_json(playlists: Dict[int, deque], file_path: str):
        # Convert deques to lists for JSON serialization
        serializable_data = {str(k): list(v) for k, v in playlists.items()}
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, indent=4, ensure_ascii=False)

    def get_lyrics(song_title, artist):
        GENIUS_TOKEN = os.getenv("GENIUS_TOKEN") 

        url = "https://api.genius.com/search"
        headers = {
            "Authorization": f"Bearer {GENIUS_TOKEN}"
        }
        params = {
            "q": f"{song_title} {artist}"  # Query with song title and artist
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            hits = data['response']['hits']
            if hits:
                song_url = hits[0]['result']['url']
                return song_url
            else:
                return "No lyrics found."
        else:
            return f"Error: {response.status_code}"
