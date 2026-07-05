import discord
from discord.ext import commands
from discord import app_commands
import json
import os

from cogs.profil import aktualizuj_mdt_profil

# ==========================================
# ID KANÁLŮ - ZDE SI DOPLŇ SVÁ ČÍSLA!
# ==========================================
MDT_REGISTR_VOZIDEL_ID = 1522684016388472983 
MDT_ZBRANE_ID = 1522683939964063794 
MDT_PRUKAZY_ID = 1522513841705975869

DATABAZE_SOUBOR = "databaze_hracu.json"

def nacti_databazi():
    if not os.path.exists(DATABAZE_SOUBOR):
        return {}
    with open(DATABAZE_SOUBOR, "r") as f:
        return json.load(f)

def uloz_databazi(data):
    with open(DATABAZE_SOUBOR, "w") as f:
        json.dump(data, f, indent=4)

# ==========================================
# SEZNAMY (VOZIDLA, ZBRANĚ, PRŮKAZY)
# ==========================================
SEZNAM_VOZIDEL = [
    "Arrow Phoenix Nationals (1977)", "Averon Anodic (2024)", "Averon Bremen VS Garde (2023)", "Averon LM (2020)", "Averon LM R (2020)", "Averon Q8 (2022)", "Averon RS3 (2020)", "Averon S5 (2010)", 
    "BKM Munich (2020)", "BKM Risen Roadster (2020)", "Bullhorn BH15 (2009)", "Bullhorn Determinator (2008)", "Bullhorn Determinator C/T (2022)", "Bullhorn Determinator SFP Blackjack Widebody (2022)", "Bullhorn Determinator SFP Fury (2022)", "Bullhorn Foreman (1988)", "Bullhorn Prancer (1969)", "Bullhorn Prancer C/T (2020)", "Bullhorn Prancer Colonel Fields (1969)", "Bullhorn Prancer Fury Widebody (2020)", "Bullhorn Prancer Hotrod (1969)", "Bullhorn Prancer S (2011)", "Bullhorn Prancer Talladega (1969)", "Bullhorn Pueblo SFP Fury (2022)", "Bullhorn Pueblo V6 (2022)", 
    "Celestial Truckatron (2024)", "Celestial Type-5 (2022)", "Celestial Type-6 (2024)", "Celestial Type-7 (2022)", "Chevlon Amigo LZR (2011)", "Chevlon Amigo S (2011)", "Chevlon Amigo S (2016)", "Chevlon Camion (2008)", "Chevlon Camion (2018)", "Chevlon Camion (2021)", "Chevlon Camion GMT 800 LT (2002)", "Chevlon Camion GMT 800 LTS (2002)", "Chevlon Camion GMT 800 S (2002)", "Chevlon Captain (1992)", "Chevlon Captain (2009)", "Chevlon Captain Antelope SS (1994)", "Chevlon Captain LTZ (1994)", "Chevlon Commuter Van (2006)", "Chevlon Corbeta 8 (2023)", "Chevlon Corbeta C2 (1967)", "Chevlon Corbeta RZR (2014)", "Chevlon Corbeta X08 (2014)", "Chevlon Inferno (1981)", "Chevlon L/15 (1981)", "Chevlon L/15 Side Step (1981)", "Chevlon L/35 Extended (1981)", "Chevlon Landslide (2007)", "Chevlon Platoro (2019)", "Chevlon Revver (2005)", 
    "Chryslus Champion (2005)", "Elysion Slick (2014)", "Falcon Advance 100 (1956)", "Falcon Advance 350 (2020)", "Falcon Advance 350 Royal Ranch (2020)", "Falcon Advance 450 (2020)", "Falcon Advance 450 Royal Ranch (2020)", "Falcon Aquarius STP (2017)", "Falcon eStallion (2024)", "Falcon Heritage (2021)", "Falcon Heritage Track (2022)", "Falcon Prime Eques (2003)", "Falcon Rampage Beast (2021)", "Falcon Rampage Bigfoot 2-Door (2021)", "Falcon Rampage Prairie (2021)", "Falcon Scavenger (2013)", "Falcon Scavenger (2016)", "Falcon Scavenger Royal Ranch (2024)", "Falcon Stallion 350 (1969)", "Falcon Stallion 350 (2015)", "Falcon Traveller (2022)", 
    "Ferdinand Jalapeno Turbo (2022)", "Kovac Heladera (2023)", "Leland LTS (2010)", "Leland LTS5-V Blackwing (2023)", "Leland Vault (2020)", "Navara Boundary (2022)", "Navara Horizon (2013)", "Navara Imperium (2020)", "Overland Apache (1995)", "Overland Apache (2011)", "Overland Apache SFP (2020)", "Overland Buckaroo (2018)", "Sentinel Platinum (1968)", "Strugatti Ettore (2020)", "Stuttgart Landschaft (2022)", "Stuttgart Vierturig (2021)", "Sumo Reflexion (2022)", "Surrey 650S (2016)", "Takeo Experience (2021)", "Terrain Traveller (2022)", 
    "Vellfire Everest VRD Max (2023)", "Vellfire Evertt Extended Cab (1995)", "Vellfire Pioneer (2019)", "Vellfire Pioneer Targa (2019)", "Vellfire Prairie (2022)", "Vellfire Prima (2009)", "Vellfire Riptide (2020)", "Vellfire Runabout (1984)", "Lawn Mower", "4-Wheeler", "Canyon Descender", "C18 Camper Trailer"
]

