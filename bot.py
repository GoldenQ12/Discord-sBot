import discord
import os
import discord.interactions
from discord.ui.item import Item
import yt_dlp as youtube_dl
import spotipy
import asyncio
import random


from discord.ext import commands
from spotipy.oauth2 import SpotifyClientCredentials
from typing import Dict, Any
from dotenv import load_dotenv

from musicControls import MusicControls
from external_defs import ExternalDefs
from paginator import Paginator
# Load the .env file
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

#Spotify Setup
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET))

intents = discord.Intents.default()
intents.message_content = True  
intents.members = True

ytdl_format_options = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # IPv4 only
}

ffmpeg_options = {
    'options': '-vn -b:a 192k -bufsize 3072k',  # Add buffer size and adjust bitrate
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'  # Add reconnection options
}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

# Use commands.Bot instead of discord.Client
bot = commands.Bot(command_prefix='/', intents=intents)



# ? Playlist Dictionary => [int : Server, deque : Dict]
guild: Dict[int, Dict[str, Any]] = ExternalDefs.load_playlist_from_json('data.json')




current_track_start_time = {}
now_playing_messages = {}
external = ExternalDefs.initialize()
current_song = {}


def ensure_unicode(text):
    if isinstance(text, bytes):
        return text.decode('utf-8')
    return text

async def load_users():
    global guild 
    while True:
        for guild_id in guild:
            if not guild[str(guild_id)]['users'] :
                guild[str(guild_id)].append({"users" : []})
            currentMembers = guild[str(guild_id)]['users']
            users_id = []
            for member in currentMembers:
                users_id.append(member['id'])
            newMembers = await bot.get_guild(int(guild_id)).fetch_members().flatten()
            for member in newMembers:
                if member.id not in users_id:
                    guild[guild_id]['users'].append({
                        "id" : member.id,
                        "cards" : [],
                        "cards_count" : 0,
                        "level" : 1,
                        "currency" : 0                    
                    })
                else:
                    total_cards_count = sum(card['card_count'] for card in guild[guild_id]['users'][users_id.index(member.id)]['cards'])
                    guild[guild_id]['users'][users_id.index(member.id)]['cards_count'] = total_cards_count  # Update cards_count
        
        ExternalDefs.save_playlist_to_json(guild, 'data.json')
        await asyncio.sleep(60)
        



async def coins_increase():
    global guild
    while True:
        for guild_id in guild:
            users = guild[str(guild_id)]['users']
            for user in users:
                user['currency'] += 1
                ExternalDefs.save_playlist_to_json(guild, 'data.json')
        await asyncio.sleep(20) 
        #TODO DETERMINE HOW MANY TIME SHALL BE FOR THE COINS TO INCREASE ( MATHS RESOLVE ) 

async def shop_setup():
    global guild
    day = 86400
    await asyncio.sleep(day)
    await create_shop()

async def create_shop():
    cards = ExternalDefs.load_cards('cards.json')
    shop = []
    counter = 0
    while counter < 5:
        random_number = random.randint(0, len(cards) - 1)
        if cards[random_number] not in shop:
            shop.append(cards[random_number])
            counter += 1
    ExternalDefs.save_cards(shop, 'shop.json')

@bot.event
async def on_ready():
    #TODO THERE IS NEED TO CHECK IF THE GUILD_ID EXISTS, IF IT DOESN'T, APPEND
    print(f'We have logged in as {bot.user}')
    await load_users()
    await shop_setup()
    await coins_increase()

@bot.slash_command(name="help", description="Lista todos los comandos disponibles.")
async def help_command(ctx):
    command_list = "\n".join([command.name for command in bot.application_commands])
    await ctx.respond(f"Comandos disponibles:\n{command_list}")

@bot.slash_command(name="addcard")
async def addCard(ctx):
    message = """
    **Bold Text**
    *Italic Text*
    [Link to Google](https://www.google.com)
    
    Here is a list:
    - Item 1
    - Item 2
    - Item 3
    """
    await ctx.send(message)

import discord


