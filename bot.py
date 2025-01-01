import discord
import os
import yt_dlp as youtube_dl
import spotipy
import asyncio
import requests

from bs4 import BeautifulSoup
from discord.ext import commands
from spotipy.oauth2 import SpotifyClientCredentials
from typing import Dict
from dotenv import load_dotenv
from collections import deque
from datetime import datetime

from musicControls import MusicControls
from external_defs import ExternalDefs
# Load the .env file
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

#Spotify Setup
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET))

intents = discord.Intents.default()
intents.message_content = True  

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
playlist: Dict[int, deque] = ExternalDefs.load_playlist_from_json('playlists.json')

# Add encoding handling for Spanish characters
def ensure_unicode(text):
    if isinstance(text, bytes):
        return text.decode('utf-8')
    return text

# Update the playlist dictionary to ensure proper encoding
for guild_id in playlist:
    for song in playlist[guild_id]:
        song['song_name'] = ensure_unicode(song['song_name'])
        song['artist_name'] = ensure_unicode(song['artist_name'])
        song['url'] = ensure_unicode(song['url'])

current_track_start_time = {}
now_playing_messages = {}
external = ExternalDefs.initialize()
current_song = {}


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.slash_command(name="help", description="List all available commands.")
async def help_command(ctx):
    command_list = "\n".join([command.name for command in bot.application_commands])  # Create a list of command names
    await ctx.respond(f"Available commands:\n{command_list}")  # Respond with the list of commands

def display(): 
    print(playlist)


