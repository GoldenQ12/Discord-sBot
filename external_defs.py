import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from bs4 import BeautifulSoup  # Add this import


class ExternalDefs():
    load_dotenv()

    def initialize():
        load_dotenv()

    def load_playlist_from_json(file_path: str) -> Dict[int, Dict[str, Any]]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ensure the structure matches the expected format
                return {k: v for k, v in data.items()}  # Keep the original structure
        except FileNotFoundError:
            return {}

    def save_playlist_to_json(playlists: Dict[int, Dict[str, Any]], file_path: str):
        # Convert the structure to a serializable format
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(playlists, f, indent=4, ensure_ascii=False)

   
