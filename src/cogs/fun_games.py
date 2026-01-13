import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio

class FunGames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_economy(self):
        return self.bot.get_cog("EconomySystem")

    @app_commands.command(name="slots", description="Play Slots (Bet: 50, 500, or 5000)")
    @app_commands.choices(bet=[
        app_commands.Choice(name="50 Coins", value=50),
        app_commands.Choice(name="500 Coins", value=500),
        app_commands.Choice(name="5000 Coins", value=5000)
    ])
    async def slots(self, interaction: discord.Interaction, bet: app_commands.Choice[int]):
        eco = self.get_economy()
        if not eco: return await interaction.response.send_message("❌ Economy System Offline.", ephemeral=True)
        
        cost = bet.value
        
        # Initial Check
        if eco.get_balance(interaction.user.id) < cost:
             return await interaction.response.send_message(f"❌ **Broke Alert**: You need {cost} coins.", ephemeral=True)

        # Start the Session View
        view = SlotsView(self.bot, interaction.user.id, eco, cost)
        await interaction.response.send_message(f"🎰 **Casino Session ({cost}💰)**\nPress **Spin** to play!", view=view)
        # Verify initial balance/cost in the view callback
        
    @app_commands.command(name="casino_info", description="View Casino Statistics & RTP")
    async def casino_info(self, interaction: discord.Interaction):
        # Precise Math based on standard weights
        # Total Weight: 72 (13*4 + 10 + 5*2)
        
        embed = discord.Embed(title="🎰 Defooz Casino Stats", color=discord.Color.green())
        embed.description = "The casino operates on a weighted RNG system.\n**Total Weight Pool**: 72"
        
        # Table Header
        header = "| Type | Combo | Chance | Payout |"
        sep = "| :--- | :--- | :--- | :--- |"
        
        # Data
        # Jackpot (777) - 5/72 ^ 3
        row1 = "| **JACKPOT** | 7️⃣-7️⃣-7️⃣ | **0.03%** (1/2,986) | **Global Pot** |"
        # Diamond (555) - 5/72 ^ 3
        row2 = "| **Diamond** | 💎-💎-💎 | **0.03%** (1/2,986) | **55x** |"
        # Triple Fruit - 4 * (13/72 ^ 3)
        row3 = "| **Triple** | 🍒/🍊/🍋/🍇 | **2.35%** (1/42) | **16x** |"
        # Triple Poop - 10/72 ^ 3
        row4 = "| **FAILURE** | 💩-💩-💩 | **0.27%** (1/373) | **0x** (Lost) |"
        # Pair - Approx 25-30%
        row5 = "| **Pair** | Any Pair | **~28%** (1/3.5) | **2x** |"
        
        table = f"\n{header}\n{sep}\n{row1}\n{row2}\n{row3}\n{row4}\n{row5}\n"
        
        embed.add_field(name="📊 Probability Table", value=table, inline=False)
        
        embed.add_field(name="RTP (Return to Player)", value="**~97.0%**\n*The house always wins (eventually).*")
        embed.set_footer(text="Gamble responsibly.")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="jackpot", description="Check the Global Progressive Jackpot")
    async def jackpot(self, interaction: discord.Interaction):
        eco = self.get_economy()
        amount = eco.get_jackpot()
        await interaction.response.send_message(f"🎰 **Current Global Jackpot**: `{amount}` Coins!\n*Spin 7️⃣-7️⃣-7️⃣ to win it all.*")

    @app_commands.command(name="dice", description="Roll a dice (Bet 10, Win 50 on 6)")
    async def dice(self, interaction: discord.Interaction):
        eco = self.get_economy()
        cost = 10
        if eco and not eco.remove_money(interaction.user.id, cost):
             return await interaction.response.send_message(f"❌ You are too poor. Cost: {cost}.", ephemeral=True)
        
        roll = random.randint(1, 6)
        if roll == 6:
            win = 50
            if eco: eco.add_money(interaction.user.id, win)
            msg = f"🎲 You rolled a **6**! **WINNER!** (+{win} coins)"
        else:
            msg = f"🎲 You rolled a {roll}. (Lost {cost} coins)."
            
        await interaction.response.send_message(msg)

