import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from cogs.profil import aktualizuj_mdt_profil

MDT_ZBRANE_ID = 1522683939964063794 # ZDE DOPLŇ ID KANÁLU

DATABAZE_SOUBOR = "databaze_hracu.json"

def nacti_databazi():
    if not os.path.exists(DATABAZE_SOUBOR):
        return {}
    with open(DATABAZE_SOUBOR, "r") as f:
        return json.load(f)

def uloz_databazi(data):
    with open(DATABAZE_SOUBOR, "w") as f:
        json.dump(data, f, indent=4)

class ZbraneCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="registrovat_zbran", description="[MDT] Zaregistruje zbraň na občana.")
    @app_commands.describe(hrac_id="Číslo ID občana", typ="Typ zbraně (např. Beretta M9)", sn="Sériové číslo ze hry")
    async def registrovat_zbran(self, interaction: discord.Interaction, hrac_id: str, typ: str, sn: str):
        if interaction.channel_id != MDT_ZBRANE_ID:
            await interaction.response.send_message("❌ Tento příkaz lze použít pouze v kanálu pro zbraně.", ephemeral=True)
            return

        db = nacti_databazi()
        if hrac_id not in db:
            db[hrac_id] = {"prukazy": [], "zbrane": [], "vozidla": []}
        if "zbrane" not in db[hrac_id]:
            db[hrac_id]["zbrane"] = []

        sn_upper = sn.upper()
        for z in db[hrac_id]["zbrane"]:
            if z["sn"] == sn_upper:
                await interaction.response.send_message(f"Zbraň se sériovým číslem `{sn_upper}` už je v databázi.", ephemeral=True)
                return

        db[hrac_id]["zbrane"].append({"typ": typ, "sn": sn_upper})
        uloz_databazi(db)

        embed = discord.Embed(title="🔫 Registrace zbraně", color=discord.Color.dark_grey())
        embed.add_field(name="Zbraň", value=typ, inline=True)
        embed.add_field(name="Sériové číslo (SN)", value=f"`{sn_upper}`", inline=True)
        embed.add_field(name="Majitel", value=f"<@{hrac_id}> (ID: `{hrac_id}`)", inline=False)
        
        # 1. OKAMŽITĚ ODPOVÍME DISCORDU (aby nespadl)
        await interaction.response.send_message(embed=embed)
        
        # 2. AŽ POTOM AKTUALIZUJEME FÓRUM NA POZADÍ
        await aktualizuj_mdt_profil(self.bot, hrac_id)

    @app_commands.command(name="odebrat_zbran", description="[MDT] Smaže zbraň z registru občana (dle Sériového Čísla).")
    @app_commands.describe(hrac_id="Číslo ID občana", sn="Sériové číslo zbraně")
    async def odebrat_zbran(self, interaction: discord.Interaction, hrac_id: str, sn: str):
        if interaction.channel_id != MDT_ZBRANE_ID:
            await interaction.response.send_message("❌ Tento příkaz lze použít pouze v kanálu pro zbraně.", ephemeral=True)
            return

        db = nacti_databazi()
        sn_upper = sn.upper()

        if hrac_id in db and "zbrane" in db[hrac_id]:
            puvodni_pocet = len(db[hrac_id]["zbrane"])
            db[hrac_id]["zbrane"] = [z for z in db[hrac_id]["zbrane"] if z["sn"] != sn_upper]
            
            if len(db[hrac_id]["zbrane"]) < puvodni_pocet:
                uloz_databazi(db)
                
                embed = discord.Embed(title="🚨 Zabavení / Odstranění zbraně", color=discord.Color.red())
                embed.add_field(name="Sériové číslo (SN)", value=f"`{sn_upper}`", inline=False)
                embed.add_field(name="Odebráno majiteli", value=f"<@{hrac_id}>", inline=True)
                
                # ODPOVÍ HNED
                await interaction.response.send_message(embed=embed)
                # AKTUALIZUJE AŽ POTOM
                await aktualizuj_mdt_profil(self.bot, hrac_id)
            else:
                await interaction.response.send_message(f"Zbraň s SN `{sn_upper}` u tohoto občana neexistuje.", ephemeral=True)
        else:
            await interaction.response.send_message("Občan nemá registrované zbraně.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ZbraneCog(bot))
