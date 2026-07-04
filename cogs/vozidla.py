import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# IMPORT AKTUALIZAČNÍ FUNKCE
from cogs.profil import aktualizuj_mdt_profil

# ID nastavení pro MDT Server
MDT_SERVER_ID = 1453744303691137045          # ZDE DOPLŇ ID MDT SERVERU
MDT_REGISTR_VOZIDEL_ID = 1522684016388472983 # ZDE DOPLŇ ID KANÁLU PRO REGISTR VOZIDEL

DATABAZE_SOUBOR = "databaze_hracu.json"

def nacti_databazi():
    if not os.path.exists(DATABAZE_SOUBOR):
        return {}
    with open(DATABAZE_SOUBOR, "r") as f:
        return json.load(f)

def uloz_databazi(data):
    with open(DATABAZE_SOUBOR, "w") as f:
        json.dump(data, f, indent=4)

class VozidlaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="registrovat_vozidlo", description="[MDT] Zaregistruje vozidlo na občana.")
    @app_commands.describe(hrac_id="Číslo ID občana", vozidlo="Značka a model", barva="Barva vozidla", spz="SPZ ze hry")
    async def registrovat_vozidlo(self, interaction: discord.Interaction, hrac_id: str, vozidlo: str, barva: str, spz: str):
        if interaction.channel_id != MDT_REGISTR_VOZIDEL_ID:
            await interaction.response.send_message("❌ Tento příkaz lze použít pouze v kanálu pro registr vozidel.", ephemeral=True)
            return

        db = nacti_databazi()
        if hrac_id not in db:
            db[hrac_id] = {"prukazy": [], "zbrane": [], "vozidla": []}
        if "vozidla" not in db[hrac_id]:
            db[hrac_id]["vozidla"] = []

        spz_upper = spz.upper()
        for v in db[hrac_id]["vozidla"]:
            if v["spz"] == spz_upper:
                await interaction.response.send_message(f"Vozidlo se značkou `{spz_upper}` už občan vlastní.", ephemeral=True)
                return

        db[hrac_id]["vozidla"].append({"model": vozidlo, "barva": barva, "spz": spz_upper})
        
        # ULOŽENÍ A AKTUALIZACE
        uloz_databazi(db)
        await aktualizuj_mdt_profil(self.bot, hrac_id)

        embed = discord.Embed(title="🚘 Záznam o registraci vozidla", color=discord.Color.blue())
        embed.add_field(name="Vozidlo", value=f"**{vozidlo}**", inline=False)
        embed.add_field(name="Barva", value=barva, inline=True)
        embed.add_field(name="SPZ (RZ)", value=f"`{spz_upper}`", inline=True)
        embed.add_field(name="Majitel", value=f"<@{hrac_id}> (ID: `{hrac_id}`)", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="odstranit_vozidlo", description="[MDT] Odstraní vozidlo z registru občana (dle SPZ).")
    @app_commands.describe(hrac_id="Číslo ID občana", spz="SPZ vozidla ke smazání")
    async def odstranit_vozidlo(self, interaction: discord.Interaction, hrac_id: str, spz: str):
        if interaction.channel_id != MDT_REGISTR_VOZIDEL_ID:
            await interaction.response.send_message("❌ Tento příkaz lze použít pouze v kanálu pro registr vozidel.", ephemeral=True)
            return

        db = nacti_databazi()
        spz_upper = spz.upper()

        if hrac_id in db and "vozidla" in db[hrac_id]:
            puvodni_pocet = len(db[hrac_id]["vozidla"])
            db[hrac_id]["vozidla"] = [v for v in db[hrac_id]["vozidla"] if v["spz"] != spz_upper]
            
            if len(db[hrac_id]["vozidla"]) < puvodni_pocet:
                # ULOŽENÍ A AKTUALIZACE
                uloz_databazi(db)
                await aktualizuj_mdt_profil(self.bot, hrac_id)
                
                embed = discord.Embed(title="🚨 Záznam o vyřazení vozidla", color=discord.Color.red())
                embed.add_field(name="SPZ (RZ)", value=f"`{spz_upper}`", inline=False)
                embed.add_field(name="Odebráno majiteli", value=f"<@{hrac_id}>", inline=True)
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(f"Vozidlo se SPZ `{spz_upper}` u tohoto občana nebylo nalezeno.", ephemeral=True)
        else:
            await interaction.response.send_message("Občan nemá registrovaná žádná vozidla.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(VozidlaCog(bot))
