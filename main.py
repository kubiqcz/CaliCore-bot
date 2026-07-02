import discord
from discord.ext import commands
import os
from keep_alive import keep_alive

class CaliCore(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        # Tento kousek projde složku 'cogs' a načte všechny soubory s příponou .py
        if os.path.exists('./cogs'):
            for filename in os.listdir('./cogs'):
                if filename.endswith('.py'):
                    await self.load_extension(f'cogs.{filename[:-3]}')
        
        await self.tree.sync()
        print("Všechny moduly a commandy byly načteny.")

bot = CaliCore()

@bot.event
async def on_ready():
    print(f'Přihlášen jako {bot.user}!')

keep_alive()

token = os.environ.get("DISCORD_TOKEN")
bot.run(token)
