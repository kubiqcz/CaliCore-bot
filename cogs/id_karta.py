import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# IMPORTUJEME TABULKU Z NAŠEHO PROFILU!
from cogs.profil import vytvor_profil_embed

MDT_FORUM_ID = 1453745209643896933  # DOPLŇ ID TVÉHO MDT FÓRA PRO SLOŽKY
DATABAZE_SOUBOR = "databaze_hracu.json"

def nacti_databazi():
    if not os.path.exists(DATABAZE_SOUBOR):
        return {}
    with open(DATABAZE_SOUBOR, "r") as f:
        return json.load(f)

def uloz_databazi(data):
    with open(DATABAZE_SOUBOR, "w") as f:
        json.dump(data, f, indent=4)

class IdKartaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="id", description="Založí novou ID kartu a složku občana v MDT fóru.")
    @app_commands.describe(jmeno="Tvé jméno", prijmeni="Tvé příjmení", datum_narozeni="Datum narození")
    async def id_command(self, interaction: discord.Interaction, jmeno: str, prijmeni: str, datum_narozeni: str):
        # Defer - Dáme botovi čas přemýšlet, aby příkaz nespadl na timeout
        await interaction.response.defer(ephemeral=True) 

        forum = self.bot.get_channel(MDT_FORUM_ID)
        if not forum or not isinstance(forum, discord.ForumChannel):
            await interaction.followup.send("❌ Chyba: Kanál fóra nebyl nalezen nebo to není fórum.")
            return

        hrac_id_str = str(interaction.user.id)
        nazev_vlakna = f"{jmeno} {prijmeni} - ID: {hrac_id_str}"

        # 1. Tvorba modré ID Karty (Zakládací zpráva)
        embed_id = discord.Embed(title="🪪 Průkaz Totožnosti (ID Karta)", color=discord.Color.blue())
        embed_id.add_field(name="Jméno", value=jmeno, inline=True)
        embed_id.add_field(name="Příjmení", value=prijmeni, inline=True)
        embed_id.add_field(name="Datum narození", value=datum_narozeni, inline=False)
        embed_id.add_field(name="Číslo ID", value=f"`{hrac_id_str}`", inline=False)
        embed_id.set_thumbnail(url=interaction.user.display_avatar.url)
        embed_id.set_footer(text="Oficiální záznam státní správy")

        # 2. Vytvoříme vlákno a pošleme do něj ID Kartu
        vytvorene_vlakno = await forum.create_thread(name=nazev_vlakna, embed=embed_id)
        vlakno = vytvorene_vlakno.thread

        # 3. Načteme databázi a vytvoříme hráči čistý záznam, pokud ho nemá
        db = nacti_databazi()
        if hrac_id_str not in db:
            db[hrac_id_str] = {"prukazy": [], "zbrane": [], "vozidla": []}

        # 4. Vygenerujeme druhou zprávu (Živý profil) a pošleme ji HNED POD ID Kartu
        profil_embed = vytvor_profil_embed(hrac_id_str, interaction.user.mention, db)
        profil_zprava = await vlakno.send(embed=profil_embed)

        # 5. ULOŽÍME SI ID ZPRÁVY DO PAMĚTI! (Tady se děje to hlavní kouzlo)
        db[hrac_id_str]["mdt_vlakno_id"] = vlakno.id
        db[hrac_id_str]["mdt_zprava_id"] = profil_zprava.id
        uloz_databazi(db)

        await interaction.followup.send(f"✅ Tvoje ID Karta a MDT složka byla úspěšně založena: {vlakno.mention}")

async def setup(bot):
    await bot.add_cog(IdKartaCog(bot))