class SlotsView(discord.ui.View):
    def __init__(self, bot, user_id, eco, cost):
        super().__init__(timeout=120)
        self.bot = bot
        self.user_id = user_id
        self.eco = eco
        self.cost = cost
        self.session_profit = 0
        self.spins = 0
        
        # Adjust button label
        self.children[0].label = f"🎰 SPIN ({cost}💰)"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    @discord.ui.button(label="🎰 SPIN", style=discord.ButtonStyle.primary)
    async def spin(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Pay Cost
        if not self.eco.remove_money(self.user_id, self.cost):
            return await interaction.response.send_message("❌ **Insufficient Funds** to continue session.", ephemeral=True)
            
        self.spins += 1
        self.session_profit -= self.cost
        
        # Game Logic
        emojis = ["🍒", "🍊", "🍋", "🍇", "💎", "💩", "7️⃣"]
        weights = [13, 13, 13, 13, 5, 10, 5] 
        results = random.choices(emojis, weights=weights, k=3)
        a, b, c = results[0], results[1], results[2]
        
        winnings = 0
        result_text = "LOST"
        outcome_color = discord.Color.red()
        
        if a == b == c:
            if a == "7️⃣":
                jackpot = self.eco.get_jackpot()
                winnings = jackpot
                self.eco.reset_jackpot()
                result_text = "🚨 **MEGA JACKPOT** 🚨"
                outcome_color = discord.Color.gold()
            elif a == "💎":
                winnings = self.cost * 55 # 55x Multiplier
                result_text = "💎 **DIAMOND WIN** 💎"
                outcome_color = discord.Color.purple()
            elif a == "💩":
                winnings = 0
                result_text = "💩 **CRITICAL FAILURE** 💩"
            else:
                winnings = self.cost * 16 # 16x Multiplier
                result_text = "**TRIPLE WIN!**"
                outcome_color = discord.Color.green()
        elif a == b or b == c or a == c:
            if "💩" in [a,b,c]:
                winnings = 0
                result_text = "Poop ruined the pair."
            else:
                winnings = self.cost * 2 # 2x Multiplier
                result_text = "Double Win"
                outcome_color = discord.Color.blue()
        
        if winnings > 0:
            self.eco.add_money(self.user_id, winnings)
            self.session_profit += winnings
            
        # UI Update
        embed = discord.Embed(title="🎰 Defooz Slots", color=outcome_color)
        embed.description = f"# [{a}|{b}|{c}]\n### {result_text}\n"
        
        if winnings > 0:
            embed.description += f"Won: **+{winnings}**"
        else:
             self.eco.add_jackpot(int(self.cost * 0.1))
        
        # Stats Footer
        profit_str = f"+{self.session_profit}" if self.session_profit >= 0 else f"{self.session_profit}"
        embed.set_footer(text=f"Session Profit: {profit_str} Coins | Spins: {self.spins}")
        
        # Check for HUGE win (Redistribute)
        if winnings >= 1500:
            # Create a new view for this special moment
            view = RedistributeView(self.bot, self.user_id, winnings)
            await interaction.response.edit_message(embed=embed, view=view)
            return

        await interaction.response.edit_message(content=None, embed=embed, view=self)

class RedistributeView(discord.ui.View):
    def __init__(self, bot, user_id, amount):
        super().__init__(timeout=60)
        self.bot = bot
        self.user_id = user_id
        self.amount = amount
        self.value = None

    @discord.ui.button(label="🌧️ Make it Rain (Share 20%)", style=discord.ButtonStyle.success, emoji="🌧️")
    async def rain(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Not your win!", ephemeral=True)
            
        amount_to_share = int(self.amount * 0.20)
        eco = self.bot.get_cog("EconomySystem")
        if eco:
            success, share = eco.distribute_money(interaction.user.id, amount_to_share)
            if success:
                await interaction.response.edit_message(content=f"🌧️ **YOU ARE A LEGEND!**\nYou shared **{amount_to_share} Coins** with the server!\nEveryone got **{share:.1f} Coins**!", view=None)
            else:
                    await interaction.response.send_message("❌ Failed to process.", ephemeral=True)
        self.stop()

    @discord.ui.button(label="🏃 Keep it all", style=discord.ButtonStyle.secondary)
    async def keep(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id: return
        await interaction.response.edit_message(content="💰 You kept it all. Scrooge.", view=None)
        self.stop()

async def setup(bot):
    await bot.add_cog(FunGames(bot))
