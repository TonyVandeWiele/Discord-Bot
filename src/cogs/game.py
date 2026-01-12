import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import ipaddress

# --- BUTTON VIEWS ---

class MissionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.value = None

    @discord.ui.button(label="🔍 Analyze Logs", style=discord.ButtonStyle.primary, emoji="🔍")
    async def logs(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.clear_items() # Remove buttons to prevent double click
        await interaction.response.edit_message(content="📜 **LOGS ANALYSIS**:\n`[CRITICAL] Port Gi0/1 down. Loop detected from User: MARVIN.`\n\nMarvin created a switching loop again...", view=None)

    @discord.ui.button(label="🔌 Reconnect Cable", style=discord.ButtonStyle.success, emoji="🔌")
    async def reconnect(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.clear_items()
        outcome = random.choice([
            "✅ Success! You saved the network. **Julie** is impressed.",
            "💥 **BOOM!** You tripped over the cable and disconnected the Server Rack. **Defooz** is furious."
        ])
        await interaction.response.edit_message(content=f"{outcome}", view=None)

    @discord.ui.button(label="🔥 Fire Ben", style=discord.ButtonStyle.danger, emoji="🔥")
    async def fire_ben(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.clear_items()
        await interaction.response.edit_message(content="🛑 **HR ALERT**\nYou cannot fire Ben. He is the mascot. But it felt good to click that button.", view=None)

class SubnetGameView(discord.ui.View):
    def __init__(self, correct_answer, wrong_answers):
        super().__init__(timeout=30)
        self.correct = correct_answer
        
        # Create a list of options (1 correct + 2 wrong)
        options = wrong_answers[:2] + [correct_answer]
        random.shuffle(options)
        
        for opt in options:
            # We use a lambda loop workaround or a custom button class, but here we just add them manually for simplicity in this constrained envio
            btn = discord.ui.Button(label=str(opt), style=discord.ButtonStyle.secondary)
            btn.callback = self.create_callback(opt)
            self.add_item(btn)

    def create_callback(self, label):
        async def callback(interaction: discord.Interaction):
            if label == self.correct:
                await interaction.response.edit_message(content=f"✅ **CORRECT!** The broadcast is indeed `{label}`. Good job.", view=None)
            else:
                await interaction.response.edit_message(content=f"❌ **WRONG!** You clicked `{label}`. The correct answer was `{self.correct}`. Go study!", view=None)
        return callback

class Game(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="mission", description="Start a Network Rescue Mission (Interactive)")
    async def mission(self, interaction: discord.Interaction):
        # Initial Story
        embed = discord.Embed(title="🚨 NETWORK EMERGENCY", description="**Alert!** The Core Router 9000 has stopped responding.\n**Ben** was seen near the rack holding a coffee.\n\n*What do you do?*", color=discord.Color.red())
        view = MissionView()
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="traceroute", description="Visual animated traceroute")
    async def traceroute(self, interaction: discord.Interaction, target: str):
        # We start by sending a message, then edit it
        await interaction.response.send_message(f"🚀 **Initiating Traceroute to {target}**...")
        msg = await interaction.original_response()
        
        hops = [
            "1. `192.168.1.1` (Local Gateway) - 1ms",
            "2. `10.0.0.254` (ISP Provider) - 12ms",
            "3. `172.16.50.5` (HELMO Firewall - Hugo's Laptop) - 🐢 450ms",
            "4. `8.8.8.8` (Google DNS) - 15ms",
            "5. `203.0.113.5` (NSA Surveillance Node) - 🔒 Hid",
            "6. `192.168.0.1` (**Ben's Smart Fridge**) - 999ms",
            f"7. **{target}** (Destination Reached) ✅"
        ]
        
        content = f"🚀 **Traceroute to {target}**:\n```"
        for hop in hops:
            await asyncio.sleep(1.0) # Animation delay
            content += f"\n{hop}"
            try:
                await msg.edit(content=content + "\n```")
            except:
                break # Stop if message deleted

    @app_commands.command(name="subnet_game", description="Practice: Find the Broadcast Address")
    async def subnet_game(self, interaction: discord.Interaction):
        # Generate random IP/Subnet
        octet3 = random.randint(0, 255)
        # Choosing easy subnets for mental math (/24, /25, /26, /30)
        cidr = random.choice([24, 25, 26, 28, 30]) 
        ip_str = f"192.168.{octet3}.0/{cidr}"
        
        network = ipaddress.ip_network(ip_str)
        broadcast = str(network.broadcast_address)
        
        # Generate wrong answers (fake broadcasts)
        wrong1 = str(network.broadcast_address + 1)
        wrong2 = str(network.broadcast_address - random.randint(5, 50))
        
        await interaction.response.send_message(
            f"🧠 **Subnet Challenge!**\nNetwork: `{ip_str}`\n\n*What is the **Broadcast Address**?*",
            view=SubnetGameView(broadcast, [wrong1, wrong2])
        )

async def setup(bot):
    await bot.add_cog(Game(bot))
