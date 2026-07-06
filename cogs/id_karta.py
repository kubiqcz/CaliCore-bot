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

class IdModal(discord.ui.Modal, title='Vydání Průkazu Totožnosti'):
    roblox_nick = discord.ui.TextInput(
        label='Roblox Nick',
        style=discord.TextStyle.short,
        placeholder='Tvůj přesný nick na Robloxu...',
        required=True,
        max_length=50
    )

    jmeno = discord.ui.TextInput(
        label='Jméno a příjmení',
        style=discord.TextStyle.short,
        placeholder='John Pork...',
        required=True,
        max_length=50
    )

    datum_narozeni = discord.ui.TextInput(
        label='Datum narození postavy DD/MM/YYYY',
        style=discord.TextStyle.short,
        placeholder='18/06/2001',
        required=True,
        max_length=20
    )

    misto_narozeni = discord.ui.TextInput(
        label='Místo narození postavy',
        style=discord.TextStyle.short,
        placeholder='Los Angeles, CA',
        required=True,
        max_length=100
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        db = nacti_databazi()
        hrac_id = str(interaction.user.id)

        if hrac_id not in db:
            db[hrac_id] = {"prukazy": [], "zbrane": [], "vozidla": []}

        # Uložení všech nových dat z formuláře do databáze
        db[hrac_id]["roblox_nick"] = self.roblox_nick.value
        db[hrac_id]["jmeno"] = self.jmeno.value
        db[hrac_id]["datum_narozeni"] = self.datum_narozeni.value
        db[hrac_id]["misto_narozeni"] = self.misto_narozeni.value

        await interaction.response.defer(ephemeral=True)

        try:
            forum_kanal = self.bot.get_channel(FORUM_MDT_ID)
            if forum_kanal:
                embed_mdt = vytvor_profil_embed(hrac_id, interaction.user.mention, db)
                
                # ZDE BÝVALA CHYBA: už nevoláme self.prijmeni.value
                nazev_vlakna = f"Složka: {self.jmeno.value}"
                
                vlakno = await forum_kanal.create_thread(
                    name=nazev_vlakna, 
                    content="Založena nová policejní složka.", 
                    embed=embed_mdt
                )
                
                db[hrac_id]["mdt_vlakno_id"] = vlakno.thread.id
                db[hrac_id]["mdt_zprava_id"] = vlakno.message.id

            uloz_databazi(db)
            # ZDE BÝVALA CHYBA: už nevoláme self.prijmeni.value
            await interaction.followup.send(f"✅ Průkaz totožnosti pro {self.jmeno.value} byl vytvořen!")
        except Exception as e:
            await interaction.followup.send(f"❌ Nastala chyba při zakládání složky ve fóru. Zkontroluj oprávnění. Detail: {e}")

class IdKartaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="id", description="Založí novou ID kartu a MDT složku pomocí formuláře.")
    async def id_karta(self, interaction: discord.Interaction):
        if POVOLENE_KANALY_ID and interaction.channel_id not in POVOLENE_KANALY_ID:
            kanaly = ", ".join([f"<#{k}>" for k in POVOLENE_KANALY_ID])
            await interaction.response.send_message(f"❌ Příkaz /id lze použít pouze v: {kanaly}", ephemeral=True)
            return

        if POVOLENE_ROLE_ID:
            if not any(role.id in POVOLENE_ROLE_ID for role in interaction.user.roles):
                await interaction.response.send_message("❌ Nemáš oprávnění k založení ID karty.", ephemeral=True)
                return
        
        await interaction.response.send_modal(IdModal(self.bot))

async def setup(bot):
    await bot.add_cog(IdKartaCog(bot))