@bot.slash_command(name='musica')
async def play(ctx, song: str, autoloop: bool = False):
    thinking = await ctx.defer()  # Store the thinking message

    try:
        guild_id = ctx.guild.id

        if guild_id not in playlist:
            playlist[guild_id] = deque()

        if ctx.author.voice:
            channel = ctx.author.voice.channel
            
            if ctx.voice_client is None:
                voice_client = await channel.connect()
            else:
                voice_client = ctx.voice_client
        else:
            await ctx.followup.send("You are not connected to a voice channel.")
            return

        # Add song to playlist first
        if song.startswith("https://open.spotify.com"):
            track_id = song.split('/')[-1].split('?')[0]
            track_info = sp.track(track_id)

            track_name = track_info['name']
            artist_name = track_info['artists'][0]['name']
            url = track_info['href']

            _seconds = int(track_info['duration_ms'] / 1000)
            minutes = int(_seconds // 60)
            seconds = int(_seconds % 60)
                    
            embed = discord.Embed(
                description=f"**[{artist_name} - {track_name}]({url}) - ``{minutes}:{seconds}``**",
                color=discord.Color.green()
            )

            
            playlist[guild_id].append({
                "song_name": track_name,
                "artist_name": artist_name,
                "url": song,
            })

            search_query = f"{track_name} {artist_name}"
            info = ytdl.extract_info(f"ytsearch:{search_query}", download=False)['entries'][0]
            song_url = info['url']

        else:
            try:
                search_query = song.encode('utf-8').decode('utf-8')
            except UnicodeError:
                search_query = song.encode('ascii', 'ignore').decode('ascii')
            
            info = ytdl.extract_info(f"ytsearch:{search_query}", download=False)['entries'][0]
            song_url = info['url']

            playlist[guild_id].append({
                "song_name": info['title'],
                "artist_name": info['uploader'],
                "url": song_url,
            })

            embed = discord.Embed(
                description=f"**Added to queue: {info['title']}**",
                color=discord.Color.green()
            )

            await ctx.followup.send(embed=embed)

        if thinking:
                    try:
                        await thinking.delete()
                    except:
                        pass  # Ignore if we can't delete the message

        ExternalDefs.save_playlist_to_json(playlist, 'playlists.json')

        def after_playing(err):
            playlist = ExternalDefs.load_playlist_from_json('playlists.json')
            if err:
                print(f"Error occurred: {err}")
                asyncio.run_coroutine_threadsafe(
                    ctx.send("An error occurred while playing the audio."), bot.loop
                )
            elif autoloop:
                play_audio()
                print("Autoloop")
            elif not autoloop and guild_id in playlist and playlist[guild_id] and len(playlist[guild_id]) > 0:
                play_audio()
                print("No Autollop")
            else:
                asyncio.run_coroutine_threadsafe(
                    ctx.send("No more songs in the playlist"), bot.loop
                )

        def play_audio():
            global playlist
            playlist = ExternalDefs.load_playlist_from_json('playlists.json')
            
            next_song = playlist[guild_id].popleft()
            playlist[guild_id].append(next_song)

            current_track_start_time[guild_id] = datetime.now()
            
            try:

                async def update_now_playing():
                    embed = discord.Embed(
                        title="🎵 Reproduciendo",
                        color=discord.Color.green()
                    )
                    embed.add_field(
                        name="Tema", 
                        value=next_song['song_name'],
                        inline=True
                    )
                    embed.add_field(
                        name="Artista", 
                        value=next_song['artist_name'],
                        inline=True
                    )
                    
                    # Add remaining songs count
                    remaining = len(playlist[guild_id])
                    embed.add_field(
                        name="Queue",
                        value=f"{remaining} songs remaining",
                        inline=False
                    )
                    
                    view = MusicControls(bot, ctx)
                    await ctx.send(embed=embed, view=view)
                    

                    voice_client.play(
                        discord.FFmpegPCMAudio(next_song['url'], **ffmpeg_options),
                        after=after_playing
                    )
                asyncio.run_coroutine_threadsafe(update_now_playing(), bot.loop)
                
            except Exception as e:
                print(f"Error occurred while fetching the song URL: {e}")
                return

        play_audio()

    except Exception as e2:
        print(f"An error occurred: {str(e2)}")
        await ctx.followup.send("An error occurred while processing your request.")

@bot.slash_command(name='leave')
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    else:
        await ctx.respond("I'm not in a voice channel.")

@bot.slash_command(name="stop")
async def stop(ctx):
    if ctx.author.voice:
            if ctx.voice_client is None:
                await ctx.respond("No hay ninguna cancion reproduciendo")
            else:
                voice_client = ctx.voice_client
                await voice_client.disconnect()
                playlist[ctx.guild.id] = deque()
                ExternalDefs.save_playlist_to_json(playlist, 'playlists.json')
                

@bot.slash_command(name="playlist")
async def show_playlist(ctx):  # Renamed the function to avoid naming conflict
    global playlist
    guild_id = ctx.guild.id
    if guild_id not in playlist or len(playlist[guild_id]) == 0:
        await ctx.respond("Is Empty")
        return
    else:
        playlist = ExternalDefs.load_playlist_from_json('playlists.json')
        current_playlist = playlist[guild_id]  # Use a different variable name
        playlist_text = "Playlist: \n"
        for i, song in enumerate(current_playlist, 1):
            playlist_text += f"{i}. {song['song_name']} by {song['artist_name']}\n"  # Fixed string concatenation

        await ctx.respond(playlist_text)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send("Parece que algo salió mal. Este mensaje solo es visible para ti.")

@bot.slash_command(name="lyrics")
async def lyrics(ctx):
    # Respond to the interaction immediately (avoid deferring too long)
    await ctx.respond("Fetching the lyrics, please wait...")

    guild_id = ctx.guild.id
    if guild_id not in playlist or not playlist[guild_id]:
        await ctx.followup.send("No songs are currently in the playlist!")
        return

    song = playlist[guild_id].popleft()
    song_name = song['song_name']
    artist_name = song['artist_name']

    # Fetch and scrape lyrics
    lyrics_url = ExternalDefs.get_lyrics(song_name, artist_name)

    if "http" in lyrics_url:
        lyrics = scrape_lyrics(lyrics_url)

        pages = split_lyrics_into_pages(lyrics)

        # Send the first page
        current_page = 0
        message = await ctx.followup.send(pages[current_page])

        # Adding pagination reactions (Previous and Next)
        await message.add_reaction("◀️")  # Previous page
        await message.add_reaction("▶️")  # Next page

        # Define a check for reactions
        def check(reaction, user):
            return user != bot.user and reaction.message.id == message.id

        while True:
            # Wait for user to react
            reaction, user = await bot.wait_for("reaction_add", check=check)

            # Handle next page
            if str(reaction.emoji) == "▶️" and current_page < len(pages) - 1:
                current_page += 1
                await message.edit(content=pages[current_page])
                await message.remove_reaction(reaction, user)  # Remove the user's reaction

            # Handle previous page
            elif str(reaction.emoji) == "◀️" and current_page > 0:
                current_page -= 1
                await message.edit(content=pages[current_page])
                await message.remove_reaction(reaction, user)  # Remove the user's reaction
            else:
                continue

@bot.slash_command(name='playyt')
async def playyt(ctx, query: str, autoloop: bool = False):
    try:
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            
            # Check if bot is already connected
            if ctx.voice_client is None:
                voice_client = await channel.connect()
            else:
                voice_client = ctx.voice_client
        else:
            await ctx.send("You are not connected to a voice channel.")
            return

        info = ytdl.extract_info(query if query.startswith('http') else f"ytsearch:{query}", download=False)
        
        if 'entries' in info:
            info = info['entries'][0]
            
        url = info['url']
        title = info['title']
        thumbnail = info.get('thumbnail')
        uploader = info.get('uploader', 'Unknown')

        # Create embed for now playing
        embed = discord.Embed(
            title="🎵 Now Playing",
            color=discord.Color.red()
        )
        embed.add_field(
            name="Title", 
            value=title,
            inline=True
        )
        embed.add_field(
            name="Uploader", 
            value=uploader,
            inline=True
        )
        
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)

        # Create view with controls
        view = MusicControls(bot, ctx)
        
        # Send the embed with controls
        await ctx.respond(embed=embed, view=view)

        guild_id = ctx.guild.id
        if guild_id not in playlist:
            playlist[guild_id] = deque()
        
        playlist[guild_id].append({
            "song_name": title,
            "artist_name": uploader,
            "url": url,
        })
        
        ExternalDefs.save_playlist_to_json(playlist, 'playlists.json')

        def after_playing(err):
            if err:
                print(f"Error occurred: {err}")
                asyncio.run_coroutine_threadsafe(
                    ctx.send("An error occurred while playing the audio."), bot.loop
                )
            elif autoloop and not err:
                play_audio()
            elif not autoloop and guild_id in playlist and playlist[guild_id]:
                play_audio()
            
            if not playlist[guild_id]:
                asyncio.run_coroutine_threadsafe(
                    ctx.send("No more songs available"), bot.loop
                )
            else:
                playlist[guild_id].popleft()
                ExternalDefs.save_playlist_to_json(playlist, 'playlists.json')

        def play_audio():
            next_song = playlist[guild_id].popleft()
            playlist[guild_id].append(next_song)
            
            async def update_now_playing():
                embed = discord.Embed(
                    title="🎵 Now Playing",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="Title", 
                    value=next_song['song_name'],
                    inline=True
                )
                embed.add_field(
                    name="Uploader", 
                    value=next_song['artist_name'],
                    inline=True
                )
                
                # Create view with controls
                view = MusicControls(bot, ctx)
                
                await ctx.send(embed=embed, view=view)
            
            # Schedule the embed update
            asyncio.run_coroutine_threadsafe(update_now_playing(), bot.loop)
            
            voice_client.play(
                discord.FFmpegPCMAudio(next_song['url'], **ffmpeg_options),
                after=after_playing
            )

        play_audio()

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        await ctx.respond("An error occurred while trying to play the video.")

