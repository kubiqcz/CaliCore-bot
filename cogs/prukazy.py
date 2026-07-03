import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# ID nastavení pro MDT Server
MDT_SERVER_ID = 1453744303691137045       # DOPLŇ ID MDT SERVERU
MDT_ARCHIV_KANAL_ID = 1522513841705975869 # DOPLŇ ID KANÁLU "ARCHIV VYDANÝCH PRŮKAZŮ"

# Databáze bota
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

class PrukazyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 1. COMMAND: Vydání průkazu
    @app_commands.command(name="vydat_prukaz", description="[MDT] Zanese do databáze občana platný průkaz.")
    @app_commands.describe(hrac_id="Číslo ID občana z jeho ID Karty", prukaz="Vyber konkrétní typ a skupinu průkazu")
    @app_commands.choices(prukaz=[
        app_commands.Choice(name="Řidičský průkaz - Skupina A (Moto)", value="rp_a"),
        app_commands.Choice(name="Řidičský průkaz - Skupina B (Auto)", value="rp_b"),
        app_commands.Choice(name="Řidičský průkaz - Skupina C (Náklaďák)", value="rp_c"),
        app_commands.Choice(name="Řidičský průkaz - Skupina T (Traktor)", value="rp_t"),
        app_commands.Choice(name="Zbrojní průkaz - Skupina A", value="zp_a"),
        app_commands.Choice(name="Zbrojní průkaz - Skupina B", value="zp_b"),
        app_commands.Choice(name="Zbrojní průkaz - Skupina C", value="zp_c")
    ])
    async def vydat_command(self, interaction: discord.Interaction, hrac_id: str, prukaz: app_commands.Choice[str]):
        # Kontrola, jestli je příkaz použit ve správném kanálu archivu
        if interaction.channel_id != MDT_ARCHIV_KANAL_ID:
            await interaction.response.send_message("❌ Tento příkaz lze použít pouze v kanálu pro archiv vydaných průkazů.", ephemeral=True)
            return

        # Uložení do databáze
        db = nacti_databazi()
        if hrac_id not in db:
            db[hrac_id] = {"prukazy": []}
        elif "prukazy" not in db[hrac_id]:
            db[hrac_id]["prukazy"] = []

        if prukaz.value in db[hrac_id]["prukazy"]:
            await interaction.response.send_message(f"Občan s ID `{hrac_id}` už tento průkaz ({prukaz.name}) v databázi má zapsaný.", ephemeral=True)
            return

        db[hrac_id]["prukazy"].append(prukaz.value)
        uloz_databazi(db)

        # Vytvoření hezké informační tabulky (Embed)
        embed = discord.Embed(title="📄 Záznam o vydání průkazu", color=discord.Color.green())
        embed.add_field(name="Typ průkazu", value=f"**{prukaz.name}**", inline=False)
        embed.add_field(name="Zpracoval úředník", value=interaction.user.mention, inline=True)
        # Pomocí <@ID> se bot pokusí hráče v textu označit, pokud je na serveru. Jinak vypíše jen ID.
        embed.add_field(name="Vydáno pro občana", value=f"<@{hrac_id}> (ID: `{hrac_id}`)", inline=True)
        embed.set_footer(text="CaliCore MDT System | Záznam uložen do databáze")

        # Zpráva už není ephemeral, pošle se rovnou do kanálu jako trvalý záznam!
        await interaction.response.send_message(embed=embed)


    # 2. COMMAND: Odebrání průkazu
    @app_commands.command(name="odebrat_prukaz", description="[MDT] Sebere občanu průkaz (např. za trestný čin).")
    @app_commands.describe(hrac_id="Číslo ID občana z jeho ID Karty", prukaz="Vyber průkaz k odebrání")
    @app_commands.choices(prukaz=[
        app_commands.Choice(name="Řidičský průkaz - Skupina A (Moto)", value="rp_a"),
        app_commands.Choice(name="Řidičský průkaz - Skupina B (Auto)", value="rp_b"),
        app_commands.Choice(name="Řidičský průkaz - Skupina C (Náklaďák)", value="rp_c"),
        app_commands.Choice(name="Řidičský průkaz - Skupina T (Traktor)", value="rp_t"),
        app_commands.Choice(name="Zbrojní průkaz - Skupina A", value="zp_a"),
        app_commands.Choice(name="Zbrojní průkaz - Skupina B", value="zp_b"),
        app_commands.Choice(name="Zbrojní průkaz - Skupina C", value="zp_c")
    ])
    async def odebrat_command(self, interaction: discord.Interaction, hrac_id: str, prukaz: app_commands.Choice[str]):
        if interaction.channel_id != MDT_ARCHIV_KANAL_ID:
            await interaction.response.send_message("❌ Tento příkaz lze použít pouze v kanálu pro archiv vydaných průkazů.", ephemeral=True)
            return

        db = nacti_databazi()
        if hrac_id in db and "prukazy" in db[hrac_id] and prukaz.value in db[hrac_id]["prukazy"]:
            db[hrac_id]["prukazy"].remove(prukaz.value)
            uloz_databazi(db)
            
            # Tabulka pro zabavení
            embed = discord.Embed(title="🚨 Záznam o odebrání průkazu", color=discord.Color.red())
            embed.add_field(name="Zabavený průkaz", value=f"**{prukaz.name}**", inline=False)
            embed.add_field(name="Zabavil úředník", value=interaction.user.mention, inline=True)
            embed.add_field(name="Odebráno občanu", value=f"<@{hrac_id}> (ID: `{hrac_id}`)", inline=True)
            embed.set_footer(text="CaliCore MDT System | Záznam smazán z databáze")

            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"Občan s ID `{hrac_id}` tento průkaz v databázi momentálně nemá.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(PrukazyCog(bot))
