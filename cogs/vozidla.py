import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# IMPORT AKTUALIZAČNÍ FUNKCE
from cogs.profil import aktualizuj_mdt_profil

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


# VYSKAKOVACÍ OKNO PRO REGISTRACI VOZIDLA
class RegistraceVozidlaModal(discord.ui.Modal, title='Registrace nového vozidla'):
    hrac_id = discord.ui.TextInput(
        label='Číslo ID občana',
        placeholder='Např. 828545265531093063',
        required=True
    )
    vozidlo = discord.ui.TextInput(
        label='Značka a model vozidla',
        placeholder='Např. Averon Bremen VS Garde',
        required=True
    )
    barva = discord.ui.TextInput(
        label='Barva vozidla',
        placeholder='Např. Černá',
        required=True
    )
    spz = discord.ui.TextInput(
        label='SPZ (RZ) ze hry',
        placeholder='Např. ABC-123',
        required=True,
        max_length=8
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        db = nacti_databazi()
        id_str = self.hrac_id.value.strip()
        
        if id_str not in db:
            db[id_str] = {"prukazy": [], "zbrane": [], "vozidla": []}
        if "vozidla" not in db[id_str]:
            db[id_str]["vozidla"] = []

        spz_upper = self.spz.value.upper().strip()
        
        for v in db[id_str]["vozidla"]:
            if v["spz"] == spz_upper:
                await interaction.response.send_message(f"❌ Vozidlo se značkou `{spz_upper}` už občan s ID `{id_str}` vlastní.", ephemeral=True)
                return

        db[id_str]["vozidla"].append({"model": self.vozidlo.value, "barva": self.barva.value, "spz": spz_upper})
        uloz_databazi(db)

        embed = discord.Embed(title="🚘 Záznam o registraci vozidla", color=discord.Color.blue())
        embed.add_field(name="Vozidlo", value=f"**{self.vozidlo.value}**", inline=False)
        embed.add_field(name="Barva", value=self.barva.value, inline=True)
        embed.add_field(name="SPZ (RZ)", value=f"`{spz_upper}`", inline=True)
        embed.add_field(name="Majitel", value=f"<@{id_str}> (ID: `{id_str}`)", inline=False)
        embed.set_footer(text="CaliCore MDT System | Vozidlo uloženo do databáze")
        
        # 1. OKAMŽITĚ ODPOVÍME DISCORDU
        await interaction.response.send_message(embed=embed)
        
        # 2. AŽ POTOM AKTUALIZUJEME FÓRUM NA POZADÍ
        await aktualizuj_mdt_profil(self.bot, id_str)


class VozidlaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="registrovat_vozidlo", description="[MDT] Otevře formulář pro registraci vozidla na občana.")
    async def registrovat_vozidlo(self, interaction: discord.Interaction):
        if interaction.channel_id != MDT_REGISTR_VOZIDEL_ID:
            await interaction.response.send_message("❌ Tento příkaz lze použít pouze v kanálu pro registr vozidel.", ephemeral=True)
            return
        
        # Otevře to naše nové vyskakovací okno
        await interaction.response.send_modal(RegistraceVozidlaModal(self.bot))

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
                uloz_databazi(db)
                
                embed = discord.Embed(title="🚨 Záznam o vyřazení vozidla", color=discord.Color.red())
                embed.add_field(name="SPZ (RZ)", value=f"`{spz_upper}`", inline=False)
                embed.add_field(name="Odebráno majiteli", value=f"<@{hrac_id}>", inline=True)
                
                await interaction.response.send_message(embed=embed)
                await aktualizuj_mdt_profil(self.bot, hrac_id)
            else:
                await interaction.response.send_message(f"Vozidlo se SPZ `{spz_upper}` u tohoto občana nebylo nalezeno.", ephemeral=True)
        else:
            await interaction.response.send_message("Občan nemá registrovaná žádná vozidla.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(VozidlaCog(bot))
