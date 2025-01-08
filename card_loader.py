import os
import json
import random
import requests

from dotenv import load_dotenv


class CardLoader():
    load_dotenv()

    def initialize():
        load_dotenv()
        load_pokemon_cards()
        load_meme_cards()
        load_cat_cards()
        load_anime_cards()




COLORS = {
    4 : "RED",
    3 : "BLUE",
    2 : "PURPLE",
    1 : "GREEN",
    0 : "RAINBOW"
}

COST = {
    "RED" : 50,
    "BLUE" : 250,
    "PURPLE" : 500,
    "GREEN" : 750,
    "RAINBOW": 1000,
}
def ensure_unicode(text):
    if isinstance(text, bytes):
        return text.decode('utf-8')
    return text

def load_cards():
    # Load cards from the JSON file
    try:
        with open('cards.json', 'r', encoding='utf-8') as file:
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

def save_cards(cards):
    # Save cards to the JSON file
    try:
        with open('cards.json', 'w', encoding='utf-8') as file:
            json.dump(cards, file, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"An error occurred while saving cards: {e}")

def load_pokemon_cards():
    cards = []
    numbers = {
        928,
        691,
        304,
        628,
        519,
        406,
        483,
        458,
        382,
        555,
        314,
        681,
        959,
        762,
        40,
        100,
        788,
        116,
        410,
        76,
        954,
        840,
        912,
        74,
        864
    }
    counter = 1
    for id in numbers:
        url = f"https://pokeapi.co/api/v2/pokemon/{id}"
        

        response = requests.get(url)
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            

            card_color = COLORS[random.choice(list(COLORS.keys()))]  # Randomly assign a color
            
            cards.append({
                "card_name": data['name'].capitalize(),
                "card_number": f"#{counter:03}",
                "card_url": data['sprites']['front_default'],
                "card_color": card_color,  # Use the assigned color
                "cost": COST[card_color]  # Get cost based on the assigned color
            })
            counter = counter + 1
            save_cards(cards=cards)
        else:
            print(f"Error: Unable to fetch data for. Status code: {response.status_code}")

def load_meme_cards():
    print("Entering load_meme_cards function...")  # Debugging output
    cards = []
    counter = 26  # Start counter from 1 for numbering
    total_memes_needed = 25  # Total number of memes to fetch

    # Load existing cards to preserve them
    existing_cards = load_cards()  # Load existing cards from the JSON file
    cards.extend(existing_cards)  # Add existing cards to the new cards list

    # Create a set of existing card names for quick duplicate checking
    existing_card_names = {card['card_name'] for card in existing_cards}

    # Debugging output to check the number of existing cards
    print(f"Number of existing cards: {len(existing_cards)}")  

    while len(cards) < total_memes_needed + 25:
        url = "https://meme-api.com/gimme/1"  # Updated URL for fetching memes
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            
            if 'memes' in data:
                for meme in data['memes']:  # Iterate over the memes in the response
                    card_color = COLORS[random.choice(list(COLORS.keys()))]  # Randomly assign a color
                    
                    new_card = {
                        "card_name": meme['title'].capitalize(),  # Ensure the title is used correctly
                        "card_number": f"#{counter:03}",
                        "card_url": meme['url'],  # Use the URL from the meme data
                        "card_color": card_color,  # Use the assigned color
                        "cost": COST[card_color]  # Get cost based on the assigned color
                    }
                    
                    # Check for duplicates before adding
                    if new_card['card_name'] not in existing_card_names:
                        cards.append(new_card)
                        existing_card_names.add(new_card['card_name'])  # Add to the set of existing names
                        counter += 1
                        save_cards(cards=cards)
                    
                    # Stop if we have enough cards
                    if len(cards) >= total_memes_needed:
                        break
        else:
            break  # Exit the loop if there's an error

    # Update the debug statement to reflect the actual number of loaded meme cards
    print(f"Loaded {len(cards) - len(existing_cards)} meme cards.")  # Debugging statement

def load_cat_cards():
    cards = []
    counter = 51
    cat_counter = 0

    # Load existing cards to preserve them
    existing_cards = load_cards()  # Load existing cards from the JSON file
    cards.extend(existing_cards)  # Add existing cards to the new cards list

    for _ in range(25):  # Iterate 25 times to fetch 25 cat images
        url = f"https://api.thecatapi.com/v1/images/search"  # Move URL inside the loop
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            for cat in data:  # Iterate over the cat images in the response
                card_color = COLORS[random.choice(list(COLORS.keys()))]  # Randomly assign a color
                new_card = {
                    "card_name": f"CAT {cat_counter}",
                    "card_number": f"#{counter:03}",
                    "card_url": cat['url'],
                    "card_color": card_color,  # Use the assigned color
                    "cost": COST[card_color]  # Get cost based on the assigned color
                }
                
                # Check for duplicates before adding
                if new_card not in cards:
                    cards.append(new_card)
                    counter += 1
                    cat_counter += 1
            
            
            # Save all cards (existing + new) after processing
            save_cards(cards=cards)  
        else:
            print(f"Error: Unable to fetch data for cats. Status code: {response.status_code}")

    print(f"Loaded {cat_counter} cat cards.")  # Debugging statement

def load_anime_cards():
    cards = []
    counter = 76
    anime_names = [
        "Your Lie in April",
        "Kimetsu No Yaiba",
        "Jujutsu Kaisen",
        "Vinland Saga",
        "Attack on Titan"
    ]
    query = '''
    query ($search: String) {
      Page {
        media(search: $search) {
          characters {
            edges {
              node {
                id
                name {
                  full
                }
                image {
                  large
                }
              }
            }
          }
        }
      }
    }
    '''
    # Load existing cards to preserve them
    existing_cards = load_cards()  # Load existing cards from the JSON file
    cards.extend(existing_cards)  # Add existing cards to the new cards list


    for anime in anime_names:
        url = f"https://graphql.anilist.co"  # Move URL inside the loop
        variables = {'search': anime}
        response = requests.post(url, json={'query': query, 'variables': variables})
        
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()['data']['Page']['media']
            if data:  # Check if data is not empty
                characters = data[0]['characters']['edges']

                random.shuffle(characters)
                # Limit to 5 characters
                for character in characters[:5]:  # Get only the first 5 characters
                    card_color = COLORS[random.choice(list(COLORS.keys()))]  # Randomly assign a color
                    new_card = {
                        "card_name": f"{character['node']['name']['full']}",
                        "card_number": f"#{counter:03}",
                        "card_url": f"{character['node']['image']['large']}",
                        "card_color": card_color,  # Use the assigned color
                        "cost": COST[card_color]  # Get cost based on the assigned color
                    }
                    
                    # Check for duplicates before adding
                    if new_card not in cards:
                        cards.append(new_card)
                        counter += 1
                
        else:
            print(f"Error: Unable to fetch data for anime '{anime}'. Status code: {response.status_code}")

    # Save all cards (existing + new) after processing
    save_cards(cards=cards)  
    print(f"Loaded {0} anime cards.")  # Debugging statement

    
load_pokemon_cards()
load_meme_cards()
load_cat_cards()
load_anime_cards()


