import discord
from discord.ext import commands
from discord import app_commands

# --- TŘÍDA PRO FORMULÁŘ ---
class MessageModal(discord.ui.Modal, title='Odeslání Embed zprávy za bota'):
    zprava_text = discord.ui.TextInput(
        label='Obsah textu',
        style=discord.TextStyle.paragraph, 
        placeholder='Zde napiš nebo vlož text, který má bot odeslat...',
        required=True,
        max_length=4000 
    )

    barva = discord.ui.TextInput(
        label='HEX kód barvy (Volitelné)',
        style=discord.TextStyle.short, 
        placeholder='Např. #121212 nebo FF0000',
        required=False,
        max_length=7
    )

    def __init__(self, cilovy_kanal):
        super().__init__()
        self.cilovy_kanal = cilovy_kanal

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Výchozí barva (pokud nevyplníš políčko, použije se tmavá šedá jako např. v Discordu)
            embed_color = discord.Color.dark_theme()

            # Pokud hráč vyplnil nějakou barvu
            vlozena_barva = self.barva.value.strip()
            if vlozena_barva:
                # Odstraníme mřížku, pokud ji tam uživatel napsal
                vlozena_barva = vlozena_barva.replace("#", "")
                try:
                    # Převedení HEX kódu na barvu, které Discord rozumí
                    embed_color = discord.Color(int(vlozena_barva, 16))
                except ValueError:
                    pass

            # Vytvoření samotného Embedu s vybranou barvou
            embed = discord.Embed(
                description=self.zprava_text.value,
                color=embed_color
            )

            # Odeslání
            await self.cilovy_kanal.send(embed=embed)
            
            await interaction.response.send_message("✅ Embed zpráva úspěšně odeslána.", ephemeral=True)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ Bot nemá práva psát do tohoto kanálu.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Nastala chyba: {e}", ephemeral=True)


# --- HLAVNÍ TŘÍDA ---
class NapisCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="message", description="Přinutí bota napsat Embed zprávu (s volitelným HEX kódem barvy).")
    @app_commands.default_permissions(administrator=True)
    async def message_command(self, interaction: discord.Interaction):
        await interaction.response.send_modal(MessageModal(interaction.channel))

async def setup(bot):
    await bot.add_cog(NapisCog(bot))