@bot.slash_command(name="hola", description="Say hello!")
async def hola_command(ctx):
    await ctx.respond("ToImplement")


def split_lyrics_into_pages(lyrics, max_length=2000):
    """
    Splits the lyrics into pages that are within Discord's message limit.
    Each page is up to 2000 characters long.
    """
    pages = []
    while len(lyrics) > max_length:
        # Find the last newline within the limit
        split_index = lyrics.rfind("\n", 0, max_length)
        if split_index == -1:  # If no newline is found, split at max_length
            split_index = max_length
        pages.append(lyrics[:split_index])
        lyrics = lyrics[split_index:].lstrip()  # Strip leading spaces from the next page
    pages.append(lyrics)  # Add remaining lyrics as the last page
    return pages

def scrape_lyrics(song_url):

    try:
        # Make a request to the song URL
        response = requests.get(song_url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)

        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all potential lyric containers
        lyrics_containers = soup.find_all("div", class_="Lyrics-sc-1bcc94c6-1 bzTABU")

        if lyrics_containers:
            # Concatenate all lyrics parts with newlines
            lyrics = "\n".join([container.get_text(separator="\n") for container in lyrics_containers])
            return lyrics.strip()  # Return cleaned lyrics
        else:
            return "Lyrics not found on the page."

    except requests.exceptions.RequestException as e:
        # Handle network-related errors
        return f"An error occurred while fetching the song page: {e}"

    except Exception as e:
        # Handle other unexpected errors
        return f"An unexpected error occurred: {e}"

bot.run(DISCORD_TOKEN)