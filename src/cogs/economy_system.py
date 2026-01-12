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
        user_data = self.get_user_data(user_id)
        user_data["balance"] += amount
        self.save_data()

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

    @app_commands.command(name="balance", description="Check your DefoozCoins wallet")
    async def balance(self, interaction: discord.Interaction):
        bal = self.get_balance(interaction.user.id)
        await interaction.response.send_message(f"💰 **Wallet**: You have **{bal:.1f} DefoozCoins**.")

    @app_commands.command(name="pay", description="Transfer money to another user")
    async def pay(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if amount <= 0:
            return await interaction.response.send_message("❌ Nice try.", ephemeral=True)
        
        if self.remove_money(interaction.user.id, amount):
            self.add_money(user.id, amount)
            await interaction.response.send_message(f"💸 **Transfer**: Sent **{amount}** coins to {user.mention}.")
        else:
            await interaction.response.send_message("❌ **Insufficient Funds** to make this transfer.", ephemeral=True)

    # --- ADMIN COMMAND (Restricted) ---
    @app_commands.command(name="eco_give", description="Admin: Give money (Cheating)")
    async def eco_give(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if interaction.user.id != 526366336507707402:
            return await interaction.response.send_message("❌ **Access Denied**: You are not the Root Admin (Tony).", ephemeral=True)
            
        self.add_money(user.id, amount)
        await interaction.response.send_message(f"💳 **Admin**: Gave {amount} coins to {user.mention}. Inflation is rising.")

async def setup(bot):
    await bot.add_cog(EconomySystem(bot))
