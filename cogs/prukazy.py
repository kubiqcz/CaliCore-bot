import discord
from discord.ext import commands
from discord import app_commands
import pymongo
from cogs.profil import aktualizuj_mdt_profil

# ==========================================
# NASTAVENÍ OPRÁVNĚNÍ MDT PRŮKAZY
# ==========================================
MDT_PRUKAZY_ID = 1522513841705975869 
POVOLENE_ROLE_MDT = [1523660335406383164] 

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
        app_commands.Choice(name="California Boater Card", value="cbc"),  # <--- PŘIDÁNO ZDE
    ]

    def ma_mdt_opravneni(self, interaction: discord.Interaction):
        if not POVOLENE_ROLE_MDT: return True
        return any(role.id in POVOLENE_ROLE_MDT for role in interaction.user.roles)

    @app_commands.command(name="vydat_prukaz", description="[MDT] Vydá občanu průkaz / licenci.")
    @app_commands.describe(hrac_id="Číslo ID občana", typ="Vyber typ průkazu")
    @app_commands.choices(typ=prukazy_choices)
    async def vydat_prukaz(self, interaction: discord.Interaction, hrac_id: str, typ: app_commands.Choice[str]):
        if interaction.channel_id != MDT_PRUKAZY_ID:
            await interaction.response.send_message(f"❌ Tento příkaz lze použít pouze v <#{MDT_PRUKAZY_ID}>.", ephemeral=True)
            return
        if not self.ma_mdt_opravneni(interaction):
            await interaction.response.send_message("❌ Nemáš policejní/úřední oprávnění pro MDT registry.", ephemeral=True)
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
        uloz_databazi(db)

        embed = discord.Embed(title="🪪 Vydání nového průkazu", color=discord.Color.green())
        embed.add_field(name="Typ průkazu", value=f"**{typ.name}**", inline=False)
        embed.add_field(name="Majitel", value=f"<@{hrac_id}> (ID: `{hrac_id}`)", inline=False)
        
        await interaction.response.send_message(embed=embed)
        await aktualizuj_mdt_profil(self.bot, hrac_id)

    @app_commands.command(name="odebrat_prukaz", description="[MDT] Odebere občanu průkaz / licenci.")
    @app_commands.describe(hrac_id="Číslo ID občana", typ="Vyber typ průkazu ke smazání")
    @app_commands.choices(typ=prukazy_choices)
    async def odebrat_prukaz(self, interaction: discord.Interaction, hrac_id: str, typ: app_commands.Choice[str]):
        if interaction.channel_id != MDT_PRUKAZY_ID:
            await interaction.response.send_message(f"❌ Tento příkaz lze použít pouze v <#{MDT_PRUKAZY_ID}>.", ephemeral=True)
            return
        if not self.ma_mdt_opravneni(interaction):
            await interaction.response.send_message("❌ Nemáš policejní/úřední oprávnění pro MDT registry.", ephemeral=True)
            return

        db = nacti_databazi()
        if hrac_id in db and "prukazy" in db[hrac_id] and typ.value in db[hrac_id]["prukazy"]:
            db[hrac_id]["prukazy"].remove(typ.value)
            uloz_databazi(db)
            
            embed = discord.Embed(title="🚨 Zrušení platnosti průkazu", color=discord.Color.red())
            embed.add_field(name="Typ průkazu", value=f"**{typ.name}**", inline=False)
            embed.add_field(name="Odebráno majiteli", value=f"<@{hrac_id}> (ID: `{hrac_id}`)", inline=False)
            
            await interaction.response.send_message(embed=embed)
            await aktualizuj_mdt_profil(self.bot, hrac_id)
        else:
            await interaction.response.send_message("❌ Tento občan daný průkaz nevlastní.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(PrukazyCog(bot))
