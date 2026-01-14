
import sys
import os
import asyncio
from discord.ext import commands
import discord

# Add current directory to path
sys.path.append(os.getcwd())

async def test_load():
    print("--- Starting Debug ---")
    
    # Fake bot
    bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())
    
    try:
        # Import directly to check for immediate syntax errors
        from src.cogs.economy_system import EconomySystem
        print("✅ Successfully imported EconomySystem class")
        
        # Initialize Cog
        cog = EconomySystem(bot)
        print("✅ Successfully initialized EconomySystem cog")
        
        # Check commands
        # App commands are in cog.app_command or similar depending on implementation
        # For app_commands, they are usually in various attributes.
        # But we can check methods decorated with @app_commands.command
        
        found = False
        for name, method in EconomySystem.__dict__.items():
            if hasattr(method, "__discord_app_commands_command__"):
                 print(f"👉 Found App Command: {name}")
                 if name == "rain":
                     found = True
            # Also check for regular commands if any
            if isinstance(method, commands.Command):
                print(f"👉 Found Prefix Command: {name}")
                
        if found:
            print("✅ 'rain' command found in class definition.")
        else:
            print("❌ 'rain' command NOT found in class definition.")

    except Exception as e:
        print(f"❌ Error during import/init: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_load())
