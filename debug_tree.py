
import discord
from discord.ext import commands
import asyncio
import os
import sys

# Add src to path
sys.path.append(os.getcwd())

extensions = [
    'src.cogs.general',
    'src.cogs.defooz',
    'src.cogs.tech',
    'src.cogs.exams',
    'src.cogs.game', 
    'src.cogs.economy_system',
    'src.cogs.fun_games',
    'src.cogs.shop',
    'src.cogs.crypto'
]

async def check_tree():
    bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())
    
    log = []
    log.append("--- Diagnostic Report ---")
    for ext in extensions:
        try:
            await bot.load_extension(ext)
        except Exception as e:
            log.append(f"[ERROR] {ext}: {e}")

    cmds = bot.tree.get_commands()
    log.append(f"Total Commands: {len(cmds)}")
    sorted_cmds = sorted([c.name for c in cmds])
    for name in sorted_cmds:
        log.append(f" - {name}")
        
    with open("cmd_list.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(log))

if __name__ == "__main__":
    try:
        asyncio.run(check_tree())
    except Exception:
        pass
