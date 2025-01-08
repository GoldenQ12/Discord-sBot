import discord
import json


class MusicControls(discord.ui.View):
    def __init__(self, bot, ctx):
        super().__init__(timeout=None)
        self.bot = bot
        self.ctx = ctx



        # Skip Button
        skip_button = discord.ui.Button(
            style=discord.ButtonStyle.gray,
            emoji="⏩",
            custom_id="skip"
        )
        skip_button.callback = self.skip_callback

        # Pause/Play button (inicialmente como pause)
        self.toggle_button = discord.ui.Button(
            style=discord.ButtonStyle.gray,
            emoji="⏸️",
            custom_id="pause"
        )
        self.toggle_button.callback = self.toggle_callback

        self.add_item(skip_button)
        self.add_item(self.toggle_button)

    async def toggle_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.voice:
            return
            
        if interaction.guild.voice_client:
            try:
                if self.toggle_button.custom_id == "pause":
                    interaction.guild.voice_client.pause()
                    self.toggle_button.style = discord.ButtonStyle.green
                    self.toggle_button.emoji = "▶️"
                    self.toggle_button.custom_id = "play"
                else:
                    interaction.guild.voice_client.resume()
                    self.toggle_button.style = discord.ButtonStyle.gray
                    self.toggle_button.emoji = "⏸️"
                    self.toggle_button.custom_id = "pause"
                
                await interaction.message.edit(view=self)
            except Exception as e:
                print(f"Error en toggle: {e}")
        else:
            return

    async def skip_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.voice:
            await interaction.response.send_message("You need to be in a voice channel to skip a track.", ephemeral=True)
            return
            
        if interaction.guild.voice_client:
            guild_id = str(interaction.guild.id)
            try:
                with open('data.json', 'r', encoding='utf-8') as f:
                    guild = json.load(f)
            except FileNotFoundError:
                await interaction.response.send_message("Playlists file not found.", ephemeral=True)
                return
            except json.JSONDecodeError:
                await interaction.response.send_message("Error reading playlists file.", ephemeral=True)
                return
            
            if guild_id in guild:
                if guild[guild_id]['playlist']:
                    guild[guild_id]['playlist'].pop(0)  # Remove the first song
                    with open('playlists.json', 'w', encoding='utf-8') as f:
                        json.dump(guild, f, indent=4, ensure_ascii=False)
                    interaction.guild.voice_client.stop()
                else:
                    await interaction.response.send_message("The playlist is empty.", ephemeral=True)
            else:
                await interaction.response.send_message("Guild ID not found in playlists.", ephemeral=True)
        else:
            await interaction.response.send_message("There is no active voice client.", ephemeral=True)


