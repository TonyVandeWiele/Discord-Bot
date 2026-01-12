import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

class DefoozBot(commands.Bot):
    def __init__(self):
        # Intents are required for modern bots
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True 
        
        super().__init__(
            command_prefix=commands.when_mentioned_or("!"), # Fallback, mostly using slash commands
            intents=intents,
            help_command=None # We will use a custom help simple command or slash command
        )

    async def setup_hook(self):
        # Load extensions (cogs)
        initial_extensions = [
            'src.cogs.general',
            'src.cogs.defooz',
            'src.cogs.tech',
            'src.cogs.exams',
            'src.cogs.game',
            'src.cogs.economy_system',
            'src.cogs.fun_games',
            'src.cogs.shop'
        ]

        print("--- Loading Cogs ---")
        for extension in initial_extensions:
            try:
                await self.load_extension(extension)
                print(f"✅ Loaded {extension}")
            except Exception as e:
                print(f"❌ Failed to load {extension}: {e}")
        
        # Sync slash commands
        print("--- Syncing Slash Commands ---")
        try:
            synced = await self.tree.sync()
            print(f"✅ Synced {len(synced)} slash commands")
        except Exception as e:
            print(f"❌ Failed to sync: {e}")

    async def on_ready(self):
        print(f'🤖 Logged in as {self.user} (ID: {self.user.id})')
        await self.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching, 
            name="Corrige l'examen de Cloud"
        ))

bot = DefoozBot()

if __name__ == '__main__':
    if not TOKEN:
        print("❌ Error: DISCORD_TOKEN not found in .env")
    else:
        try:
            bot.run(TOKEN)
        except Exception as e:
            print(f"❌ Critical Error: {e}")