import discord
from discord import app_commands
from discord.ext import commands

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Check latency (Test connectivity)")
    async def ping(self, interaction: discord.Interaction):
        # Using technical term "Latency" fitting the theme
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"🏓 Pong! Latency: {latency}ms. Connection status: ACTIVE.")

async def setup(bot):
    await bot.add_cog(General(bot))
