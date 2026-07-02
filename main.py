import discord
from discord.ext import commands
import os
from keep_alive import keep_alive

# Nastavení bota pro slash commandy
class CaliCore(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        await self.tree.sync()
        print("Slash commandy byly načteny.")

bot = CaliCore()

@bot.event
async def on_ready():
    print(f'Přihlášen jako {bot.user}!')

# Zkušební slash command
@bot.tree.command(name="ping", description="Zkontroluje, jestli CaliCore žije.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong! CaliCore je online a připraven na RP v Los Angeles.")

keep_alive()

# Spuštění
token = os.environ.get("DISCORD_TOKEN")
bot.run(token)
