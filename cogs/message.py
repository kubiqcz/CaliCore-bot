import discord
from discord.ext import commands
from discord import app_commands

# --- TŘÍDA PRO FORMULÁŘ ---
class MessageModal(discord.ui.Modal, title='Odeslání zprávy za bota'):
    zprava_text = discord.ui.TextInput(
        label='Text zprávy',
        style=discord.TextStyle.paragraph, # Zvětšené textové pole
        placeholder='Zde napiš nebo vlož text, který má bot odeslat...',
        required=True,
        max_length=2000
    )

    def __init__(self, cilovy_kanal):
        super().__init__()
        # Uložíme si aktuální kanál
        self.cilovy_kanal = cilovy_kanal

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Bot odešle zprávu do uloženého kanálu
            await self.cilovy_kanal.send(self.zprava_text.value)
            
            # Tajné potvrzení pro admina
            await interaction.response.send_message("✅ Zpráva úspěšně odeslána.", ephemeral=True)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ Bot nemá práva psát do tohoto kanálu.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Nastala chyba: {e}", ephemeral=True)


# --- HLAVNÍ TŘÍDA ---
class NapisCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="message", description="Přinutí bota napsat zprávu do tohoto kanálu (pouze Admini).")
    @app_commands.default_permissions(administrator=True)
    async def message_command(self, interaction: discord.Interaction):
        # Přímo předáme kanál, ve kterém se nacházíme, do modalu
        await interaction.response.send_modal(MessageModal(interaction.channel))

async def setup(bot):
    await bot.add_cog(NapisCog(bot))
