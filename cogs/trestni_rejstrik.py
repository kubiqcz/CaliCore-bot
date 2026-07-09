import discord
from discord.ext import commands
from discord import app_commands
import pymongo
from datetime import datetime
import zoneinfo
from cogs.profil import aktualizuj_mdt_profil

# ==========================================
# NASTAVENÍ OPRÁVNĚNÍ
# ==========================================
ROLE_POLICIE_ID = 1523660335406383164

# ==========================================
# DATABÁZE
# ==========================================
MONGO_URI = "mongodb+srv://kubiqcz1:Aluska78@calicore.kmnmj4h.mongodb.net/?appName=CaliCore"
klient = pymongo.MongoClient(MONGO_URI)
db_cloud = klient["calicore_databaze"]
kolekce_hraci = db_cloud["hraci"]

# --- TŘÍDA PRO FORMULÁŘ ---
class TrestModal(discord.ui.Modal, title='Zápis do trestního rejstříku'):
    hrac_id = discord.ui.TextInput(
        label='Číslo průkazu (ID hráče)', 
        style=discord.TextStyle.short, 
        required=True
    )
    ciny = discord.ui.TextInput(
        label='Spáchané trestné činy', 
        style=discord.TextStyle.paragraph, 
        placeholder='Např: Vražda 1. stupně, Nelegální držení zbraně...', 
        required=True
    )
    trest = discord.ui.TextInput(
        label='Udělený trest (Měsíce / Pokuta)', 
        style=discord.TextStyle.short, 
        placeholder='Např: 120 měsíců ve vězení, $150,000 pokuta', 
        required=True
    )
    poznamka = discord.ui.TextInput(
        label='Doplňující poznámka (Volitelné)', 
        style=discord.TextStyle.paragraph,
        placeholder='Pachatel byl agresivní, nebezpečí útěku...', 
        required=False
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        hrac_id_str = self.hrac_id.value.strip()

        # Kontrola, jestli má hráč vůbec založený MDT profil
        hrac = kolekce_hraci.find_one({"_id": hrac_id_str})
        if not hrac:
            return await interaction.response.send_message(f"❌ Občan s průkazem `{hrac_id_str}` nemá vedený záznam v databázi.", ephemeral=True)

        # Vygenerování aktuálního českého času
        ted = datetime.now(zoneinfo.ZoneInfo("Europe/Prague")).strftime("%d.%m.%Y %H:%M")

        zaznam = {
            "datum": ted,
            "policista": interaction.user.mention,
            "ciny": self.ciny.value,
            "trest": self.trest.value,
            "poznamka": self.poznamka.value if self.poznamka.value else "Žádná"
        }

        # Zápis záznamu PŘÍMO do databáze hráče (používáme $push, aby se vytvořil seznam trestů a staré se nesmazaly)
        kolekce_hraci.update_one({"_id": hrac_id_str}, {"$push": {"tresty": zaznam}})

        # Aktualizace grafického MDT fóra
        await aktualizuj_mdt_profil(self.bot, hrac_id_str)

        # Zpráva pro policistu, že se to povedlo
        embed = discord.Embed(title="⚖️ Záznam do rejstříku vytvořen", color=discord.Color.red())
        embed.description = f"Záznam byl úspěšně nahrán do spisu občana <@{hrac_id_str}>."
        embed.add_field(name="Spáchané činy", value=self.ciny.value, inline=False)
        embed.add_field(name="Trest", value=self.trest.value, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

class TrestniRejstrikCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="zapsat_trest", description="Zápis spáchaných zločinů do trestního rejstříku občana.")
    async def zapsat_trest_command(self, interaction: discord.Interaction):
        if ROLE_POLICIE_ID not in [role.id for role in interaction.user.roles]:
            return await interaction.response.send_message("❌ Pouze Policie může zapisovat do rejstříku!", ephemeral=True)
        
        await interaction.response.send_modal(TrestModal(self.bot))

async def setup(bot):
    await bot.add_cog(TrestniRejstrikCog(bot))
