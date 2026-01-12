import discord
from discord import app_commands
from discord.ext import commands
import random

class Exams(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="result", description="Get your (fake) exam result")
    async def result(self, interaction: discord.Interaction):
        score = random.randint(0, 20)
        
        if score >= 10:
            status = "PASS ✅"
            messages = [
                "Just enough. Don't get cocky.",
                "Miracle. You passed.",
                "Acceptable. But your handwriting was terrible.",
                "Good job. See you in the next Master year.",
                "Not quite **Julie** level, but acceptable.",
                "You passed! Go buy **Ben** a drink, he needs it.",
                "Better than **Marvin**, that's a start.",
                "**Loris** approves this efficiency."
            ]
        else:
            status = "FAIL ❌"
            messages = [
                "See you in September (Seconde session).",
                "Did you even open the PDF?",
                "Unacceptable. Your routing table was empty.",
                "You confused Layer 2 and Layer 3. Get out.",
                "Even **Ben** got a better grade, and he was asleep.",
                "Ask **Julie** for tutoring next time.",
                "You performed like **Marvin**. That is an insult.",
                "Go join **Hugo & Tobias** at **HELMO**, maybe they accept 2/20."
            ]
            
        await interaction.response.send_message(
            f"📄 **Exam Result for {interaction.user.mention}**\n"
            f"Score: **{score}/20**\n"
            f"Status: **{status}**\n"
            f"Comment: *{random.choice(messages)}*"
        )

    @app_commands.command(name="cheat", description="Try to cheat on the exam")
    async def cheat(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "🚨 **ACADEMIC INTEGRITY ALERT** 🚨\n"
            "Cheating attempt detected.\n"
            "IP Address logged.\n"
            "Report sent to the Dean.\n"
            "*(Nice try, but Professor Defooz sees everything via Wireshark)*"
        )

async def setup(bot):
    await bot.add_cog(Exams(bot))
