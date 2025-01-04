import discord
import os
import yt_dlp as youtube_dl
import spotipy
import asyncio

from discord.ext import commands
from spotipy.oauth2 import SpotifyClientCredentials
from typing import Dict, Any
from dotenv import load_dotenv
from collections import deque

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
guild: Dict[int, Dict[str, Any]] = ExternalDefs.load_playlist_from_json('playlists.json')



def ensure_unicode(text):
    if isinstance(text, bytes):
        return text.decode('utf-8')
    return text



current_track_start_time = {}
now_playing_messages = {}
external = ExternalDefs.initialize()
current_song = {}


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.slash_command(name="help", description="Lista todos los comandos disponibles.")
async def help_command(ctx):
    command_list = "\n".join([command.name for command in bot.application_commands])
    await ctx.respond(f"Comandos disponibles:\n{command_list}")



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

            print(guild[guild_id]['playlist'])

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
        ExternalDefs.save_playlist_to_json(guild, 'playlists.json')

        # Only start playing if nothing is currently playing
        if not voice_client.is_playing():
            play_next_song(ctx, voice_client, guild_id)

    except Exception as e:
        print(f"Ocurrió un error: {str(e)}")  # Print the error message
        await ctx.followup.send(f"Ocurrió un error al procesar tu solicitud: {str(e)}")  # Send error message to user

@bot.slash_command(name="cartas")
async def cards(ctx):
    await ctx.respond("Implement")

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
                ExternalDefs.save_playlist_to_json(guild, 'playlists.json')
                

@bot.slash_command(name="playlist")
async def show_playlist(ctx):  # Renamed the function to avoid naming conflict
    global guild
    guild_id = ctx.guild.id
    if len(guild[str(guild_id)]['playlist']) == 0:
        await ctx.respond("Está vacía")
        return
    else:
        guild = ExternalDefs.load_playlist_from_json('playlists.json')
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
                    ExternalDefs.save_playlist_to_json(guild, 'playlists.json')
                
                # Play next song if there are more songs
                if guild[str(guild_id)]['playlist']:
                    play_next_song(ctx, voice_client, guild_id)
                else:
                    await ctx.send("¡Cola terminada!")

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