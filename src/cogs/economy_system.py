import discord
from discord import app_commands
from discord.ext import commands
import json
import os

# --- CONGIGURATION ---
DATA_FILE = "economy.json"

class EconomySystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = self.load_data()

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            return {}
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump(self.data, f, indent=4)

    # Migrating to schema: {"user_id": {"balance": int, "last_daily": str_date}}
    
    def get_user_data(self, user_id: int):
        uid = str(user_id)
        # Handle Global keys vs User keys check? No, just ensure we don't treat _GLOBAL as user.
        if uid not in self.data:
            self.data[uid] = {"balance": 0, "last_daily": "", "inventory": []}
        
        # Migration for old int-only format if exists
        if isinstance(self.data[uid], int):
            self.data[uid] = {"balance": self.data[uid], "last_daily": "", "inventory": []}
            
        # Migration for missing inventory key
        if "inventory" not in self.data[uid]:
            self.data[uid]["inventory"] = []
            
        return self.data[uid]

    def get_balance(self, user_id: int) -> float:
        return self.get_user_data(user_id)["balance"]

    def add_money(self, user_id: int, amount: float):
        # TAX SYSTEM: 10% on amounts >= 1000
        tax = 0
        if amount >= 1000:
            tax = amount * 0.10
            amount -= tax
            # Add tax to jackpot? Or burn it? Let's add to Jackpot
            self.add_jackpot(int(tax))
            
        user_data = self.get_user_data(user_id)
        user_data["balance"] += amount
        self.save_data()
        return tax # Return tax amount for UI feedback

    def remove_money(self, user_id: int, amount: float) -> bool:
        user_data = self.get_user_data(user_id)
        if user_data["balance"] >= amount:
            user_data["balance"] -= amount
            self.save_data()
            return True
        return False

    def check_daily(self, user_id: int) -> bool:
        """Returns True if daily is available, False otherwise"""
        import datetime
        today = datetime.date.today().isoformat()
        user_data = self.get_user_data(user_id)
        if user_data.get("last_daily") != today:
            return True
        return False

    def claim_daily(self, user_id: int) -> bool:
        """Marks daily as claimed. Returns True if successful."""
        if self.check_daily(user_id):
            import datetime
            self.data[str(user_id)]["last_daily"] = datetime.date.today().isoformat()
            self.save_data()
            return True
        return False

    # --- V2 FEATURES (JACKPOT, INVENTORY, LEADERBOARD, GENERATORS) ---
    
    # ... (Jackpot methods remain)

    def get_jackpot(self) -> int:
        return self.data.get("_GLOBAL_JACKPOT", 1000)

    def add_jackpot(self, amount: int):
        current = self.get_jackpot()
        self.data["_GLOBAL_JACKPOT"] = current + amount
        self.save_data()

    def reset_jackpot(self):
        self.data["_GLOBAL_JACKPOT"] = 1000
        self.save_data()

    # --- INVENTORY ---
    def add_item(self, user_id: int, item_id: str):
        data = self.get_user_data(user_id)
        if item_id in ["cisco_lab", "aws_lambda", "nexus_9k", "ecs_cluster", "sagemaker", "braket"]:
             # Generator Logic: Store in "generators" dict with count
             if "generators" not in data: data["generators"] = {}
             count = data["generators"].get(item_id, 0)
             data["generators"][item_id] = count + 1
             
             # Initialize collection time if first generator ever purchased
             if "last_collection" not in data:
                 import datetime
                 data["last_collection"] = datetime.datetime.utcnow().isoformat()
        else:
            # Regular Item
            data["inventory"].append(item_id)
        self.save_data()

    def remove_item(self, user_id: int, item_id: str) -> bool:
        data = self.get_user_data(user_id)
        if item_id in data["inventory"]:
            data["inventory"].remove(item_id)
            self.save_data()
            return True
        return False

    def has_item(self, user_id: int, item_id: str) -> bool:
        data = self.get_user_data(user_id)
        return item_id in data["inventory"]

    def get_generators(self, user_id: int):
        data = self.get_user_data(user_id)
        return data.get("generators", {})

    def calculate_pending_income(self, user_id: int, rates: dict) -> int:
        data = self.get_user_data(user_id)
        last_collection_str = data.get("last_collection")
        
        if not last_collection_str or "generators" not in data:
            return 0
            
        import datetime
        last_collection = datetime.datetime.fromisoformat(last_collection_str)
        now = datetime.datetime.utcnow()
        elapsed_hours = (now - last_collection).total_seconds() / 3600
        
        income_per_hour = 0
        gens = data["generators"]
        for gen_id, count in gens.items():
            if gen_id in rates:
                income_per_hour += rates[gen_id] * count
        
        return int(income_per_hour * elapsed_hours)

    def collect_income(self, user_id: int, rates: dict) -> int:
        data = self.get_user_data(user_id)
        # Ensure last_collection exists if they have generators but it's missing (migration fix)
        if "generators" in data and data["generators"] and "last_collection" not in data:
             import datetime
             data["last_collection"] = datetime.datetime.utcnow().isoformat()
             self.save_data()
             return 0

        amount = self.calculate_pending_income(user_id, rates)
        if amount > 0:
            import datetime
            self.add_money(user_id, amount)
            data["last_collection"] = datetime.datetime.utcnow().isoformat()
            self.save_data()
        return amount

    # ... (Leaderboard remains)

    def get_leaderboard(self):
        # Filter out global keys
        users = []
        for k, v in self.data.items():
            if k.startswith("_"): continue
            if isinstance(v, dict):
                 users.append((k, v["balance"]))
        # Sort desc
        return sorted(users, key=lambda x: x[1], reverse=True)[:10]

    def get_all_users_data(self):
        """Returns list of (user_id, data_dict) for all users"""
        users = []
        for k, v in self.data.items():
            if k.startswith("_"): continue
            if isinstance(v, dict):
                 users.append((k, v))
        return users

    @app_commands.command(name="balance", description="Check your DefoozCoins wallet")
    async def balance(self, interaction: discord.Interaction):
        bal = self.get_balance(interaction.user.id)
        await interaction.response.send_message(f"💰 **Wallet**: You have **{bal:.1f} DefoozCoins**.")

    # Pay command removed


    # --- LOAN SYSTEM & REDISTRIBUTION ---
    
    def create_loan(self, lender_id: int, borrower_id: int, amount: float, interest_percent: int):
        import uuid
        import datetime
        
        loan_id = str(uuid.uuid4())[:8]
        loan_data = {
            "id": loan_id,
            "lender": lender_id,
            "borrower": borrower_id,
            "amount": amount,
            "interest": interest_percent,
            "repayment": amount * (1 + interest_percent / 100),
            "date": datetime.date.today().isoformat(),
            "status": "pending"
        }
        
        if "_LOANS" not in self.data: self.data["_LOANS"] = []
        self.data["_LOANS"].append(loan_data)
        self.save_data()
        return loan_id, loan_data["repayment"]

    def confirm_loan(self, loan_id: str):
        # Helper to activate a loan
        pass # Implemented in command logic for simplicity or here? 
        # Actually proper way: Command creates pending, borrower accepts. 
        # Simply: User A loans to User B -> Money removed from A, added to B (with tax?).
        # For simplicity: Direct loan.
        pass

    def get_user_loans(self, user_id: int):
        loans = self.data.get("_LOANS", [])
        return [l for l in loans if l["borrower"] == user_id or l["lender"] == user_id]

    def pay_loan(self, loan_id: str, payer_id: int):
        loans = self.data.get("_LOANS", [])
        for loan in loans:
            if loan["id"] == loan_id and loan["status"] == "pending":
                if loan["borrower"] != payer_id: return "not_borrower"
                
                repayment = loan["repayment"]
                if self.remove_money(payer_id, repayment):
                    self.add_money(loan["lender"], repayment) # Tax applies on repayment income
                    loan["status"] = "paid"
                    self.save_data()
                    return "success"
                else:
                    return "insufficient_funds"
        return "not_found"

    
    # --- RAIN SYSTEM ---

    def distribute_money(self, sender_id: int, amount: float):
        """Helper for instant redistribution (Casino)"""
        if not self.remove_money(sender_id, amount):
            return False, 0
            
        targets = []
        for uid in self.data:
             if uid.isdigit() and int(uid) != sender_id:
                 targets.append(int(uid))
        
        if not targets:
            self.add_money(sender_id, amount) 
            return False, 0
            
        share = amount / len(targets)
        for uid in targets:
            self.add_money(uid, share)
            
        return True, share

    @app_commands.command(name="rain", description="Make it Rain! (Interactive 60s Pool)")
    async def rain(self, interaction: discord.Interaction, amount: int):
         if amount <= 0: return await interaction.response.send_message("❌ Invalid amount.", ephemeral=True)
         
         if not self.remove_money(interaction.user.id, amount):
             return await interaction.response.send_message("❌ You are too poor to make it rain.", ephemeral=True)

         # Create View
         view = RainView(self.bot, amount, interaction.user.id)
         await interaction.response.send_message(f"🌧️ **MAKE IT RAIN!** 🌧️\n**{interaction.user.display_name}** is dropping **{amount} Coins**!\n\n👇 **Click the button to join the pool!**\n⏳ *Ends in 60 seconds...*", view=view)
         view.message = await interaction.original_response()

    class RainView(discord.ui.View):
        def __init__(self, bot, amount, owner_id):
            super().__init__(timeout=60)
            self.bot = bot
            self.amount = amount
            self.owner_id = owner_id
            self.participants = set()
            self.message = None

        @discord.ui.button(label="💸 Grab Coins", style=discord.ButtonStyle.success)
        async def grab(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id == self.owner_id:
                 return await interaction.response.send_message("❌ You dropped it, you can't pick it up!", ephemeral=True)
            
            if interaction.user.id in self.participants:
                return await interaction.response.send_message("❌ You are already in the pool!", ephemeral=True)
            
            self.participants.add(interaction.user.id)
            await interaction.response.send_message("✅ You joined the rain pool!", ephemeral=True)
            
            # Update button label
            button.label = f"💸 Grab Coins ({len(self.participants)})"
            await self.message.edit(view=self)

        async def on_timeout(self):
            if not self.participants:
                # Refund owner
                eco = self.bot.get_cog("EconomySystem")
                if eco: eco.add_money(self.owner_id, self.amount)
                if self.message: await self.message.edit(content=f"❌ **RAIN OVER**: No one picked up the **{self.amount} Coins**. Refunded to {self.owner_id}.", view=None)
                return

            share = self.amount / len(self.participants)
            eco = self.bot.get_cog("EconomySystem")
            if eco:
                for uid in self.participants:
                    eco.add_money(uid, share) # Tax individual shares? Maybe. For now, no double tax.
            
            if self.message:
                await self.message.edit(content=f"🌧️ **RAIN OVER!**\n**{self.amount} Coins** shared among **{len(self.participants)}** people.\nEveryone got **{share:.1f} Coins**!", view=None)

    @app_commands.command(name="loan", description="Offer a loan to a user")
    async def loan(self, interaction: discord.Interaction, user: discord.Member, amount: int, interest: int):
        if amount <= 0 or interest < 0:
            return await interaction.response.send_message("❌ Invalid parameters.", ephemeral=True)
        
        # Immediate transfer model:
        # lender loses money, borrower gets money. Loan recorded for repayment.
        if self.remove_money(interaction.user.id, amount):
            self.add_money(user.id, amount) # Taxed
            
            lid, repay = self.create_loan(interaction.user.id, user.id, amount, interest)
            
            await interaction.response.send_message(f"💸 **LOAN ISSUED**\n{interaction.user.mention} loaned **{amount}** to {user.mention} at **{interest}%** interest.\n💳 **Repayment Due**: {repay:.1f} (ID: `{lid}`)\n*Use `/payloan {lid}` to repay.*")
        else:
            await interaction.response.send_message("❌ Insufficient funds to lend.", ephemeral=True)

    @app_commands.command(name="payloan", description="Repay a loan")
    async def payloan(self, interaction: discord.Interaction, loan_id: str):
        res = self.pay_loan(loan_id, interaction.user.id)
        if res == "success":
            await interaction.response.send_message("✅ **Loan Repaid!** You are free.")
        elif res == "insufficient_funds":
            await interaction.response.send_message("❌ You don't have the money to repay this loan.", ephemeral=True)
        elif res == "not_borrower":
             await interaction.response.send_message("❌ This is not your loan to repay.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Loan not found or already paid.", ephemeral=True)

    @app_commands.command(name="loans", description="View your active loans")
    async def loans(self, interaction: discord.Interaction):
        loans = self.get_user_loans(interaction.user.id)
        if not loans:
             return await interaction.response.send_message("You have no active loans.", ephemeral=True)
        
        embed = discord.Embed(title="📜 Your Loans", color=discord.Color.gold())
        for l in loans:
            status = "🔴 Unpaid" if l["status"] == "pending" else "🟢 Paid"
            role = "Borrower" if l["borrower"] == interaction.user.id else "Lender"
            other = l["lender"] if role == "Borrower" else l["borrower"]
            
            embed.add_field(
                name=f"ID: {l['id']} ({role})", 
                value=f"Amount: {l['amount']}\nRepayment: **{l['repayment']:.1f}**\nTo/From: <@{other}>\nStatus: {status}", 
                inline=False
            )
        await interaction.response.send_message(embed=embed)

    # Commands 'pay' and 'eco_give' removed by request


async def setup(bot):
    await bot.add_cog(EconomySystem(bot))
