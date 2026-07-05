import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# IMPORT AKTUALIZAČNÍ FUNKCE
from cogs.profil import aktualizuj_mdt_profil

MDT_ZBRANE_ID = 1522683939964063794 # ZDE DOPLŇ ID KANÁLU PRO ZBRANĚ

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

    # ==========================================
    # SEZNAM ZBRANÍ PRO PŘEDVOLBY (Můžeš si libovolně upravit)
    # ==========================================
    zbrane_choices = [
        app_commands.Choice(name="Beretta M9", value="Beretta M9"),
        app_commands.Choice(name="Colt M911", value="Colt M1911"),
        app_commands.Choice(name="Colt Python", value="Colt Python"),
        app_commands.Choice(name="Remington 870", value="Remington 870"),
        app_commands.Choice(name="Remington 700", value="Remington 700"),
        app_commands.Choice(name="M14", value="M14")
        app_commands.Choice(name="LMT L129A1", value="LMT L129A1")  
    ]

    @app_commands.command(name="registrovat_zbran", description="[MDT] Zaregistruje zbraň na občana.")
    @app_commands.describe(hrac_id="Číslo ID občana", model="Vyber typ zbraně ze seznamu", sériové číslo="Sériové číslo")
    @app_commands.choices(typ=zbrane_choices)
    async def registrovat_zbran(self, interaction: discord.Interaction, hrac_id: str, typ: app_commands.Choice[str], sn: str):
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
                await interaction.response.send_message(f"❌ Zbraň se sériovým číslem `{sn_upper}` už je v databázi.", ephemeral=True)
                return

        db[hrac_id]["zbrane"].append({"typ": model.value, "sériové číslo": sn_upper})
        uloz_databazi(db)

        embed = discord.Embed(title="🔫 Registrace zbraně", color=discord.Color.dark_grey())
        embed.add_field(name="Zbraň", value=typ.name, inline=True)
        embed.add_field(name="Sériové číslo (SN)", value=f"`{sn_upper}`", inline=True)
        embed.add_field(name="Majitel", value=f"<@{hrac_id}> (ID: `{hrac_id}`)", inline=False)
        embed.set_footer(text="CaliCore MDT System | Zbraň uložena do databáze")
        
        # 1. OKAMŽITĚ ODPOVÍME DISCORDU
        await interaction.response.send_message(embed=embed)
        # 2. AKTUALIZUJEME FÓRUM NA POZADÍ
        await aktualizuj_mdt_profil(self.bot, hrac_id)

    @app_commands.command(name="odebrat_zbran", description="[MDT] Smaže zbraň z registru občana (dle Sériového Čísla).")
    @app_commands.describe(hrac_id="Číslo ID občana", sériové číslo="Sériové číslo zbraně ke smazání")
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
                embed.set_footer(text="CaliCore MDT System | Zbraň vymazána z registru")
                
                # 1. ODPOVÍME HNED
                await interaction.response.send_message(embed=embed)
                # 2. AKTUALIZUJEME FÓRUM NA POZADÍ
                await aktualizuj_mdt_profil(self.bot, hrac_id)
            else:
                await interaction.response.send_message(f"❌ Zbraň s SN `{sn_upper}` u tohoto občana neexistuje.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Občan nemá registrované žádné zbraně.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ZbraneCog(bot))
