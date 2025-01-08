import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

async def my_continuous_task():
    await bot.wait_until_ready()  # Wait until the bot is ready
    channel = bot.get_channel("YOUR_CHANNEL_ID")  # Replace with your channel ID
    while not bot.is_closed():  # Run until the bot is closed
        if channel:
            await channel.send("This message is sent continuously!")
        await asyncio.sleep(10)  # Wait for 10 seconds before sending the next message

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    bot.loop.create_task(my_continuous_task())  # Start the continuous task

bot.run('YOUR_BOT_TOKEN')