import discord
from discord.ext import commands
from discord import app_commands
import random

class TryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="try", description="Rozhodne spornou RP situaci. Hodí jen Ano nebo Ne.")
    async def try_command(self, interaction: discord.Interaction):
        # Obyčejný los 50/50
        vysledek = random.choice(["✅ **Ano**", "❌ **Ne**"])
        
        # Odešle rovnou do chatu bez jakýchkoliv okecávaček
        await interaction.response.send_message(f"{interaction.user.mention} zkusil štěstí: {vysledek}")

async def setup(bot):
    await bot.add_cog(TryCog(bot))
