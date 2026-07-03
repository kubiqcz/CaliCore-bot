import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# ID nastavení pro MDT Server
MDT_SERVER_ID = 1453744303691137045       # DOPLŇ ID MDT SERVERU
MDT_ARCHIV_ZBRANI_ID = 1522683939964063794 # DOPLŇ ID KANÁLU PRO REGISTR ZBRANÍ

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

class ZbraneCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 1. COMMAND: Registrace zbraně
    @app_commands.command(name="registrovat_zbran", description="[MDT] Zaregistruje legálně zakoupenou zbraň na občana.")
    @app_commands.describe(
        hrac_id="Číslo ID občana z jeho ID Karty", 
        zbran="Vyber typ zbraně",
        seriove_cislo="Zadej sériové číslo zbraně (vymysli, např. M9-1234)"
    )
    @app_commands.choices(zbran=[
        app_commands.Choice(name="Beretta M9", value="Beretta M9"),
        app_commands.Choice(name="Colt M1911", value="Colt M1911"),
        app_commands.Choice(name="Colt Python", value="Colt Python"),
        app_commands.Choice(name="Remington 870", value="Remington 870"),
        app_commands.Choice(name="Remington 700", value="Remington 700"),
        app_commands.Choice(name="M14", value="M14"),
        app_commands.Choice(name="LMT L129A1", value="LMT L129A1")
    ])
    async def registrovat_command(self, interaction: discord.Interaction, hrac_id: str, zbran: app_commands.Choice[str], seriove_cislo: str):
        if interaction.channel_id != MDT_ARCHIV_ZBRANI_ID:
            await interaction.response.send_message("❌ Tento příkaz lze použít pouze v kanálu pro registr zbraní.", ephemeral=True)
            return

        db = nacti_databazi()
        if hrac_id not in db:
            db[hrac_id] = {}
        if "zbrane" not in db[hrac_id]:
            db[hrac_id]["zbrane"] = []

        # Zápis zbraně i se sériovým číslem do databáze (uloženo jako datový slovník)
        nova_zbran = {"typ": zbran.value, "sn": seriove_cislo}
        db[hrac_id]["zbrane"].append(nova_zbran)
        uloz_databazi(db)

        # Tabulka s logem do kanálu
        embed = discord.Embed(title="🔫 Záznam o registraci zbraně", color=discord.Color.dark_theme())
        embed.add_field(name="Typ zbraně", value=f"**{zbran.name}**", inline=False)
        embed.add_field(name="Sériové číslo", value=f"`{seriove_cislo}`", inline=False)
        embed.add_field(name="Zpracoval úředník", value=interaction.user.mention, inline=True)
        embed.add_field(name="Zapsáno na občana", value=f"<@{hrac_id}> (ID: `{hrac_id}`)", inline=True)
        embed.set_footer(text="CaliCore MDT System | Záznam uložen do databáze")

        await interaction.response.send_message(embed=embed)

    # 2. COMMAND: Zabavení zbraně
    @app_commands.command(name="zabavit_zbran", description="[MDT] Odebere občanu zbraň z registru (dle sériového čísla).")
    @app_commands.describe(hrac_id="Číslo ID občana z jeho ID Karty", seriove_cislo="Zadej sériové číslo zabavené zbraně")
    async def zabavit_command(self, interaction: discord.Interaction, hrac_id: str, seriove_cislo: str):
        if interaction.channel_id != MDT_ARCHIV_ZBRANI_ID:
            await interaction.response.send_message("❌ Tento příkaz lze použít pouze v kanálu pro registr zbraní.", ephemeral=True)
            return

        db = nacti_databazi()
        if hrac_id in db and "zbrane" in db[hrac_id]:
            puvodni_pocet = len(db[hrac_id]["zbrane"])
            
            # Najde zbraň podle sériového čísla a smaže ji
            db[hrac_id]["zbrane"] = [z for z in db[hrac_id]["zbrane"] if z["sn"] != seriove_cislo]
            
            if len(db[hrac_id]["zbrane"]) < puvodni_pocet:
                uloz_databazi(db)
                
                embed = discord.Embed(title="🚨 Záznam o zabavení zbraně", color=discord.Color.red())
                embed.add_field(name="Sériové číslo", value=f"`{seriove_cislo}`", inline=False)
                embed.add_field(name="Zabavil", value=interaction.user.mention, inline=True)
                embed.add_field(name="Odebráno občanu", value=f"<@{hrac_id}> (ID: `{hrac_id}`)", inline=True)
                embed.set_footer(text="CaliCore MDT System | Zbraň vymazána z registru")

                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(f"Zbraň se sériovým číslem `{seriove_cislo}` nebyla u občana s ID `{hrac_id}` nalezena.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Občan s ID `{hrac_id}` nemá v registru žádné zbraně.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ZbraneCog(bot))
