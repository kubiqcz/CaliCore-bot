import discord
from discord.ext import commands
from discord import app_commands
import pymongo

from cogs.profil import aktualizuj_mdt_profil

# ==========================================
MDT_ZBRANE_ID = 1522683939964063794 # ZDE DOPLŇ ID KANÁLU PRO ZBRANĚ
# ==========================================

MONGO_URI = "mongodb+srv://kubiqcz1:Aluska78@calicore.kmnmj4h.mongodb.net/?appName=CaliCore"
klient = pymongo.MongoClient(MONGO_URI)
db_cloud = klient["calicore_databaze"]
kolekce_hraci = db_cloud["hraci"]

def nacti_databazi():
    data = {}
    for hrac in kolekce_hraci.find():
        data[str(hrac["_id"])] = hrac
    return data

def uloz_databazi(data):
    for hrac_id, hrac_data in data.items():
        hrac_data["_id"] = str(hrac_id)
        kolekce_hraci.replace_one({"_id": str(hrac_id)}, hrac_data, upsert=True)

class ZbraneCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    zbrane_choices = [
        app_commands.Choice(name="Berreta M9", value="Berreta M9"),
        app_commands.Choice(name="Colt M1911", value="Colt M1911"),
        app_commands.Choice(name="Colt Python", value="Colt Python"),
        app_commands.Choice(name="Remington 870", value="Remington 870"),
        app_commands.Choice(name="Remington 700", value="Remington 700"),
        app_commands.Choice(name="M14", value="M14"),
        app_commands.Choice(name="LMT L129A1", value="LMT L129A1")
    ]

    @app_commands.command(name="registrovat_zbran", description="[MDT] Zaregistruje zbraň na občana.")
    @app_commands.describe(hrac_id="Číslo ID občana", model="Vyber model zbraně ze seznamu", seriove_cislo="Sériové číslo ze hry")
    @app_commands.choices(model=zbrane_choices)
    async def registrovat_zbran(self, interaction: discord.Interaction, hrac_id: str, model: app_commands.Choice[str], seriove_cislo: str):
        if interaction.channel_id != MDT_ZBRANE_ID:
            await interaction.response.send_message("❌ Tento příkaz lze použít pouze v kanálu pro zbraně.", ephemeral=True)
            return

        db = nacti_databazi()
        if hrac_id not in db:
            db[hrac_id] = {"prukazy": [], "zbrane": [], "vozidla": []}
        if "zbrane" not in db[hrac_id]:
            db[hrac_id]["zbrane"] = []

        sn_upper = seriove_cislo.upper().strip()
        for z in db[hrac_id]["zbrane"]:
            if z["sn"] == sn_upper:
                await interaction.response.send_message(f"❌ Zbraň se sériovým číslem `{sn_upper}` už je v databázi.", ephemeral=True)
                return

        db[hrac_id]["zbrane"].append({"typ": model.value, "sn": sn_upper})
        uloz_databazi(db)

        embed = discord.Embed(title="🔫 Registrace zbraně", color=discord.Color.dark_grey())
        embed.add_field(name="Model", value=model.name, inline=True)
        embed.add_field(name="Sériové číslo", value=f"`{sn_upper}`", inline=True)
        embed.add_field(name="Majitel", value=f"<@{hrac_id}> (ID: `{hrac_id}`)", inline=False)
        embed.set_footer(text="CaliCore MDT System | Zbraň uložena do databáze")
        
        await interaction.response.send_message(embed=embed)
        await aktualizuj_mdt_profil(self.bot, hrac_id)

    @app_commands.command(name="odebrat_zbran", description="[MDT] Smaže zbraň z registru občana.")
    @app_commands.describe(hrac_id="Číslo ID občana", seriove_cislo="Sériové číslo zbraně ke smazání")
    async def odebrat_zbran(self, interaction: discord.Interaction, hrac_id: str, seriove_cislo: str):
        if interaction.channel_id != MDT_ZBRANE_ID:
            await interaction.response.send_message("❌ Tento příkaz lze použít pouze v kanálu pro zbraně.", ephemeral=True)
            return

        db = nacti_databazi()
        sn_upper = seriove_cislo.upper().strip()

        if hrac_id in db and "zbrane" in db[hrac_id]:
            puvodni_pocet = len(db[hrac_id]["zbrane"])
            db[hrac_id]["zbrane"] = [z for z in db[hrac_id]["zbrane"] if z["sn"] != sn_upper]
            
            if len(db[hrac_id]["zbrane"]) < puvodni_pocet:
                uloz_databazi(db)
                embed = discord.Embed(title="🚨 Zabavení / Odstranění zbraně", color=discord.Color.red())
                embed.add_field(name="Sériové číslo", value=f"`{sn_upper}`", inline=False)
                embed.add_field(name="Odebráno majiteli", value=f"<@{hrac_id}>", inline=True)
                embed.set_footer(text="CaliCore MDT System | Zbraň vymazána z registru")
                
                await interaction.response.send_message(embed=embed)
                await aktualizuj_mdt_profil(self.bot, hrac_id)
            else:
                await interaction.response.send_message(f"❌ Zbraň se sériovým číslem `{sn_upper}` u tohoto občana neexistuje.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Občan nemá registrované žádné zbraně.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ZbraneCog(bot))
