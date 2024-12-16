import discord
import json


class MusicControls(discord.ui.View):
    def __init__(self, bot, ctx):
        super().__init__(timeout=None)
        self.bot = bot
        self.ctx = ctx
        
        # Spotify button
        spotify_button = discord.ui.Button(
            style=discord.ButtonStyle.green,
            emoji="🎵"
        )
        self.add_item(spotify_button)
        
        # Skip button
        skip_button = discord.ui.Button(
            style=discord.ButtonStyle.gray,
            emoji="⏭️",
            custom_id="skip"
        )
        skip_button.callback = self.skip_callback

        # Corrected pause button creation
        pause_button = discord.ui.Button(
            style=discord.ButtonStyle.gray,
            emoji="⏯️",
            custom_id="pause"
        )
        pause_button.callback = self.pause_callback

        self.add_item(skip_button)
        self.add_item(pause_button)

    async def pause_callback(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            await interaction.response.send_message("You need to be in a voice channel!", ephemeral=True)
            return
            
        if interaction.guild.voice_client:
            try:
                if interaction.guild.voice_client.is_paused():
                    await interaction.guild.voice_client.resume()  # Await the resume
                    await interaction.response.send_message("Resumed playback!", ephemeral=True)
                else:
                    await interaction.guild.voice_client.pause()  # Await the pause
                    await interaction.response.send_message("Paused playback!", ephemeral=True)
                
            except Exception as e:
                print(f"Error updating JSON: {e}")
        else:
            await interaction.response.send_message("Nothing is playing!", ephemeral=True)

    async def skip_callback(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            await interaction.response.send_message("You need to be in a voice channel!", ephemeral=True)
            return
            
        if interaction.guild.voice_client:
            guild_id = str(interaction.guild.id)  # Use interaction.guild.id instead of interaction.guild_id
            with open('playlists.json', 'r', encoding='utf-8') as f:
                playlists_data = json.load(f)
            
            # Remove the current song if guild exists in JSON
            if guild_id in playlists_data and playlists_data[guild_id]:
                playlists_data[guild_id].pop(0)  # Remove first song (dictionary with song details)
                
                # Save updated JSON
                with open('playlists.json', 'w', encoding='utf-8') as f:
                    json.dump(playlists_data, f)
            
            # Stop current track
            interaction.guild.voice_client.stop()
            await interaction.response.send_message("⏭️ Skipped!", ephemeral=True)
                
           
        else:
            await interaction.response.send_message("Nothing is playing!", ephemeral=True)