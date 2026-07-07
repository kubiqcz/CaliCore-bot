import discord
from discord.ext import commands
from discord import app_commands

class NapisCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Změněno name="message"
    @app_commands.command(name="message", description="Přinutí bota napsat libovolnou zprávu (pouze pro Adminy).")
    @app_commands.describe(
        zprava="Text, který má bot odeslat", 
        kanal="Kanál, kam to má poslat (když nevybereš, pošle se sem)"
    )
    @app_commands.default_permissions(administrator=True)
    async def message_command(self, interaction: discord.Interaction, zprava: str, kanal: discord.TextChannel = None):
        # Pokud nevybereš kanál, nastaví se ten, ve kterém zrovna píšeš
        cilovy_kanal = kanal if kanal else interaction.channel
        
        try:
            # Bot odešle zprávu
            await cilovy_kanal.send(zprava)
            
            # Tobě se ukáže tajné potvrzení, že to klaplo (ephemeral)
            await interaction.response.send_message(f"✅ Zpráva úspěšně odeslána do {cilovy_kanal.mention}", ephemeral=True)
            
        except discord.Forbidden:
            # Kdyby se bot pokusil psát někam, kam nemá přístup
            await interaction.response.send_message(f"❌ Bot nemá práva psát do kanálu {cilovy_kanal.mention}.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Nastala chyba: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(NapisCog(bot))
