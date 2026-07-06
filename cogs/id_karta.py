import discord
from discord.ext import commands
from discord import app_commands
import pymongo

# ==========================================
# NASTAVENÍ OPRÁVNĚNÍ A KANÁLŮ
# ==========================================
FORUM_MDT_ID = 1453745209643896933 # ID FÓRA PRO MDT SLOŽKY
POVOLENE_KANALY_ID = [1394695582760571070] # ID KANÁLU, KDE HRÁČI PÍŠOU /ID
POVOLENE_ROLE_ID = [] 

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
    roblox_nick = discord.ui.TextInput(label='Roblox Nick', style=discord.TextStyle.short, placeholder='Tvůj přesný nick na Robloxu...', required=True, max_length=50)
    jmeno = discord.ui.TextInput(label='Jméno a příjmení', style=discord.TextStyle.short, placeholder='John Pork...', required=True, max_length=50)
    datum_narozeni = discord.ui.TextInput(label='Datum narození postavy', style=discord.TextStyle.short, placeholder='18/06/2001', required=True, max_length=20)
    misto_narozeni = discord.ui.TextInput(label='Místo narození postavy', style=discord.TextStyle.short, placeholder='Los Angeles, CA', required=True, max_length=100)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        db = nacti_databazi()
        hrac_id = str(interaction.user.id)

        if hrac_id not in db:
            db[hrac_id] = {"prukazy": [], "zbrane": [], "vozidla": []}

        # Uložení do DB
        db[hrac_id]["roblox_nick"] = self.roblox_nick.value
        db[hrac_id]["jmeno"] = self.jmeno.value
        db[hrac_id]["datum_narozeni"] = self.datum_narozeni.value
        db[hrac_id]["misto_narozeni"] = self.misto_narozeni.value

  # VEŘEJNÁ OBČANKA DO KANÁLU
        embed_obcanka = discord.Embed(color=discord.Color.dark_theme())
        embed_obcanka.description = (
            f"{interaction.user.mention}\n\n"
            f"**Roblox nick:** {self.roblox_nick.value}\n"
            f"**Jméno a Příjmení:** {self.jmeno.value}\n"
            f"**Datum narození:** {self.datum_narozeni.value}\n"
            f"**Místo narození:** {self.misto_narozeni.value}\n\n"
            f"-# Číslo průkazu: {hrac_id}"
        )
        
        # Odeslání veřejně
        await interaction.response.send_message(embed=embed_obcanka)

        # VYTVOŘENÍ FÓRA PRO MDT A AUTOMATICKÉ AKTUALIZACE
        try:
            forum_kanal = self.bot.get_channel(FORUM_MDT_ID)
            if forum_kanal:
                # 1. Zpráva: Vytvoří vlákno a pošle tam kopii občanky
                vlakno = await forum_kanal.create_thread(
                    name=f"Složka: {self.jmeno.value}", 
                    content="Založena nová policejní složka.", 
                    embed=embed_obcanka
                )
                
                # 2. Zpráva hned pod občankou: Čistý profil pro inventář
                from cogs.profil import vytvor_profil_embed
                embed_profil = vytvor_profil_embed(hrac_id, interaction.user.mention, db)
                profil_zprava = await vlakno.thread.send(embed=embed_profil)
                
                # Uložíme ID té druhé zprávy (profilu), aby se mohl měnit a občanka zůstala nedotčená!
                db[hrac_id]["mdt_vlakno_id"] = vlakno.thread.id
                db[hrac_id]["mdt_zprava_id"] = profil_zprava.id

            uloz_databazi(db)
        except Exception as e:
            print(f"Chyba při zakládání složky ve fóru: {e}")

class IdKartaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="id", description="Založí novou ID kartu a MDT složku (zobrazí se všem).")
    async def id_karta(self, interaction: discord.Interaction):
        if POVOLENE_KANALY_ID and interaction.channel_id not in POVOLENE_KANALY_ID:
            await interaction.response.send_message("❌ Zde nelze založit ID kartu.", ephemeral=True)
            return
        await interaction.response.send_modal(IdModal(self.bot))

async def setup(bot):
    await bot.add_cog(IdKartaCog(bot))
