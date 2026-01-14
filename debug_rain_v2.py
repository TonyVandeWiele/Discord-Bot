
import sys
import os
import inspect
import discord
from discord.ext import commands
from discord import app_commands

# Add current directory to path
sys.path.append(os.getcwd())

def analyze_cog():
    print("--- Deep Analysis ---")
    try:
        import src.cogs.economy_system as eco_module
        print(f"📂 Module File: {eco_module.__file__}")
        
        from src.cogs.economy_system import EconomySystem
        print(f"📂 Class Defined in: {inspect.getfile(EconomySystem)}")
        
        print(f"📋 Class Attributes in EconomySystem:")
        for name in dir(EconomySystem):
            if name == "rain":
                print(f"   ✅ FOUND 'rain' attribute!")
                attr = getattr(EconomySystem, name)
                print(f"      Type: {type(attr)}")
                # Check for app command info
                if hasattr(attr, "callback"):
                    print(f"      Callback: {attr.callback}")
                if hasattr(attr, "__discord_app_commands_command__"):
                     print("      Has __discord_app_commands_command__")
            elif not name.startswith("__"):
                pass # print(f"   - {name}")

        if "rain" not in dir(EconomySystem):
            print("   ❌ 'rain' attribute NOT found in checking dir()")
            
        # Check source lines just to be crazy sure
        lines, start = inspect.getsourcelines(EconomySystem)
        print(f"FILESYSTEM CHECK: Class starts at line {start}, has {len(lines)} lines")
        rain_in_source = any("def rain" in line for line in lines)
        print(f"   'def rain' text in source lines: {rain_in_source}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_cog()
