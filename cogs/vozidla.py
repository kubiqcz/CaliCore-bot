import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# ID nastavení pro MDT Server
MDT_SERVER_ID = 1453744303691137045          # ZDE DOPLŇ ID MDT SERVERU
MDT_REGISTR_VOZIDEL_ID = 1522684016388472983# ZDE DOPLŇ ID KANÁLU PRO REGISTR VOZIDEL

DATABAZE_SOUBOR = "databaze_hracu.json"

def nacti_databazi():
    if not os.path.exists(DATABAZE_SOUBOR):
        with open(DATABAZE_SOUBOR, "w") as f:
            json.dump({}, f)
    with open(DATABAZE_SOUBOR, "r") as f:
        return json.load(f)

def uloz_databazi(data):
    with open(DATABAZE_SOUBOR, "w") as f:
        json.dump(data, f, indent=4)

class VozidlaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 1. COMMAND: Registrace vozidla
    @app_commands.command(name="registrovat_vozidlo", description="[MDT] Zaregistruje vozidlo na občana.")
    @app_commands.describe(
        hrac_id="Číslo ID občana z jeho ID Karty",
        vozidlo="Značka a model (např. Averon Q8)",
        barva="Barva vozidla",
        spz="Státní poznávací značka (RZ) ze hry"
    )
    async def registrovat_vozidlo(self, interaction: discord.Interaction, hrac_id: str, vozidlo: str, barva: str, spz: str):
        if interaction.channel_id != MDT_REGISTR_VOZIDEL_ID:
            await interaction.response.send_message("❌ Tento příkaz lze použít pouze v kanálu pro registr vozidel.", ephemeral=True)
            return

        db = nacti_databazi()
        if hrac_id not in db:
            db[hrac_id] = {}
        if "vozidla" not in db[hrac_id]:
            db[hrac_id]["vozidla"] = []

        spz_upper = spz.upper()
        
        # Kontrola duplicity SPZ u daného hráče
        for v in db[hrac_id]["vozidla"]:
            if v["spz"] == spz_upper:
                await interaction.response.send_message(f"Vozidlo se značkou `{spz_upper}` už má tento občan registrované.", ephemeral=True)
                return

        nove_vozidlo = {"model": vozidlo, "barva": barva, "spz": spz_upper}
        db[hrac_id]["vozidla"].append(nove_vozidlo)
        uloz_databazi(db)

        embed = discord.Embed(title="🚘 Záznam o registraci vozidla", color=discord.Color.blue())
        embed.add_field(name="Vozidlo", value=f"**{vozidlo}**", inline=False)
        embed.add_field(name="Barva", value=barva, inline=True)
        embed.add_field(name="SPZ (RZ)", value=f"`{spz_upper}`", inline=True)
        embed.add_field(name="Zpracoval úředník", value=interaction.user.mention, inline=False)
        embed.add_field(name="Zapsáno na majitele", value=f"<@{hrac_id}> (ID: `{hrac_id}`)", inline=True)
        embed.set_footer(text="CaliCore MDT System | Vozidlo uloženo do databáze")

        await interaction.response.send_message(embed=embed)

    # 2. COMMAND: Odstranění vozidla z registru
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
            
            # Ponechá v databázi jen ta auta, jejichž SPZ se nerovná té mazané
            db[hrac_id]["vozidla"] = [v for v in db[hrac_id]["vozidla"] if v["spz"] != spz_upper]
            
            if len(db[hrac_id]["vozidla"]) < puvodni_pocet:
                uloz_databazi(db)
                
                embed = discord.Embed(title="🚨 Záznam o vyřazení vozidla", color=discord.Color.red())
                embed.add_field(name="SPZ (RZ)", value=f"`{spz_upper}`", inline=False)
                embed.add_field(name="Zpracoval", value=interaction.user.mention, inline=True)
                embed.add_field(name="Odebráno z profilu", value=f"<@{hrac_id}> (ID: `{hrac_id}`)", inline=True)
                embed.set_footer(text="CaliCore MDT System | Vozidlo vymazáno z registru")

                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(f"Vozidlo se SPZ `{spz_upper}` nebylo u tohoto občana nalezeno.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Občan s ID `{hrac_id}` nemá registrovaná žádná vozidla.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(VozidlaCog(bot))
