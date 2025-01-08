import os
import json
import random
import requests

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

    def save_playlist_to_json(data: Dict[int, Dict[str, Any]], file_path: str):
        # Convert the structure to a serializable format
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def load_cards(filePath : str):
    # Load cards from the JSON file
        try:
            with open(filePath, 'r', encoding='utf-8') as file:
                cards = json.load(file)
            
            # Clean card names by removing U+202C
            for card in cards:
                card['card_name'] = card['card_name'].replace('\u202c', '')  # Remove U+202C

            return cards
        except FileNotFoundError:
            print("Warning: 'cards.json' not found. Returning an empty list.")
            return []  # Return an empty list if the file does not exist
        except json.JSONDecodeError:
            print("Error: 'cards.json' is not a valid JSON file. Returning an empty list.")
            return []  # Return an empty list if the JSON is invalid
        except Exception as e:
            print(f"An error occurred while loading cards: {e}")
            return []  # Return an empty list for any other exceptions

    def save_cards(cards, filePath : str):
        # Save cards to the JSON file
        try:
            with open(filePath, 'w', encoding='utf-8') as file:
                json.dump(cards, file, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"An error occurred while saving cards: {e}")
   
