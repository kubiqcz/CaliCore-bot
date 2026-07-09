import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import zoneinfo

# ==========================================
# NASTAVENÍ KANÁLU
# ==========================================
KANAL_DARKWEB_ID = 1394695584669241457 # Jediný kanál, kde příkaz funguje a kam se zprávy posílají

# --- TŘÍDA PRO FORMULÁŘ ---
class DarkWebModal(discord.ui.Modal, title='🌐 Šifrované připojení k Dark Webu'):
    prezdivka = discord.ui.TextInput(
        label='Krycí jméno (Alias)', 
        style=discord.TextStyle.short, 
        placeholder='Např. Kmotr, Anonymous, Stín, Neznámý...', 
        required=True,
        max_length=30
    )
    zprava = discord.ui.TextInput(
        label='Obsah inzerátu / Zprávy', 
        style=discord.TextStyle.paragraph, 
        placeholder='Co nabízíš? Zbraně, drogy, kradená auta, nebo hledáš prácičku?', 
        required=True,
        max_length=2000
    )
    kontakt = discord.ui.TextInput(
        label='Jak se s tebou spojit? (Volitelné)', 
        style=discord.TextStyle.short,
        placeholder='Např. Volejte číslo 555-1234, nebo odpovídejte sem.', 
        required=False,
        max_length=100
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        # Čas odeslání pro navození atmosféry
        ted = datetime.now(zoneinfo.ZoneInfo("Europe/Prague")).strftime("%d.%m.%Y %H:%M")

        # Vytvoření "temného" Embedu
        embed = discord.Embed(
            title="Tor Network | Nový příspěvek",
            description=f"{self.zprava.value}",
            color=discord.Color.dark_theme() # Temně šedá barva
        )
        embed.set_author(name=f"👤 Odesílatel: {self.prezdivka.value}")
        
        # Přidání kontaktu, pokud ho hráč vyplnil
        if self.kontakt.value:
            embed.add_field(name="📞 Kontakt / Instrukce", value=f"`{self.kontakt.value}`", inline=False)
            
        embed.set_footer(text=f"🔒 End-to-End Šifrování | Odesláno: {ted}")

        # Odeslání zprávy do Dark Web kanálu (Odešle ji bot, takže hráč je chráněn)
        kanal = self.bot.get_channel(KANAL_DARKWEB_ID)
        if kanal:
            await kanal.send(embed=embed)
            
            # Potvrzení pro hráče, které uvidí jen on (ephemeral)
            await interaction.response.send_message("✅ Tvoje zpráva byla zašifrována a úspěšně odeslána na Dark Web.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Chyba: Kanál pro Dark Web nebyl nalezen. Kontaktuj admina.", ephemeral=True)

class DarkWebCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="darkweb", description="Odešle plně anonymní, šifrovanou zprávu na černý trh.")
    async def darkweb_command(self, interaction: discord.Interaction):
        # Kontrola kanálu - příkaz jde použít jen v nastaveném kanálu
        if interaction.channel_id != KANAL_DARKWEB_ID:
            return await interaction.response.send_message(f"❌ K Dark Webu se lze připojit pouze z příslušného kanálu <#{KANAL_DARKWEB_ID}>.", ephemeral=True)
        
        # Otevření formuláře pro hráče
        await interaction.response.send_modal(DarkWebModal(self.bot))

async def setup(bot):
    await bot.add_cog(DarkWebCog(bot))
