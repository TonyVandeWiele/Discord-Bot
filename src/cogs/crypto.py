import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
import aiohttp
import random
import datetime
import asyncio
import aiofiles

DATA_FILE = "crypto.json"

# Components stats
COMPONENTS = {
    # RACKS (Hold Components)
    "rack_small": {"name": "🗑️ DIY Shelf", "cost": 1000, "slots": 2, "type": "rack"}, 
    "rack_medium": {"name": "🗄️ Server Rack", "cost": 5000, "slots": 8, "type": "rack"},
    "rack_large": {"name": "🕋 Data Center Row", "cost": 50000, "slots": 20, "type": "rack"},
    
    # GPUS (Hashrate)
    "gpu_1050ti": {"name": "📼 GTX 1050 Ti", "cost": 750, "hash": 2, "power": 10, "type": "gpu", "req": None},
    "gpu_3060": {"name": "📼 RTX 3060", "cost": 4000, "hash": 12, "power": 25, "type": "gpu", "req": "gpu_1050ti"},
    "gpu_4090": {"name": "🔥 RTX 4090", "cost": 25000, "hash": 50, "power": 80, "type": "gpu", "req": "gpu_3060"},
    "asic_s19": {"name": "⚒️ Antminer S19", "cost": 120000, "hash": 200, "power": 250, "type": "gpu", "req": "gpu_4090"}, 
    
    # CPUS 
    "cpu_i3": {"name": "💻 Intel i3", "cost": 500, "hash": 0.5, "type": "cpu", "req": None},
    "cpu_threadripper": {"name": "🧠 Threadripper", "cost": 10000, "hash": 25, "type": "cpu", "req": "cpu_i3"}
}

class CryptoSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = self.load_data()
        self.btc_price = 100000.0 # Default fallback
        self.last_price_update = datetime.datetime.min
        self.session = None # Initialize session placeholder
        
        # Start loops
        self.mining_loop.start()
        self.price_loop.start()

    async def cog_load(self):
        # No setup needed for local session
        pass

    async def cog_unload(self):
        self.mining_loop.cancel()
        self.price_loop.cancel()

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            return {}
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    async def save_data(self):
        try:
            # Dump to string (CPU bound but fast for small data)
            content = json.dumps(self.data, indent=4)
            # Write asynchronously (I/O bound)
            async with aiofiles.open(DATA_FILE, "w") as f:
                await f.write(content)
        except Exception as e:
            print(f"⚠️ [CRYPTO] Save Error: {e}")
            
    def get_user_data(self, user_id: int):
        uid = str(user_id)
        if uid not in self.data:
            self.data[uid] = {
                "btc": 0.0,
                "components": [], # List of item_ids
                "last_mined": datetime.datetime.utcnow().isoformat()
            }
        return self.data[uid]

    def get_hashrate(self, user_id: int):
        data = self.get_user_data(user_id)
        total_hash = 0
        
        # Calculate from components
        for item_id in data["components"]:
            item = COMPONENTS.get(item_id)
            if item:
                total_hash += item.get("hash", 0)
        
        return total_hash

    def get_rack_capacity(self, user_id: int):
        data = self.get_user_data(user_id)
        slots = 0
        # Default 1 slot for free?
        slots = 1 
        
        for item_id in data["components"]:
            item = COMPONENTS.get(item_id)
            if item and item.get("type") == "rack":
                slots += item["slots"]
        return slots

    def get_component_count(self, user_id: int):
        data = self.get_user_data(user_id)
        count = 0
        for item_id in data["components"]:
            item = COMPONENTS.get(item_id)
            if item and item.get("type") in ["gpu", "cpu"]:
                count += 1
        return count

    # --- TASKS ---


    async def fetch_btc_price(self):
        """Helper to fetch price (used by loop and command)"""
        async with aiohttp.ClientSession() as session:
            try:
                # Add timeout and user-agent to prevent hanging/blocking
                headers = {'User-Agent': 'DefoozBot/1.0'}
                async with session.get(
                    'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd', 
                    headers=headers, 
                    timeout=5
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.btc_price = data['bitcoin']['usd']
                        self.last_price_update = datetime.datetime.utcnow()
                        print(f"📈 [CRYPTO] Updated BTC Price: ${self.btc_price}")
                        return self.btc_price
                    elif resp.status == 429:
                        print("⚠️ [CRYPTO] Rate Limited (429). Use cached.")
                        return None
                    else:
                        print(f"⚠️ [CRYPTO] Price fetch failed {resp.status}")
                        return None
            except asyncio.TimeoutError:
                print("⚠️ [CRYPTO] Timeout fetching price.")
                return None
            except Exception as e:
                print(f"⚠️ [CRYPTO] Error fetching price: {e}")
                return None

    @tasks.loop(minutes=10)
    async def price_loop(self):
        await self.fetch_btc_price()

    @tasks.loop(minutes=1)
    async def mining_loop(self):
        # Add BTC to all users based on hashrate
        for uid in list(self.data.keys()):
            if not uid.isdigit(): continue
            
            user_id = int(uid)
            hashrate = self.get_hashrate(user_id)
            
            if hashrate > 0:
                # Formula: 1 MH/s = 0.0000001 BTC / min (Simple balance)
                btc_gain = hashrate * 0.0000001
                self.data[uid]["btc"] += btc_gain
        
        # Optimization: Don't save every minute if not needed.
        # But to be safe for now, let's keep it but use the async version.
        # Ideally, save every 5 mins.
        if datetime.datetime.utcnow().minute % 5 == 0:
             await self.save_data()

    @price_loop.before_loop
    async def before_price_loop(self):
        await self.bot.wait_until_ready()

    @mining_loop.before_loop
    async def before_mining_loop(self):
        await self.bot.wait_until_ready()

    # --- VIEWS ---
    
    class ShopView(discord.ui.View):
        def __init__(self, bot, components, userId):
            super().__init__(timeout=120)
            self.bot = bot
            self.components = components
            self.userId = userId
            
            # Create Select Options
            options = []
            for cid, cdata in components.items():
                # Add price to description
                label = f"{cdata['name']} ({cdata['cost']}💰)"
                # Truncate if needed
                desc = f"Hash: {cdata.get('hash', 0)} MH/s | Slots: {cdata.get('slots', 0)}"
                options.append(discord.SelectOption(label=label, description=desc, value=cid))
            
            # Divide into chunks if > 25 (discord limit)
            # For now assuming < 25 items
            self.add_item(self.ShopSelect(options, bot, userId, components))

        class ShopSelect(discord.ui.Select):
            def __init__(self, options, bot, userId, components):
                super().__init__(placeholder="🛒 Select an item to buy...", min_values=1, max_values=1, options=options)
                self.bot = bot
                self.userId = userId
                self.components = components

            async def callback(self, interaction: discord.Interaction):
                if interaction.user.id != self.userId:
                    return await interaction.response.send_message("❌ Open your own shop!", ephemeral=True)
                
                item_id = self.values[0]
                item = self.components.get(item_id)
                
                if not item: return
                
                eco = self.bot.get_cog("EconomySystem")
                crypto = self.bot.get_cog("CryptoSystem") # Self reference workaround
                
                if not eco or not crypto: return
                
                # Logic copied from buy command
                # Check money
                if not eco.remove_money(interaction.user.id, item["cost"]):
                    return await interaction.response.send_message(f"❌ **Insufficient Funds** for {item['name']}.", ephemeral=True)

                # Check capacity
                if item["type"] != "rack":
                    slots = crypto.get_rack_capacity(interaction.user.id)
                    used = crypto.get_component_count(interaction.user.id)
                    if used >= slots:
                        eco.add_money(interaction.user.id, item["cost"])
                        return await interaction.response.send_message(f"❌ **No Space!** {used}/{slots} slots. Buy a Rack!", ephemeral=True)

                # Add item
                data = crypto.get_user_data(interaction.user.id)
                data["components"].append(item_id)
                await crypto.save_data()
                
                await interaction.response.send_message(f"✅ **Purchased** {item['name']}!", ephemeral=True)
                
                # Reset view to clear selection
                try:
                    await interaction.message.edit(view=self.view)
                except:
                    pass


    @app_commands.command(name="crypto_price", description="Check current Bitcoin Price (Updated every 10m)")
    async def crypto_price(self, interaction: discord.Interaction):
        # Use cached data to avoid API Latency / Timeouts / Rate Limits
        price = self.btc_price
        
        # Format timestamp
        if self.last_price_update != datetime.datetime.min:
            ts = int(self.last_price_update.timestamp())
            time_str = f"<t:{ts}:R>"
        else:
            time_str = "Unknown"
            
        embed = discord.Embed(title="📈 Bitcoin Price", color=discord.Color.gold())
        embed.add_field(name="Current Price", value=f"**${price:,.2f}** (USD)", inline=False)
        embed.add_field(name="Last Updated", value=time_str, inline=False)
        embed.set_footer(text="Prices update automatically every 10 minutes.")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="crypto_shop", description="Buy mining equipment")
    async def crypto_shop(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🛒 Crypto Mining Shop", color=discord.Color.orange())
        
        # Group by type
        racks = []
        gpus = []
        
        for k, v in COMPONENTS.items():
            if v["type"] == "rack": racks.append(f"**{v['name']}** - {v['cost']}💰 ({v['slots']} slots)")
            else: gpus.append(f"**{v['name']}** - {v['cost']}💰 ({v['hash']} MH/s)")
            
        embed.add_field(name="🗄️ Racks (Storage)", value="\n".join(racks), inline=False)
        embed.add_field(name="⛏️ Miners (Hashrate)", value="\n".join(gpus), inline=False)
        embed.set_footer(text="Select an item below to purchase instantly!")
        
        view = self.ShopView(self.bot, COMPONENTS, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)



    @app_commands.command(name="crypto_stats", description="View your mining rig")
    async def crypto_stats(self, interaction: discord.Interaction):
        data = self.get_user_data(interaction.user.id)
        hashrate = self.get_hashrate(interaction.user.id)
        slots = self.get_rack_capacity(interaction.user.id)
        used = self.get_component_count(interaction.user.id)
        btc = data["btc"]
        value_usd = btc * self.btc_price
        
        # Simplified convert rate for game: 1 USD ~ 1 Coin (Arbitrary balance)
        # Actually let's make 1 USD = 1 Coin for simplicity of display
        
        desc = f"**Balance**: `{btc:.8f} BTC` (~ {value_usd:,.0f} Coins)\n"
        desc += f"**Hashrate**: `{hashrate} MH/s`\n"
        desc += f"**Rig Capacity**: `{used}/{slots}` slots used.\n\n"
        
        # List items
        from collections import Counter
        counts = Counter(data["components"])
        if counts:
            desc += "**Equipment**:\n"
            for i_id, count in counts.items():
                name = COMPONENTS[i_id]["name"]
                desc += f"- {name} x{count}\n"
        
        await interaction.response.send_message(embed=discord.Embed(title=f"⛏️ Mining Rig - {interaction.user.display_name}", description=desc, color=discord.Color.gold()))

    @app_commands.command(name="crypto_sell", description="Sell BTC for DefoozCoins")
    async def crypto_sell(self, interaction: discord.Interaction, amount_btc: float):
        data = self.get_user_data(interaction.user.id)
        if amount_btc <= 0: return await interaction.response.send_message("❌ Invalid amount.", ephemeral=True)
        if data["btc"] < amount_btc:
             return await interaction.response.send_message("❌ You don't have enough BTC.", ephemeral=True)
             
        # Conversion
        # Rate: 1 BTC = self.btc_price Coins
        coins = amount_btc * self.btc_price
        
        data["btc"] -= amount_btc
        await self.save_data()
        
        eco = self.bot.get_cog("EconomySystem")
        if eco:
            # TAX APPLIES HERE? Yes, income.
            tax = eco.add_money(interaction.user.id, coins)
            
        await interaction.response.send_message(f"💱 **SOLD** {amount_btc} BTC for **{coins:,.0f} Coins**.\n*(Tax Paid: {tax:,.0f} Coins)*")

async def setup(bot):
    await bot.add_cog(CryptoSystem(bot))
