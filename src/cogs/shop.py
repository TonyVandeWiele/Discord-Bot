import discord
from discord import app_commands
from discord.ext import commands

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Consumables / Utility / Upgrades
        self.items = {
            # Utility
            "exam_answers": {"type": "item", "name": "📜 Exam Answers", "cost": 500, "desc": "Guarantees 20/20 on next grade", "req_id": None},
            "vpn": {"type": "item", "name": "🛡️ VPN Shield", "cost": 100, "desc": "Protects against /kill (One use)", "req_id": None},
            "coffee": {"type": "item", "name": "☕ Defooz Coffee", "cost": 15, "desc": "Buy the professor a drink (Good Karma)", "req_id": None},
            "lottery": {"type": "item", "name": "🎫 Lottery Ticket", "cost": 50, "desc": "Scratch to win random amount", "req_id": None},
            
            # Clicker Upgrades (Alternating Flat / Crit)
            "logi_b100": {
                "type": "upgrade", "name": "🖱️ Logitech B100", "cost": 250, 
                "desc": "Clicker: +0.5 Coin (Office Basic)", 
                "req_id": None, "req_count": 0, "bonus": 0.5, "stat": "flat"
            },
            "hyperx_pulsefire": {
                "type": "upgrade", "name": "🖱️ HyperX Pulsefire", "cost": 600, 
                "desc": "Clicker: +2% Crit Chance (Entry Gaming)", 
                "req_id": "logi_b100", "req_count": 5, "bonus": 0.02, "stat": "crit"
            },
            "razer_deathadder": {
                "type": "upgrade", "name": "🖱️ Razer DeathAdder V3", "cost": 1500, 
                "desc": "Clicker: +2.0 Coin (Esports Pro)", 
                "req_id": "hyperx_pulsefire", "req_count": 5, "bonus": 2.0, "stat": "flat"
            },
            "logi_g502": {
                "type": "upgrade", "name": "🖱️ Logitech G502 Hero", "cost": 4000, 
                "desc": "Clicker: +3% Crit Chance (The Brick)", 
                "req_id": "razer_deathadder", "req_count": 5, "bonus": 0.03, "stat": "crit"
            },
            "wooting_60he": {
                "type": "upgrade", "name": "🎹 Wooting 60HE+", "cost": 10000, 
                "desc": "Clicker: +8.0 Coin (Rapid Trigger)", 
                "req_id": "logi_g502", "req_count": 5, "bonus": 8.0, "stat": "flat"
            },
            "secretlab_titan": {
                "type": "upgrade", "name": "💺 SecretLab Titan Evo", "cost": 25000, 
                "desc": "Clicker: +4% Crit Chance (Gamer Comfort)", 
                "req_id": "wooting_60he", "req_count": 5, "bonus": 0.04, "stat": "crit"
            }
        }
        
        # Generators (Passive Income) - AWS/Cisco Theme
        self.generators = {
            "cisco_lab": {
                "name": "🕸️ Cisco Packet Tracer", 
                "cost": 100, 
                "rate": 5, 
                "desc": "Simulated network. Low profit.",
                "req_id": None, "req_count": 0
            },
            "aws_lambda": {
                "name": "⚡ AWS Lambda", 
                "cost": 500, 
                "rate": 20, 
                "desc": "Serverless compute functions.",
                "req_id": "cisco_lab", "req_count": 5
            },
            "nexus_9k": {
                "name": "🔌 Cisco Nexus 9000", 
                "cost": 2000, 
                "rate": 100, 
                "desc": "Data Center switch. Big bandwidth.",
                "req_id": "aws_lambda", "req_count": 5
            },
            "ecs_cluster": {
                "name": "📦 AWS ECS Fargate", 
                "cost": 7500, 
                "rate": 400, 
                "desc": "Elastic Container Service. Docker containers.",
                "req_id": "nexus_9k", "req_count": 5
            },
            "sagemaker": {
                "name": "🧠 AWS SageMaker", 
                "cost": 25000, 
                "rate": 1500, 
                "desc": "Training ML models on p4d.24xlarge.",
                "req_id": "ecs_cluster", "req_count": 5
            },
            "braket": {
                "name": "⚛️ AWS Braket (Quantum)", 
                "cost": 100000, 
                "rate": 7000, 
                "desc": "Quantum computing. The future is now.",
                "req_id": "sagemaker", "req_count": 5
            }
        }

    def get_economy(self):
        return self.bot.get_cog("EconomySystem")

    def get_gen_rates(self):
        return {k: v["rate"] for k, v in self.generators.items()}

    @app_commands.command(name="shop", description="View the Item & Tech Shop")
    async def shop(self, interaction: discord.Interaction):
        eco = self.get_economy()
        if not eco: return
        
        balance = eco.get_balance(interaction.user.id)
        user_gens = eco.get_generators(interaction.user.id)
        user_data = eco.get_user_data(interaction.user.id)
        inv = user_data.get("inventory", [])
        
        embed = discord.Embed(title="🛒 Defooz Tech Market", description=f"Your Balance: **{balance:.1f} Coins**", color=discord.Color.blue())
        
        # Items / Upgrades Section
        embed.add_field(name="🖱️ Gamer Gear (Active Clicker)", value="Mainstream brands for max performance.", inline=False)
        for item_id, item in self.items.items():
            # Check requirements
            is_locked = False
            req_text = ""
            if item.get("req_id"):
                # Count how many of req_id user has in inventory
                count_req = inv.count(item["req_id"])
                if count_req < item["req_count"]:
                    is_locked = True
                    req_name = self.items[item["req_id"]]["name"]
                    req_text = f"🔒 [Requires {item['req_count']}x {req_name}]"
            
            if is_locked:
                embed.add_field(name=f"{item['name']} - LOCKED", value=req_text, inline=True)
            else:
                owned_count = inv.count(item_id)
                owned_text = f"\nOwned: **{owned_count}**" if item["type"] == "upgrade" else ""
                embed.add_field(name=f"{item['name']} - {item['cost']}💰", value=f"{item['desc']}{owned_text}", inline=True)
            
        # Generators Section
        embed.add_field(name="🏭 Passive Income (Tech Tree)", value="Buy tech to generate coins/hour.", inline=False)
        
        for gen_id, gen in self.generators.items():
            # Check requirements logic
            is_locked = False
            req_text = ""
            if gen["req_id"]:
                current_prev = user_gens.get(gen["req_id"], 0)
                if current_prev < gen["req_count"]:
                    is_locked = True
                    req_name = self.generators[gen["req_id"]]["name"]
                    req_text = f"🔒 [Requires {gen['req_count']}x {req_name}]"
            
            owned = user_gens.get(gen_id, 0)
            
            if is_locked:
                embed.add_field(name=f"{gen['name']} - LOCKED", value=req_text, inline=True)
            else:
                embed.add_field(
                    name=f"{gen['name']} - {gen['cost']}💰", 
                    value=f"Income: **{gen['rate']}/hr**\nOwned: **{owned}**\n{gen['desc']}", 
                    inline=True
                )
            
        embed.set_footer(text="Use /buy <item_id> to purchase. Use /collect to harvest income.")
        await interaction.response.send_message(embed=embed)

    async def item_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        all_items = {**self.items, **self.generators}
        choices = []
        for key, value in all_items.items():
            display_name = f"{value['name']} ({value['cost']}💰)"
            if current.lower() in display_name.lower():
                choices.append(app_commands.Choice(name=display_name, value=key))
        
        return choices[:25]

    @app_commands.command(name="buy", description="Buy an item or generator")
    @app_commands.autocomplete(item_id=item_autocomplete)
    async def buy(self, interaction: discord.Interaction, item_id: str):
        eco = self.get_economy()
        item = self.items.get(item_id) or self.generators.get(item_id)
        
        if not item:
            return await interaction.response.send_message(f"❌ Unknown item.", ephemeral=True)
            
        # Check Generator Requirements
        if item_id in self.generators:
            gen = item
            if gen["req_id"]:
                 user_gens = eco.get_generators(interaction.user.id)
                 prev_count = user_gens.get(gen["req_id"], 0)
                 if prev_count < gen["req_count"]:
                     req_name = self.generators[gen["req_id"]]["name"]
                     return await interaction.response.send_message(f"🔒 **Locked**: You need **{gen['req_count']}x {req_name}** first.", ephemeral=True)

        # Check Item/Upgrade Requirements
        if item_id in self.items:
            it = item
            if it.get("req_id"):
                 # Check inventory count
                 user_data = eco.get_user_data(interaction.user.id)
                 inv = user_data.get("inventory", [])
                 prev_count = inv.count(it["req_id"])
                 if prev_count < it["req_count"]:
                     req_name = self.items[it["req_id"]]["name"]
                     return await interaction.response.send_message(f"🔒 **Locked**: You need **{it['req_count']}x {req_name}** first.", ephemeral=True)

        if eco.remove_money(interaction.user.id, item['cost']):
            eco.add_item(interaction.user.id, item_id)
            
            msg = f"✅ **Purchased** {item['name']} for {item['cost']} Coins!"
            
            # Special logic for consumables
            if item_id == "lottery":
                import random
                prizes = [0, 20, 50, 200, 1500, 10000]
                weights = [589, 250, 100, 50, 10, 1]
                outcome = random.choices(prizes, weights=weights, k=1)[0]
                
                eco.add_money(interaction.user.id, outcome)
                eco.remove_item(interaction.user.id, "lottery") 
                
                if outcome >= 1000:
                    msg += f"\n🚨 **JACKPOT!** You scratched it and won **{outcome} Coins**! 🚨"
                elif outcome > 0:
                    msg += f"\n🎰 You scratched it and won **{outcome} Coins**!"
                else:
                    msg += f"\n📉 You scratched it... and lost."
            elif item_id == "coffee":
                eco.remove_item(interaction.user.id, "coffee")
                msg += f"\n☕ Defooz appreciates it."
            
            await interaction.response.send_message(msg)
        else:
             await interaction.response.send_message(f"❌ **Insufficient Funds**.", ephemeral=True)

    def calculate_user_stats(self, user_id):
        base_gain = 1.0 
        crit_chance = 0.05
        
        eco = self.get_economy()
        if not eco: return base_gain, crit_chance

        user_data = eco.get_user_data(user_id)
        inv = user_data.get("inventory", [])
        
        from collections import Counter
        counts = Counter(inv)
        
        for item_id, item in self.items.items():
            if item.get("type") == "upgrade" and item_id in counts:
                count = counts[item_id]
                if item["stat"] == "flat":
                    base_gain += item["bonus"] * count
                elif item["stat"] == "crit":
                    crit_chance += item["bonus"] * count
        
        return base_gain, crit_chance

    @app_commands.command(name="click", description="Open YOUR Mining Console (Restricted to you)")
    async def click_console(self, interaction: discord.Interaction):
        # Calculate initial stats to display
        gain, crit = self.calculate_user_stats(interaction.user.id)
        
        view = MiningView(self.get_economy(), interaction.user.id, self.items, self)
        
        embed = discord.Embed(title=f"⛏️ Mining Console - {interaction.user.display_name}", description="Click the button to mine.\n*Upgrades apply!*", color=discord.Color.dark_grey())
        embed.add_field(name="💥 Current Stats", value=f"• Gain: **{gain:.1f} Coins** / Click\n• Crit: **{crit*100:.0f}%** Chance", inline=False)
        
        await interaction.response.send_message(embed=embed, view=view)
    
    # ... (Collect, Inventory, Leaderboard same)
    @app_commands.command(name="collect", description="Harvest YOUR passive income")
    async def collect(self, interaction: discord.Interaction):
        eco = self.get_economy()
        rates = self.get_gen_rates()
        amount = eco.collect_income(interaction.user.id, rates)
        
        if amount > 0:
            await interaction.response.send_message(f"💰 **Harvest**: Collected **{amount} Coins** from your tech empire!")
        else:
            user_gens = eco.get_generators(interaction.user.id)
            total_rate = 0
            for gid, count in user_gens.items():
                if gid in rates: total_rate += rates[gid] * count
            
            if total_rate == 0:
                 await interaction.response.send_message(f"📉 You have 0 income. Buy generators first!", ephemeral=True)
            else:
                minutes_wait = (1 / total_rate) * 60
                await interaction.response.send_message(f"📉 **Too early**: You need at least 1 coin to collect.\nAt your rate (**{total_rate}/hr**), you generate 1 coin every **{minutes_wait:.1f} minutes**.", ephemeral=True)

    @app_commands.command(name="inventory", description="View owned items")
    async def inventory(self, interaction: discord.Interaction):
        eco = self.get_economy()
        data = eco.get_user_data(interaction.user.id)
        inv = data.get("inventory", [])
        gens = data.get("generators", {})
        
        desc = "**Items / Upgrades:**\n"
        from collections import Counter
        counts = Counter(inv)
        for i_id, count in counts.items():
            name = self.items.get(i_id, {"name": i_id})["name"]
            desc += f"- {name} x{count}\n"
            
        desc += "\n**Infrastructure:**\n"
        total_rate = 0
        for g_id, count in gens.items():
            if count > 0:
                gen_info = self.generators.get(g_id, {})
                name = gen_info.get("name", g_id)
                rate = gen_info.get("rate", 0)
                desc += f"- {name} x{count} ({rate*count}/hr)\n"
                total_rate += rate * count
                
        desc += f"\n⚡ **Total Profit**: {total_rate} Coins/Hour"
        await interaction.response.send_message(embed=discord.Embed(title=f"🎒 Inventory - {interaction.user.display_name}", description=desc))

    @app_commands.command(name="leaderboard", description="Top 10 Richest")
    async def leaderboard(self, interaction: discord.Interaction):
         eco = self.get_economy()
         data = eco.get_leaderboard()
         desc = "\n".join([f"**{i}.** <@{u}> : **{b:.1f}**" for i, (u, b) in enumerate(data, 1)])
         await interaction.response.send_message(embed=discord.Embed(title="🏆 Leaderboard", description=desc))

class MiningView(discord.ui.View):
    def __init__(self, eco, user_id, items_dict, shop_cog):
        super().__init__(timeout=None)
        self.eco = eco
        self.user_id = user_id
        self.items_dict = items_dict
        self.shop = shop_cog
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your console! Run `/click` to get yours.", ephemeral=True)
            return False
        return True
    
    @discord.ui.button(label="⛏️ Mine Coin", style=discord.ButtonStyle.blurple, custom_id="mine_btn")
    async def mine_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Calculate Stats dynamically (using helper)
        base_gain, crit_chance = self.shop.calculate_user_stats(interaction.user.id)
        
        import random
        gain = base_gain
        is_crit = False
        
        if random.random() < crit_chance:
            gain = base_gain * 5 
            is_crit = True
        
        self.eco.add_money(interaction.user.id, gain)
        
        if is_crit:
             await interaction.response.send_message(f"🔥 **CRIT!** Mined **{gain:.2f} Coins**!", ephemeral=True)
        else:
             await interaction.response.defer()

async def setup(bot):
    await bot.add_cog(Shop(bot))