# * VIEWS ( GENERAL )
class ShopView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.shop = ExternalDefs.load_cards('shop.json')
        self.create_buttons()

    def create_buttons(self):
        for counter, card in enumerate(self.shop):
            button = discord.ui.Button(
                label=f"{card['card_name']} - {card['cost']} coins",
                style=discord.ButtonStyle.green,
                custom_id=f"buy_{card['card_number']}",
                row=counter # Adjust this number based on how many buttons you want per row
            )
            button.callback = self.button_callback  # Set the callback for the button
            self.add_item(button)

    async def button_callback(self, interaction: discord.Interaction):
        # Get the card number from the custom_id
        card_number = interaction.data['custom_id'].split('_')[1]
        card = next((c for c in self.shop if c['card_number'] == card_number), None)

        if card:
            # Create an embed to confirm the purchase
            embed = discord.Embed(
                title="Confirm Purchase",
                description=f"Do you really want to buy **{card['card_name']}** for **{card['cost']} coins**?",
                color=discord.Color.blue()

            )
            embed.set_image(url=card['card_url'])
            embed.set_footer(text="Click the buttons below to confirm or cancel.")

            confirm_view = ConfirmPurchaseView(card)
            await interaction.response.send_message(embed=embed, view=confirm_view, ephemeral=True)
        else:
            await interaction.response.send_message("Error: Card not found.", ephemeral=True)  # Handle case where card is not found

class ConfirmPurchaseView(discord.ui.View):
    def __init__(self, card):
        super().__init__()
        self.card = card  # Store the card data

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        # Handle the purchase logic here
        global guild  # Ensure guild is accessible
        user_id = interaction.user.id
        guild_id = str(interaction.guild.id)

        # Check if user has enough currency
        for user in guild[guild_id]['users']:
            if user['id'] == user_id:
                if user['currency'] >= self.card['cost']:
                    user['currency'] -= self.card['cost']  # Deduct cost
                    self.card["card_count"] = 1
                    user['cards'].append(self.card)  # Add card to user's collection
                    ExternalDefs.save_playlist_to_json(guild, 'data.json')  # Save changes
                    await interaction.response.send_message(f"Has comprado **{self.card['card_name']}**!", ephemeral=True)
                    self.stop()  # Stop the view
                    return
                else:
                    await interaction.response.send_message("No tienes suficiente dinero para comprar esta carta.", ephemeral=True)
                    self.stop()  # Stop the view
                    return

    @discord.ui.button(label="Back", style=discord.ButtonStyle.red)
    async def cancel_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.stop()  # Stop the view
        await interaction.response.send_message(view=ShopView(), ephemeral=True)

class GamesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view

    @discord.ui.button(label="Tienda", style=discord.ButtonStyle.primary, custom_id="shop")
    async def shop_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await create_shop()
        embed = discord.Embed(
                    title="Bienvenido a nuestra tienda",
                    description="Compra lo que quieras!",
                    color=0x00ff00
                )

        await interaction.response.edit_message(
            embed=embed,
            view=ShopView(),
        )

    @discord.ui.button(label="Ruleta - 100 🪙", style=discord.ButtonStyle.green, custom_id="wheel")
    async def ruleta_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        user_id = interaction.user.id  # Convert to string to match your JSON structure
        guild_id = str(interaction.guild.id)  # Convert to string to match your JSON structure
        cards = ExternalDefs.load_cards('cards.json')
        random_number = random.randrange(0, len(cards))  # Include the last card
        selected_card = cards[random_number]
        selected_card["card_count"] = 1
        global guild
        for user in guild[str(guild_id)]['users']:
            if user['id'] == user_id:  # Check if the user ID matches
                if user['currency'] >= 100:
                    # Check if the card already exists in the user's collection
                    if any(card['card_name'] == selected_card['card_name'] for card in user['cards']):
                        # Find the specific card in the user's collection
                        existing_card = next(card for card in user['cards'] if card['card_name'] == selected_card['card_name'])
                        existing_card['card_count'] += 1  # Increment the card count
                        embed = discord.Embed(
                            title="¡Ya tienes esta carta!",
                            description=f"***{selected_card['card_name']} ya está en tu colección: x{existing_card['card_count']} *** ",
                            color=0xff0000  # Red color for error
                        )
                        embed.set_image(url = existing_card['card_url'])
                        ExternalDefs.save_playlist_to_json(guild, 'data.json')
                    else:
                        user['cards'].append(selected_card)  # Append the selected card
                        user['currency'] -= 100
                        ExternalDefs.save_playlist_to_json(guild, 'data.json')
                        embed = discord.Embed(
                            title=f"Enhorabuena, {interaction.user.name}!",
                            description=f"Te ha tocado {selected_card['card_name']} - {selected_card['card_number']}!",
                            color=0x00ff00  # You can choose any color you like
                        )
                        embed.set_image(url=selected_card['card_url'])
                    
                    await interaction.response.send_message(
                        embed=embed,
                        ephemeral=True
                    )
                else:
                    embed = discord.Embed(
                        title="Lo siento, no tienes suficiente dinero",
                        description=f"***{user['currency']} 🪙 restantes ***"
                    )
                    await interaction.response.send_message(
                        embed=embed,
                        ephemeral=True
                    )





