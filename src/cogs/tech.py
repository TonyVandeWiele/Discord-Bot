import discord
from discord import app_commands
from discord.ext import commands
import random
import ipaddress

class TechTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="calc", description="Subnet Calculator (Network/Broadcast/Hosts)")
    async def calc(self, interaction: discord.Interaction, ip_cidr: str):
        try:
            # Parse the IP network
            network = ipaddress.ip_network(ip_cidr, strict=False)
            
            # Calculate details
            net_id = str(network.network_address)
            broadcast = str(network.broadcast_address)
            netmask = str(network.netmask)
            total_hosts = network.num_addresses
            usable_hosts = total_hosts - 2 if total_hosts > 2 else 0
            
            # For /31 and /32 edge cases, logic changes slightly but standard /24 etc is standard.
            
            response = (
                f"🧮 **Subnet Calculator Results** for `{ip_cidr}`\n"
                f"----------------------------------------\n"
                f"**Network ID**: `{net_id}`\n"
                f"**Broadcast**: `{broadcast}`\n"
                f"**Netmask**: `{netmask}`\n"
                f"**Usable Hosts**: `{usable_hosts}`\n"
                f"**First Host**: `{network.network_address + 1}`\n"
                f"**Last Host**: `{network.broadcast_address - 1}`"
            )
            await interaction.response.send_message(response)
            
        except ValueError:
            await interaction.response.send_message("❌ **Error**: Invalid Format. Use `192.168.1.1/24` format.", ephemeral=True)

    @app_commands.command(name="excuse", description="Generate a random technical excuse")
    async def excuse(self, interaction: discord.Interaction):
        excuses = [
            "My BGP neighbor relationship timed out.",
            "The cloud instance is stuck in a reboot loop.",
            "I experienced high latency on my neural network.",
            "A cosmic ray flipped a bit in my RAM.",
            "I was busy debugging a race condition.",
            "The DNS propagation took longer than expected.",
            "My firewall dropped the packets containing my homework.",
            "**Ben** deleted my repository by accident.",
            "I was too busy helping **Ben** understand what an IP address is.",
            "I tried to be like **Julie**, but I am mere mortal.",
            "**Marvin** tripped over the power cord.",
            "**Hugo & Tobias** hacked my laptop (supposedly).",
            "I was translating the documentation for **Loris**.",
            "A **HELMO** student stole my notes."
        ]
        await interaction.response.send_message(f"🤷 **Excuse:** {random.choice(excuses)}")

    @app_commands.command(name="ask_marvin", description="Get terrible advice from Marvin")
    async def ask_marvin(self, interaction: discord.Interaction):
        advice = [
            "Have you tried **deleting System32**? It improves packet flow.",
            "Use a **Hub** instead of a Switch. It broadcasts your love to everyone.",
            "Passwords are for weaklings. Just set it to `admin/admin`.",
            "Disable the **Firewall**. It just slows down the internet.",
            "If it doesn't work, just hit the server hard. Percussive maintenance.",
            "Why use IPv6? IPv4 has enough addresses for at least... 2 more years.",
            "NAT is basically a security feature, right?",
            "Just route everything to `0.0.0.0`, the internet will find a way.",
            "Ask **Ben**, he usually Googles it for me."
        ]
        await interaction.response.send_message(
            f"🤓 **Marvin's Advice**:\n"
            f"\"{random.choice(advice)}\"\n"
            f"*(Disclaimer: Do NOT listen to Marvin)*"
        )

    @app_commands.command(name="quiz", description="Take a quick CCNA or AWS quiz")
    @app_commands.choices(topic=[
        app_commands.Choice(name="CCNA (Cisco)", value="ccna"),
        app_commands.Choice(name="AWS (Cloud)", value="aws")
    ])
    async def quiz(self, interaction: discord.Interaction, topic: app_commands.Choice[str]):
        # Simple quiz logic. For a real bot, we might use buttons, but let's stick to text for simplicity/reliability first.
        
        ccna_questions = [
            {"q": "What is the default administrative distance of OSPF?", "a": "110"},
            {"q": "Which command displays the routing table?", "a": "show ip route"},
            {"q": "What is the PDU of Layer 2?", "a": "Frame"},
            {"q": "What port does SSH use?", "a": "22"}
        ]
        
        aws_questions = [
            {"q": "Which service is Object Storage?", "a": "S3"},
            {"q": "What is the serverless compute service?", "a": "Lambda"},
            {"q": "Which database is NoSQL?", "a": "DynamoDB"},
            {"q": "What is the managed DDoS protection service?", "a": "Shield"}
        ]
        
        if topic.value == "ccna":
            question = random.choice(ccna_questions)
        else:
            question = random.choice(aws_questions)
            
        # We send the question, user has to think about it (spoiler for answer)
        await interaction.response.send_message(
            f"❓ **Quiz Time ({topic.name})**\n\n"
            f"**Question**: {question['q']}\n\n"
            f"||**Answer**: {question['a']}|| (Click to reveal)"
        )

async def setup(bot):
    await bot.add_cog(TechTools(bot))
