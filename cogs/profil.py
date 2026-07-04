import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATABAZE_SOUBOR = "databaze_hracu.json"

# Slovník pro hezčí výpis průkazů z databázových zkratek
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
    if not os.path.exists(DATABAZE_SOUBOR):
        return {}
    with open(DATABAZE_SOUBOR, "r") as f:
        return json.load(f)

# Hlavní funkce pro tvorbu vzhledu profilu (využijeme ji později i pro MDT)
def vytvor_profil_embed(hrac_id, hrac_jmeno=None, db_data=None):
    if db_data is None:
        db_data = {}

    hrac_data = db_data.get(str(hrac_id), {})
    
    embed = discord.Embed(title="📁 Osobní RP Profil", color=discord.Color.gold())
    if hrac_jmeno:
        embed.description = f"Výpis z centrální databáze pro občana: {hrac_jmeno}"
    
    # 1. Průkazy
    prukazy = hrac_data.get("prukazy", [])
    if prukazy:
        prukazy_text = "\n".join([f"• {PRUKAZY_MAP.get(p, p)}" for p in prukazy])
    else:
        prukazy_text = "❌ Žádné vydané průkazy"
    embed.add_field(name="🪪 Průkazy a Licence", value=prukazy_text, inline=False)

    # 2. Zbraně
    zbrane = hrac_data.get("zbrane", [])
    if zbrane:
        zbrane_text = "\n".join([f"• {z['typ']} (SN: `{z['sn']}`)" for z in zbrane])
    else:
        zbrane_text = "❌ Žádné registrované zbraně"
    embed.add_field(name="🔫 Registr Zbraní", value=zbrane_text, inline=False)

    # 3. Vozidla
    vozidla = hrac_data.get("vozidla", [])
    if vozidla:
        vozidla_text = "\n".join([f"• {v['model']} - {v['barva']} (RZ: `{v['spz']}`)" for v in vozidla])
    else:
        vozidla_text = "❌ Žádná registrovaná vozidla"
    embed.add_field(name="🚘 Registr Vozidel", value=vozidla_text, inline=False)

    embed.set_footer(text=f"Číslo ID: {hrac_id} | CaliCore System")
    return embed

class ProfilCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="profil", description="Zobrazí tvůj aktuální osobní RP profil (průkazy, zbraně, vozidla).")
    async def profil_command(self, interaction: discord.Interaction):
        db = nacti_databazi()
        hrac_id = str(interaction.user.id)
        
        # Vygenerujeme tabulku
        embed = vytvor_profil_embed(hrac_id, interaction.user.mention, db)
        
        # Odeslání odpovědi pouze hráči
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ProfilCog(bot))