@bot.slash_command(name="tienda", description="Una tienda donde podrás comprar cartas con tu dinero")
async def shop(ctx):
    shop = ExternalDefs.load_cards('shop.json')
    
    embed = discord.Embed(
        title="Juegos",
        color=discord.Color.green()
    )
    
    embed.add_field(
        name="Ruleta",
        value=f"**Cuando hagas click en el botón recibirás una carta aleatoria de todas las disponibles **",
        inline=True
    )
    embed.add_field(
        name="Tienda",
        value=f"** Cuando hagas click en este botón te mostraré una pequeña tienda donde podrás elegir la carta que quieras**",
        inline=True
    )



    await ctx.respond(embed=embed, view=GamesView())

@bot.slash_command(name='musica')
async def play(ctx, song: str):
    await ctx.defer()
    try:
        guild_id = ctx.guild.id

        print(f"1.- {guild[str(guild_id)]}")
        
        # Ensure the playlist for the guild is initialized
        for num in guild :
            if num not in guild:
                guild[guild_id].append({'playlist': []})  # Initialize with an empty list

        # Voice channel connection check
        if not ctx.author.voice:
            await ctx.followup.send("No estás conectado a un canal de voz.")
            return
            
        channel = ctx.author.voice.channel
        voice_client = ctx.voice_client or await channel.connect()

        # Handle Spotify URLs
        if song.startswith("https://open.spotify.com"):
            track_id = song.split('/')[-1].split('?')[0]
            track_info = sp.track(track_id)
            
            track_name = track_info['name']
            artist_name = track_info['artists'][0]['name']
            
            # Search for the song on YouTube instead of using Spotify URL
            search_query = f"{track_name} {artist_name}"
            info = ytdl.extract_info(f"ytsearch:{search_query}", download=False)['entries'][0]
            song_url = info['url']


            # Add to playlist
            guild[str(guild_id)]['playlist'].append({
                "song_name": track_name,
                "artist_name": artist_name,
                "url": song_url,
            })

            # Create embed
            duration = int(track_info['duration_ms'] / 1000)
            minutes, seconds = divmod(duration, 60)
            embed = discord.Embed(
                description=f"**Añadido a la cola: [{track_name} - {artist_name}]({song}) - {minutes}:{seconds:02d}**",
                color=discord.Color.green()
            )

        # Handle regular YouTube searches
        else:
            search_query = song
            info = ytdl.extract_info(f"ytsearch:{search_query}", download=False)['entries'][0]
            song_url = info['url']

            # Add to playlist
            guild[str(guild_id)]['playlist'].append({
                "song_name": info['title'],
                "artist_name": info['uploader'],
                "url": song_url,
            })

            embed = discord.Embed(
                description=f"**Añadido a la cola: {info['title']}**",
                color=discord.Color.green()
            )

        await ctx.followup.send(embed=embed)
        ExternalDefs.save_playlist_to_json(guild, 'data.json')

        # Only start playing if nothing is currently playing
        if not voice_client.is_playing():
            play_next_song(ctx, voice_client, guild_id)

    except Exception as e:
        print(f"Ocurrió un error: {str(e)}")  # Print the error message
        await ctx.followup.send(f"Ocurrió un error al procesar tu solicitud: {str(e)}")  # Send error message to user




@bot.slash_command(name="cartas")
async def cards(ctx):
    import discord
from discord.ext import commands
from external_defs import ExternalDefs

# Assuming the guild variable is defined globally
guild = {}

# Define your bot
bot = commands.Bot(command_prefix="!")

