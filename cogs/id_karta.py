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

class IdKartaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="id", description="Založí novou ID kartu a MDT složku.")
    @app_commands.describe(jmeno="Tvé RP jméno", prijmeni="Tvé RP příjmení", vek="Tvůj RP věk")
    async def id_karta(self, interaction: discord.Interaction, jmeno: str, prijmeni: str, vek: int):
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

        db = nacti_databazi()
        hrac_id = str(interaction.user.id)

        if hrac_id not in db:
            db[hrac_id] = {"prukazy": [], "zbrane": [], "vozidla": []}

        db[hrac_id]["jmeno"] = jmeno
        db[hrac_id]["prijmeni"] = prijmeni
        db[hrac_id]["vek"] = vek

        await interaction.response.defer(ephemeral=True)

        try:
            forum_kanal = self.bot.get_channel(FORUM_MDT_ID)
            if forum_kanal:
                embed_mdt = vytvor_profil_embed(hrac_id, interaction.user.mention, db)
                nazev_vlakna = f"Složka: {jmeno} {prijmeni}"
                
                vlakno = await forum_kanal.create_thread(name=nazev_vlakna, content="Založena nová policejní složka.", embed=embed_mdt)
                
                db[hrac_id]["mdt_vlakno_id"] = vlakno.thread.id
                db[hrac_id]["mdt_zprava_id"] = vlakno.message.id

            uloz_databazi(db)
            await interaction.followup.send(f"✅ ID Karta pro {jmeno} {prijmeni} byla úspěšně vytvořena a uložena do databáze!")
        except Exception as e:
            await interaction.followup.send(f"❌ Nastala chyba při zakládání složky ve fóru. Zkontroluj oprávnění bota. Detail: {e}")

async def setup(bot):
    await bot.add_cog(IdKartaCog(bot))
