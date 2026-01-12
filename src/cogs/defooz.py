import discord
from discord import app_commands
from discord.ext import commands
import random

class DefoozPersona(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="grade", description="Get YOUR grade /20 (Daily reward available)")
    async def grade(self, interaction: discord.Interaction):
        user = interaction.user # Self-target only
        
        # Check for Exam Answers Item
        eco = self.bot.get_cog("EconomySystem")
        used_cheat_item = False
        
        if eco and eco.has_item(user.id, "exam_answers"):
            score = 20
            eco.remove_item(user.id, "exam_answers")
            used_cheat_item = True
        else:
            score = random.randint(0, 20)
        
        comments_high = [
            "Excellent. Your **BGP configuration** is flawless. Almost as good as **Julie**.",
            "Not bad. Your throughput is acceptable. **Ben** would be proud.",
            "Finally, someone who understands **Spanning Tree Protocol**.",
            "Good job. You didn't block port 80 this time.",
            "20/20? No, that's reserved for **Julie**. But you get close.",
            "Impressive. Did **Ben** help you with this? No? Then good job.",
            "**Loris** would say *Das ist fantastisch*.",
            "Better than those **HELMO** guys (**Hugo & Tobias**), that's for sure."
        ]
        
        comments_mid = [
            "We can observe some packet loss in your logic.",
            "Moyenne. Your **TTL** is too low.",
            "It works, but your cabling is a mess. **Ben** would have organized it better.",
            "Passable, but clean up your VLANs.",
            "Why can't you be more like **Julie**? Her packets never drop.",
            "Not bad, but **Marvin** could probably do this. And that's worrying.",
            "You are hacking like **Hugo & Tobias**. Stop trying to be Mr. Robot."
        ]
        
        comments_low = [
            "C'est inacceptable. Check your **Layer 1** connectivity.",
            "0/20. Did you even read the RFC?",
            "Your brain has a segmentation fault.",
            "Route unknown. Host unreachable.",
            "It's always DNS, but in this case, it's just you.",
            "Even **Ben** doesn't make these mistakes (and he asks me questions all day).",
            "This is why **Julie** is the favorite student.",
            "Are you **Marvin** in disguise? Because this is garbage.",
            "Go back to **HELMO** with **Hugo & Tobias** if you want to fail.",
            "**Loris** is crying in German looking at this code."
        ]
        
        if score >= 15:
            comment = random.choice(comments_high)
        elif score >= 10:
            comment = random.choice(comments_mid)
        else:
            comment = random.choice(comments_low)
            
        # Economy Reward (Daily Limit)
        reward_msg = ""
        eco = self.bot.get_cog("EconomySystem")
        
        if eco:
            if eco.check_daily(user.id):
                if score >= 10:
                    reward = score * 10
                    eco.add_money(user.id, reward)
                    eco.claim_daily(user.id) # Mark as claimed
                    reward_msg = f"\n💰 **Scholarship Awarded**: +{reward} Coins (Daily Limit Reached)"
                else:
                    # Failed grade = No money, but daily NOT consumed? 
                    # Usually daily rewards are consumed on attempt or success. 
                    # Let's say: Only consumed if you PASS and get money.
                    reward_msg = "\n💸 **No Scholarship**: You failed. Study harder."
            else:
                reward_msg = "\n⏳ **Daily Reward Cooldown**: Come back tomorrow for money."

        await interaction.response.send_message(f"🎓 **Grade for {user.mention}**: {score}/20\n👨‍🏫 *Professor Defooz says:* {comment}{reward_msg}")

    @app_commands.command(name="aws_bill", description="Generate a fake AWS invoice")
    async def aws_bill(self, interaction: discord.Interaction):
        amount = random.randint(500, 15000)
        services = ["EC2 (p3.16xlarge)", "RDS Multi-AZ", "Nat Gateway (Idle)", "Data Transfer Out", "Elastic Kubernetes Service"]
        regions = ["us-east-1", "eu-west-1", "ap-northeast-1"]
        
        service = random.choice(services)
        region = random.choice(regions)
        
        await interaction.response.send_message(
            f"💸 **AWS BILLING ALERT** 💸\n"
            f"User: {interaction.user.mention}\n"
            f"Amount Due: **${amount:,.2f}**\n"
            f"Reason: You forgot to terminate a **{service}** in **{region}**.\n"
            f"Action: Immediate liquidation of assets required."
        )

    @app_commands.command(name="cisco", description="Get a random Cisco fact or config line")
    async def cisco(self, interaction: discord.Interaction):
        facts = [
            "`switchport mode trunk` - The basics, come on!",
            "`copy running-config startup-config` - Do NOT forget this before reloading.",
            "`router ospf 1` - Open Shortest Path First, learn it.",
            "`no shutdown` - The command you always forget on the interface.",
            "`show i p int brief` - The only verification command you need.",
            "Did you check the ACL? It's always the ACL.",
            "**Ben** asks me this question every day: 'What is a VLAN?'... Don't be like Ben.",
            "**Julie** already finished the lab. Why are you still on Step 1?",
            "Remember: Layer 1 issues are usually just you tripping over the cable.",
            "**Marvin**, stop touching the switch. You are breaking the STP.",
            "**Hugo & Tobias**: 'Putting a firewall everywhere' is NOT a network design.",
            "**Loris**: *Achtung*! Do not loop the network."
        ]
        await interaction.response.send_message(f"🖥️ **Cisco Tip:**\n{random.choice(facts)}")

    @app_commands.command(name="shutup", description="Administratively down a user (Mock)")
    async def shutup(self, interaction: discord.Interaction, user: discord.Member):
        # We don't actually mute because that requires permissions, just roleplay
        await interaction.response.send_message(f"🚫 **Command issued:**\n`interface {user.display_name}`\n`shutdown`\n\n*User administratively down.*")

        await interaction.response.send_message(
            f"💪 **COMMITMENT IS KEY!**\n"
            f"You think the network builds itself? NO! \n"
            f"You need **100% COMMITMENT**.\n"
            f"Packet delivery requires human delivery. Be committed to your subnet!"
        )

    @app_commands.command(name="kill", description="Kill a user's connection/process")
    async def kill(self, interaction: discord.Interaction, user: discord.Member):
        pid = random.randint(1000, 9999)
        await interaction.response.send_message(
            f"� **Killing Process {pid} ({user.display_name})...**\n"
            f"`taskkill /F /PID {pid}`\n"
            f"⚠️ **Connection Reset by Peer**.\n"
            f"*(The user has been successfully terminated from the network layer)*"
        )


async def setup(bot):
    await bot.add_cog(DefoozPersona(bot))
