import discord
from discord.ext import commands
from discord import app_commands
import pymongo

POVOLENE_KANALY_PROFIL = [
    1394695584383762569, 1394695584383762570, 1394695584383762571, 1394695584383762572, 1394695584383762573, 1394695584383762574 # ZDE DOPLŇ ID KANÁLU PRO PŘÍKAZ /PROFIL
]

MONGO_URI = "mongodb+srv://kubiqcz1:Aluska78@calicore.kmnmj4h.mongodb.net/?appName=CaliCore"
klient = pymongo.MongoClient(MONGO_URI)
db_cloud = klient["calicore_databaze"]
kolekce_hraci = db_cloud["hraci"]

PRUKAZY_MAP = {
    "rp_a": "Řidičský průkaz - Skupina A (Moto)",
    "rp_b": "Řidičský průkaz - Skupina B (Auto)",
    "rp_c": "Řidičský průkaz - Skupina C (Náklaďák)",
    "rp_t": "Řidičský průkaz - Skupina T (Traktor)",
    "zp_a": "Zbrojní průkaz - Skupina A",
    "zp_b": "Zbrojní průkaz - Skupina B",
    "zp_c": "Zbrojní průkaz - Skupina C"
}

def nacti_databazi():
    data = {}
    for hrac in kolekce_hraci.find():
        data[str(hrac["_id"])] = hrac
    return data

def vytvor_profil_embed(hrac_id, hrac_jmeno=None, db_data=None):
    if db_data is None:
        db_data = nacti_databazi()

    hrac_data = db_data.get(str(hrac_id), {})
    
    embed = discord.Embed(title="📁 Osobní RP Profil", color=discord.Color.gold())
    if hrac_jmeno:
        embed.description = f"Výpis z centrální databáze pro občana: {hrac_jmeno}"
    
    prukazy = hrac_data.get("prukazy", [])
    if prukazy:
        prukazy_text = "\n".join([f"• {PRUKAZY_MAP.get(p, p)}" for p in prukazy])
    else:
        prukazy_text = "❌ Žádné vydané průkazy"
    embed.add_field(name="🪪 Průkazy a Licence", value=prukazy_text, inline=False)

    zbrane = hrac_data.get("zbrane", [])
    if zbrane:
        zbrane_text = "\n".join([f"• {z.get('model', 'Neznámá zbraň')} (Sériové číslo: `{z.get('serial number', 'N/A')}`)" for z in zbrane])
    else:
        zbrane_text = "❌ Žádné registrované zbraně"
    embed.add_field(name="🔫 Registr Zbraní", value=zbrane_text, inline=False)

    vozidla = hrac_data.get("vozidla", [])
    if vozidla:
        vozidla_text = "\n".join([f"• {v['model']} - {v['barva']} (RZ: `{v['spz']}`)" for v in vozidla])
    else:
        vozidla_text = "❌ Žádná registrovaná vozidla"
    embed.add_field(name="🚘 Registr Vozidel", value=vozidla_text, inline=False)

    embed.set_footer(text=f"Číslo ID: {hrac_id} | CaliCore System")
    return embed

async def aktualizuj_mdt_profil(bot, hrac_id):
    db = nacti_databazi()
    hrac_id_str = str(hrac_id)
    hrac_data = db.get(hrac_id_str, {})
    
    vlakno_id = hrac_data.get("mdt_vlakno_id")
    zprava_id = hrac_data.get("mdt_zprava_id")
    
    if not vlakno_id or not zprava_id:
        return 
        
    try:
        vlakno = await bot.fetch_channel(vlakno_id)
        zprava = await vlakno.fetch_message(zprava_id)
        novy_embed = vytvor_profil_embed(hrac_id_str, None, db)
        await zprava.edit(embed=novy_embed)
    except Exception as e:
        print(f"Chyba při updatu profilu na MDT: {e}")

class ProfilCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="profil", description="Zobrazí tvůj aktuální osobní RP profil (průkazy, zbraně, vozidla).")
    async def profil_command(self, interaction: discord.Interaction):
        if interaction.channel_id not in POVOLENE_KANALY_PROFIL:
            spravne_kanaly = ", ".join([f"<#{k_id}>" for k_id in POVOLENE_KANALY_PROFIL])
            await interaction.response.send_message(f"❌ Tento příkaz lze použít pouze v kanálech: {spravne_kanaly}", ephemeral=True)
            return

        db = nacti_databazi()
        hrac_id = str(interaction.user.id)
        embed = vytvor_profil_embed(hrac_id, interaction.user.mention, db)
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ProfilCog(bot))