zbrane_choices = [
    app_commands.Choice(name="Berreta M9", value="Berreta M9"),
    app_commands.Choice(name="Colt M1911", value="Colt M1911"),
    app_commands.Choice(name="Colt Python", value="Colt Python"),
    app_commands.Choice(name="Remington 870", value="Remington 870"),
    app_commands.Choice(name="Remington 700", value="Remington 700"),
    app_commands.Choice(name="M14", value="M14"),
    app_commands.Choice(name="LMT L129A1", value="LMT L129A1")
]

prukazy_choices = [
    app_commands.Choice(name="Řidičský průkaz - A (Moto)", value="rp_a"),
    app_commands.Choice(name="Řidičský průkaz - B (Auto)", value="rp_b"),
    app_commands.Choice(name="Řidičský průkaz - C (Náklaďák)", value="rp_c"),
    app_commands.Choice(name="Řidičský průkaz - T (Traktor)", value="rp_t"),
    app_commands.Choice(name="Zbrojní průkaz - Skupina A", value="zp_a"),
    app_commands.Choice(name="Zbrojní průkaz - Skupina B", value="zp_b"),
    app_commands.Choice(name="Zbrojní průkaz - Skupina C", value="zp_c"),
]

# ==========================================
# HLAVNÍ TŘÍDA PRO MDT
# ==========================================
class MdtCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -----------------------------------------------------
    # VYTVOŘENÍ KATEGORIE /mdt
    # -----------------------------------------------------
    mdt = app_commands.Group(name="mdt", description="Policejní a úřední databáze (zbraně, vozidla, průkazy)")

    # Funkce našeptávače pro vozidla
    async def auto_naseptavac(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        shody = [auto for auto in SEZNAM_VOZIDEL if current.lower() in auto.lower()]
        return [app_commands.Choice(name=auto, value=auto) for auto in shody][:25]

    # -----------------------------------------------------
    # 1. SEKCE: VOZIDLA
    # -----------------------------------------------------
    @mdt.command(name="registrovat_vozidlo", description="Zaregistruje vozidlo na občana.")
    @app_commands.describe(hrac_id="Číslo ID občana", model="Začni psát značku auta...", barva="Barva vozidla", spz="SPZ ze hry")
    @app_commands.autocomplete(model=auto_naseptavac)
    async def registrovat_vozidlo(self, interaction: discord.Interaction, hrac_id: str, model: str, barva: str, spz: str):
        if interaction.channel_id != MDT_REGISTR_VOZIDEL_ID:
            await interaction.response.send_message("❌ Tento příkaz lze použít pouze v kanálu pro registr vozidel.", ephemeral=True)
            return

        db = nacti_databazi()
        if hrac_id not in db: db[hrac_id] = {"prukazy": [], "zbrane": [], "vozidla": []}
        if "vozidla" not in db[hrac_id]: db[hrac_id]["vozidla"] = []

        spz_upper = spz.upper().strip()
        for v in db[hrac_id]["vozidla"]:
            if v["spz"] == spz_upper:
                await interaction.response.send_message(f"❌ Vozidlo se značkou `{spz_upper}` už občan vlastní.", ephemeral=True)
                return

        db[hrac_id]["vozidla"].append({"model": model, "barva": barva, "spz": spz_upper})
        uloz_databazi(db)

        embed = discord.Embed(title="🚘 Záznam o registraci vozidla", color=discord.Color.blue())
        embed.add_field(name="Vozidlo", value=f"**{model}**", inline=False)
        embed.add_field(name="Barva", value=barva, inline=True)
        embed.add_field(name="SPZ (RZ)", value=f"`{spz_upper}`", inline=True)
        embed.add_field(name="Majitel", value=f"<@{hrac_id}> (ID: `{hrac_id}`)", inline=False)
        
        await interaction.response.send_message(embed=embed)
        await aktualizuj_mdt_profil(self.bot, hrac_id)

    @mdt.command(name="odstranit_vozidlo", description="Odstraní vozidlo z registru občana (dle SPZ).")
    @app_commands.describe(hrac_id="Číslo ID občana", spz="SPZ vozidla ke smazání")
    async def odstranit_vozidlo(self, interaction: discord.Interaction, hrac_id: str, spz: str):
        if interaction.channel_id != MDT_REGISTR_VOZIDEL_ID:
            await interaction.response.send_message("❌ Tento příkaz lze použít pouze v kanálu pro registr vozidel.", ephemeral=True)
            return

        db = nacti_databazi()
        spz_upper = spz.upper().strip()

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
                await interaction.response.send_message(f"❌ Vozidlo se SPZ `{spz_upper}` u tohoto občana nebylo nalezeno.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Občan nemá registrovaná žádná vozidla.", ephemeral=True)

    # -----------------------------------------------------
    # 2. SEKCE: ZBRANĚ
    # -----------------------------------------------------
    @mdt.command(name="registrovat_zbran", description="Zaregistruje zbraň na občana.")
    @app_commands.describe(hrac_id="Číslo ID občana", model="Vyber model zbraně ze seznamu", seriove_cislo="Sériové číslo ze hry")
    @app_commands.choices(model=zbrane_choices)
    async def registrovat_zbran(self, interaction: discord.Interaction, hrac_id: str, model: app_commands.Choice[str], seriove_cislo: str):
        if interaction.channel_id != MDT_ZBRANE_ID:
            await interaction.response.send_message("❌ Tento příkaz lze použít pouze v kanálu pro zbraně.", ephemeral=True)
            return

        db = nacti_databazi()
        if hrac_id not in db: db[hrac_id] = {"prukazy": [], "zbrane": [], "vozidla": []}
        if "zbrane" not in db[hrac_id]: db[hrac_id]["zbrane"] = []

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

    @mdt.command(name="odebrat_zbran", description="Smaže zbraň z registru občana.")
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

    # -----------------------------------------------------
    # 3. SEKCE: PRŮKAZY
    # -----------------------------------------------------
    @mdt.command(name="vydat_prukaz", description="Vydá občanu průkaz / licenci.")
    @app_commands.describe(hrac_id="Číslo ID občana", typ="Vyber typ průkazu")
    @app_commands.choices(typ=prukazy_choices)
    async def vydat_prukaz(self, interaction: discord.Interaction, hrac_id: str, typ: app_commands.Choice[str]):
        if interaction.channel_id != MDT_PRUKAZY_ID:
            await interaction.response.send_message("❌ Tento příkaz lze použít pouze v kanálu pro průkazy.", ephemeral=True)
            return

        db = nacti_databazi()
        if hrac_id not in db: db[hrac_id] = {"prukazy": [], "zbrane": [], "vozidla": []}
        if "prukazy" not in db[hrac_id]: db[hrac_id]["prukazy"] = []

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

    @mdt.command(name="odebrat_prukaz", description="Odebere občanu průkaz / licenci.")
    @app_commands.describe(hrac_id="Číslo ID občana", typ="Vyber typ průkazu ke smazání")
    @app_commands.choices(typ=prukazy_choices)
    async def odebrat_prukaz(self, interaction: discord.Interaction, hrac_id: str, typ: app_commands.Choice[str]):
        if interaction.channel_id != MDT_PRUKAZY_ID:
            await interaction.response.send_message("❌ Tento příkaz lze použít pouze v kanálu pro průkazy.", ephemeral=True)
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
    await bot.add_cog(MdtCog(bot))
