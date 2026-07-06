import discord
from discord.ext import commands
from discord import app_commands
import pymongo
from cogs.profil import vytvor_profil_embed

# ==========================================
# NASTAVENÍ OPRÁVNĚNÍ A KANÁLŮ
# ==========================================
FORUM_MDT_ID = 1453745209643896933 # ID FÓRA PRO MDT SLOŽKY
POVOLENE_KANALY_ID = [1394695582760571070] # ID KANÁLU, KDE HRÁČI PÍŠOU /ID
POVOLENE_ROLE_ID = [] # Např. ID role "Ověřený hráč", nech prázdné [] pro všechny

MONGO_URI = "mongodb+srv://kubiqcz1:Aluska78@calicore.kmnmj4h.mongodb.net/?appName=CaliCore"
klient = pymongo.MongoClient(MONGO_URI)
db_cloud = klient["calicore_databaze"]
kolekce_hraci = db_cloud["hraci"]

def nacti_databazi():
    data = {}
    for hrac in kolekce_hraci.find():
        data[str(hrac["_id"])] = hrac
    return data

def uloz_databazi(data):
    for hrac_id, hrac_data in data.items():
        hrac_data["_id"] = str(hrac_id)
        kolekce_hraci.replace_one({"_id": str(hrac_id)}, hrac_data, upsert=True)

# Třída definující samotný Modal (vyskakovací okno)
class IdModal(discord.ui.Modal, title='Založení nové ID Karty'):
    jmeno = discord.ui.TextInput(
        label='RP Jméno',
        style=discord.TextStyle.short,
        placeholder='Zadej své křestní RP jméno...',
        required=True,
        max_length=50
    )
    
    prijmeni = discord.ui.TextInput(
        label='RP Příjmení',
        style=discord.TextStyle.short,
        placeholder='Zadej své RP příjmení...',
        required=True,
        max_length=50
    )

    vek = discord.ui.TextInput(
        label='RP Věk',
        style=discord.TextStyle.short,
        placeholder='Např. 25',
        required=True,
        max_length=3
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    # Co se stane, když uživatel formulář odešle
    async def on_submit(self, interaction: discord.Interaction):
        # Kontrola, jestli hráč zadal do věku opravdu číslo
        try:
            vek_int = int(self.vek.value)
        except ValueError:
            await interaction.response.send_message("❌ Věk musí být zapsán jako číslo!", ephemeral=True)
            return

        db = nacti_databazi()
        hrac_id = str(interaction.user.id)

        if hrac_id not in db:
            db[hrac_id] = {"prukazy": [], "zbrane": [], "vozidla": []}

        # Uložení dat z formuláře
        db[hrac_id]["jmeno"] = self.jmeno.value
        db[hrac_id]["prijmeni"] = self.prijmeni.value
        db[hrac_id]["vek"] = vek_int

        await interaction.response.defer(ephemeral=True)

        try:
            forum_kanal = self.bot.get_channel(FORUM_MDT_ID)
            if forum_kanal:
                embed_mdt = vytvor_profil_embed(hrac_id, interaction.user.mention, db)
                nazev_vlakna = f"Složka: {self.jmeno.value} {self.prijmeni.value}"
                
                vlakno = await forum_kanal.create_thread(
                    name=nazev_vlakna, 
                    content="Založena nová policejní složka.", 
                    embed=embed_mdt
                )
                
                db[hrac_id]["mdt_vlakno_id"] = vlakno.thread.id
                db[hrac_id]["mdt_zprava_id"] = vlakno.message.id

            uloz_databazi(db)
            await interaction.followup.send(f"✅ ID Karta pro {self.jmeno.value} {self.prijmeni.value} byla úspěšně vytvořena a uložena do databáze!")
        except Exception as e:
            await interaction.followup.send(f"❌ Nastala chyba při zakládání složky ve fóru. Zkontroluj oprávnění bota. Detail: {e}")

class IdKartaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="id", description="Založí novou ID kartu a MDT složku pomocí formuláře.")
    async def id_karta(self, interaction: discord.Interaction):
        # KONTROLA KANÁLU
        if POVOLENE_KANALY_ID and interaction.channel_id not in POVOLENE_KANALY_ID:
            kanaly = ", ".join([f"<#{k}>" for k in POVOLENE_KANALY_ID])
            await interaction.response.send_message(f"❌ Příkaz /id lze použít pouze v: {kanaly}", ephemeral=True)
            return

        # KONTROLA ROLE
        if POVOLENE_ROLE_ID:
            if not any(role.id in POVOLENE_ROLE_ID for role in interaction.user.roles):
                await interaction.response.send_message("❌ Nemáš oprávnění k založení ID karty.", ephemeral=True)
                return
        
        # Samotné vyvolání okna
        await interaction.response.send_modal(IdModal(self.bot))

async def setup(bot):
    await bot.add_cog(IdKartaCog(bot))
