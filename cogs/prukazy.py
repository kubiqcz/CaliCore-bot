import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# IMPORT AKTUALIZAČNÍ FUNKCE
from cogs.profil import aktualizuj_mdt_profil

MDT_PRUKAZY_ID = 1394695582760571070 # ZDE DOPLŇ ID KANÁLU PRO PRŮKAZY

DATABAZE_SOUBOR = "databaze_hracu.json"

def nacti_databazi():
    if not os.path.exists(DATABAZE_SOUBOR):
        return {}
    with open(DATABAZE_SOUBOR, "r") as f:
        return json.load(f)

def uloz_databazi(data):
    with open(DATABAZE_SOUBOR, "w") as f:
        json.dump(data, f, indent=4)

class PrukazyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    prukazy_choices = [
        app_commands.Choice(name="Řidičský průkaz - A (Moto)", value="rp_a"),
        app_commands.Choice(name="Řidičský průkaz - B (Auto)", value="rp_b"),
        app_commands.Choice(name="Řidičský průkaz - C (Náklaďák)", value="rp_c"),
        app_commands.Choice(name="Řidičský průkaz - T (Traktor)", value="rp_t"),
        app_commands.Choice(name="Zbrojní průkaz - Skupina A", value="zp_a"),
        app_commands.Choice(name="Zbrojní průkaz - Skupina B", value="zp_b"),
        app_commands.Choice(name="Zbrojní průkaz - Skupina C", value="zp_c"),
    ]

    @app_commands.command(name="vydat_prukaz", description="[MDT] Vydá občanu průkaz / licenci.")
    @app_commands.describe(hrac_id="Číslo ID občana", typ="Vyber typ průkazu")
    @app_commands.choices(typ=prukazy_choices)
    async def vydat_prukaz(self, interaction: discord.Interaction, hrac_id: str, typ: app_commands.Choice[str]):
        if interaction.channel_id != MDT_PRUKAZY_ID:
            await interaction.response.send_message("❌ Tento příkaz lze použít pouze v kanálu pro průkazy.", ephemeral=True)
            return

        db = nacti_databazi()
        if hrac_id not in db:
            db[hrac_id] = {"prukazy": [], "zbrane": [], "vozidla": []}
        if "prukazy" not in db[hrac_id]:
            db[hrac_id]["prukazy"] = []

        if typ.value in db[hrac_id]["prukazy"]:
            await interaction.response.send_message("❌ Tento občan už tento průkaz vlastní.", ephemeral=True)
            return

        db[hrac_id]["prukazy"].append(typ.value)
        
        # ULOŽENÍ A AKTUALIZACE
        uloz_databazi(db)
        await aktualizuj_mdt_profil(self.bot, hrac_id)

        embed = discord.Embed(title="🪪 Vydání nového průkazu", color=discord.Color.green())
        embed.add_field(name="Typ průkazu", value=f"**{typ.name}**", inline=False)
        embed.add_field(name="Majitel", value=f"<@{hrac_id}> (ID: `{hrac_id}`)", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="odebrat_prukaz", description="[MDT] Odebere občanu průkaz / licenci.")
    @app_commands.describe(hrac_id="Číslo ID občana", typ="Vyber typ průkazu ke smazání")
    @app_commands.choices(typ=prukazy_choices)
    async def odebrat_prukaz(self, interaction: discord.Interaction, hrac_id: str, typ: app_commands.Choice[str]):
        if interaction.channel_id != MDT_PRUKAZY_ID:
            await interaction.response.send_message("❌ Tento příkaz lze použít pouze v kanálu pro průkazy.", ephemeral=True)
            return

        db = nacti_databazi()
        if hrac_id in db and "prukazy" in db[hrac_id] and typ.value in db[hrac_id]["prukazy"]:
            db[hrac_id]["prukazy"].remove(typ.value)
            
            # ULOŽENÍ A AKTUALIZACE
            uloz_databazi(db)
            await aktualizuj_mdt_profil(self.bot, hrac_id)
            
            embed = discord.Embed(title="🚨 Zrušení platnosti průkazu", color=discord.Color.red())
            embed.add_field(name="Typ průkazu", value=f"**{typ.name}**", inline=False)
            embed.add_field(name="Odebráno majiteli", value=f"<@{hrac_id}> (ID: `{hrac_id}`)", inline=False)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ Tento občan daný průkaz nevlastní.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(PrukazyCog(bot))
