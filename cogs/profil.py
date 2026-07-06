import discord
from discord.ext import commands
from discord import app_commands
import pymongo

# ==========================================
# NASTAVENÍ OPRÁVNĚNÍ A KANÁLŮ
# ==========================================
POVOLENE_KANALY_PROFIL = [1394695584383762569, 1394695584383762570, 1394695584383762571, 1394695584383762572, 1394695584383762573, 1394695584383762574] # ZDE DOPLŇ ID KANÁLU
POVOLENE_ROLE_PROFIL = [1394695578801148019] # Pokud necháš prázdné [], může to použít kdokoli. Pokud sem dáš ID, např. [12345, 67890], omezí se to na tyto role.

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

def vytvor_profil_embed(hrac_id, discord_jmeno=None, db_data=None):
    if db_data is None:
        db_data = nacti_databazi()

    hrac_data = db_data.get(str(hrac_id), {})
    embed = discord.Embed(title="📁 Osobní RP Profil (Přehled majetku)", color=discord.Color.gold())
    
    jmeno_postavy = hrac_data.get('jmeno', 'Neznámo')
    embed.description = f"**Občan:** {jmeno_postavy}\n**Číslo průkazu: \"{hrac_id}\"**"
    
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

    return embed

async def aktualizuj_mdt_profil(bot, hrac_id):
    db = nacti_databazi()
    hrac_id_str = str(hrac_id)
    hrac_data = db.get(hrac_id_str, {})
    
    vlakno_id = hrac_data.get("mdt_vlakno_id")
    zprava_id = hrac_data.get("mdt_zprava_id") # Tohle je to ID zprávy, kde je tabulka profilu ve fóru
    
    if not vlakno_id or not zprava_id: return 
    try:
        vlakno = await bot.fetch_channel(vlakno_id)
        zprava = await vlakno.fetch_message(zprava_id)
        novy_embed = vytvor_profil_embed(hrac_id_str, None, db)
        await zprava.edit(embed=novy_embed) # Upraví POUZE tabulku majetku ve fóru (občanka nahoře zůstane)
    except Exception as e:
        print(f"Chyba při updatu profilu na MDT: {e}")

class ProfilCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="profil", description="Zobrazí tvůj RP profil, nebo profil jiného hráče.")
    @app_commands.describe(obcan="Vyber hráče, pokud se chceš podívat na jeho profil (nepovinné)")
    async def profil_command(self, interaction: discord.Interaction, obcan: discord.Member = None):
        if POVOLENE_KANALY_PROFIL and interaction.channel_id not in POVOLENE_KANALY_PROFIL:
            await interaction.response.send_message("❌ Zde nemůžeš tento příkaz použít.", ephemeral=True)
            return

        # Pokud nevybral nikoho, ukáže se jeho vlastní profil. Pokud vybral, ukáže se ten pingnutý.
        cilovy_hrac = obcan if obcan else interaction.user
        
        db = nacti_databazi()
        hrac_id = str(cilovy_hrac.id)
        embed = vytvor_profil_embed(hrac_id, cilovy_hrac.mention, db)
        
        # Tohle vyjede pouze tomu hráči, který ten příkaz napsal (ephemeral=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ProfilCog(bot))