@bot.slash_command(name="cartas")
async def cards(ctx):
    global guild
    guild = ExternalDefs.load_playlist_from_json('data.json')
    try:
        # Load all cards
        cards = ExternalDefs.load_cards('cards.json')
        print(f"Loaded cards: {cards}")  # Debugging output

        user_cards = []  # Initialize user_cards to store user's cards

        user_found = False  # Flag to check if user is found

        # Find the user's cards
        for user in guild[str(ctx.guild.id)]['users']:
            print(f"Checking user: {user}")  # Debugging output
            if str(user['id']) == str(ctx.author.id):  # Ensure both IDs are strings for comparison
                user_cards = user['cards']  # Get user's cards
                user_found = True  # Set flag to true
                break

        # If user has no cards, inform them
        if not user_found:
            await ctx.respond("No se encontró el usuario en la colección.")
            return

        if not user_cards:
            await ctx.respond("No tienes cartas en tu colección.")
            return

        # Create paginator for user's cards
        paginator = Paginator(cards=cards, user_cards=user_cards, guild=guild, items_per_page=9)
        embed = paginator.get_embed()  # Create embed for pagination
        view = paginator.get_view()  # Create view for pagination buttons

        # Respond with the embed and view
        await ctx.respond(embed=embed, view=view)

    except Exception as e:
        print(f"Error in cards command: {str(e)}")  # Log the error
        await ctx.respond("Ocurrió un error al procesar tu solicitud.")


        

@bot.slash_command(name='leave')
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    else:
        await ctx.respond("No estoy en un canal de voz.")

@bot.slash_command(name="stop")
async def stop(ctx):
    guild_id = ctx.guild_id
    if ctx.author.voice:
            if ctx.voice_client is None:
                await ctx.respond("No hay ninguna cancion reproduciendo")
            else:
                voice_client = ctx.voice_client
                await voice_client.disconnect()
                guild[str(guild_id)]['playlist'] = ([])  
                ExternalDefs.save_playlist_to_json(guild, 'data.json')
                await ctx.respond("Chau :(")
                

@bot.slash_command(name="playlist")
async def show_playlist(ctx):  # Renamed the function to avoid naming conflict
    global guild
    guild_id = ctx.guild.id
    if len(guild[str(guild_id)]['playlist']) == 0:
        await ctx.respond("Está vacía")
        return
    else:
        guild = ExternalDefs.load_playlist_from_json('data.json')
        current_playlist = guild[str(guild_id)]['playlist']  # Use a different variable name
        playlist_text = "Lista de reproducción: \n"
        for i, song in enumerate(current_playlist, 1):
            playlist_text += f"{i}. {song['song_name']} por {song['artist_name']}\n"  # Fixed string concatenation

        await ctx.respond(playlist_text)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send("Parece que algo salió mal. Este mensaje solo es visible para ti.")

def play_next_song(ctx, voice_client, guild_id):

    
    try:
        
        next_song = guild[str(guild_id)]['playlist'][0]  # Peek at the next song without removing
        
        async def after_playing(error):
            if error:
                print(f"Error playing audio: {error}")
            else:
                # Remove the song that just finished
                if guild[str(guild_id)]['playlist']:  # Check if the playlist is not empty
                    guild[str(guild_id)]['playlist'].pop(0)
                    ExternalDefs.save_playlist_to_json(guild, 'data.json')
                
                # Play next song if there are more songs
                if guild[str(guild_id)]['playlist']:
                    play_next_song(ctx, voice_client, guild_id)

        voice_client.play(
            discord.FFmpegPCMAudio(next_song['url'], **ffmpeg_options),
            after=lambda e: asyncio.run_coroutine_threadsafe(after_playing(e), bot.loop)
        )

        # Update now playing message
        async def update_now_playing():
            embed = discord.Embed(
                title="🎵 Reproduciendo ahora",
                color=discord.Color.green()
            )
            embed.add_field(name="Título", value=next_song['song_name'], inline=True)
            embed.add_field(name="Artista", value=next_song['artist_name'], inline=True)
            
            view = MusicControls(bot, ctx)
            await ctx.send(embed=embed, view=view)

        asyncio.run_coroutine_threadsafe(update_now_playing(), bot.loop)

    except Exception as e:
        print(f"Error in play_next_song: {e}")







bot.run(DISCORD_TOKEN)