import discord
from discord.ext import commands
from discord import app_commands
import pymongo
import random
from datetime import datetime

# ==========================================
# NASTAVENÍ OPRÁVNĚNÍ A KANÁLŮ
# ==========================================
ROLE_POLICIE_ID = 1523660335406383164  
ROLE_SOUDCE_ID = 1524106694915788870   
KANAL_SOUD_ID = 1524108627353538803    
KANAL_AKTIVNI_ZATYKACE_ID = 1524108142206652416 

MONGO_URI = "mongodb+srv://kubiqcz1:Aluska78@calicore.kmnmj4h.mongodb.net/?appName=CaliCore"
klient = pymongo.MongoClient(MONGO_URI)
db_cloud = klient["calicore_databaze"]
kolekce_hraci = db_cloud["hraci"]

def nacti_databazi():
    data = {}
    for hrac in kolekce_hraci.find():
        data[str(hrac["_id"])] = hrac
    return data

# --- TŘÍDA PRO FORMULÁŘ SOUDCE (Doplnění údajů) ---
class SoudceZatykacModal(discord.ui.Modal, title='Doplnění zatykače soudu'):
    jmeno_soudce = discord.ui.TextInput(
        label='Jméno soudce (Postava)', 
        style=discord.TextStyle.short, 
        placeholder='JUDr. Antonín Sova', 
        required=True
    )
    
    vykon_noc = discord.ui.TextInput(
        label='Výkon v noci (Zločin / Přečin / ZAMÍTNUTO)', 
        style=discord.TextStyle.short, 
        placeholder='Např: Zločin (Lze vykonat v noci)', 
        required=True
    )
    
    kauce = discord.ui.TextInput(
        label='Kauce', 
        style=discord.TextStyle.short, 
        placeholder='Např: $50,000 nebo Bez kauce', 
        required=True
    )

    def __init__(self, puvodni_zprava, puvodni_view):
        super().__init__()
        self.puvodni_zprava = puvodni_zprava
        self.puvodni_view = puvodni_view

    async def on_submit(self, interaction: discord.Interaction):
        embed = self.puvodni_zprava.embeds[0]
        
        footer_text = embed.footer.text
        hrac_id = footer_text.replace("Číslo průkazu cíle: ", "").strip()

        # Aktuální čas vydání
        ted = datetime.now().strftime("%d.%m.%Y %H:%M")

        # Nahrazení placeholderů (zástupných textů) hodnotami od soudce
        novy_text = embed.description.replace("[ČEKÁ NA ROZHODNUTÍ SOUDCE - NOC]", self.vykon_noc.value)
        novy_text = novy_text.replace("[ČEKÁ NA ROZHODNUTÍ SOUDCE - KAUCE]", self.kauce.value)
        novy_text = novy_text.replace("[ČEKÁ NA PODPIS SOUDCE]", self.jmeno_soudce.value)
        novy_text = novy_text.replace("[ČEKÁ NA ČAS VYDÁNÍ]", ted)

        embed.description = novy_text
        embed.color = discord.Color.green()
        embed.title = "📄 ZATYKAČ VYDÁN (Schváleno)"

        # Vypnutí tlačítek
        for child in self.puvodni_view.children:
            child.disabled = True
        await self.puvodni_zprava.edit(embed=embed, view=self.puvodni_view)

        # Rozeslání do kanálů
        kanal_aktivni = interaction.client.get_channel(KANAL_AKTIVNI_ZATYKACE_ID)
        if kanal_aktivni:
            await kanal_aktivni.send(embed=embed)

        db = nacti_databazi()
        if hrac_id in db:
            vlakno_id = db[hrac_id].get("mdt_vlakno_id")
            if vlakno_id:
                vlakno = interaction.client.get_channel(vlakno_id)
                if vlakno:
                    await vlakno.send(embed=embed)

        await interaction.response.send_message("✅ Zatykač byl úspěšně doplněn, podepsán a vydán.", ephemeral=True)


# --- TŘÍDA PRO TLAČÍTKA (SOUDCE) ---
class ZatykacView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Vydat zatykač", style=discord.ButtonStyle.success, custom_id="zatykac_vydat", emoji="🟢")
    async def btn_vydat(self, interaction: discord.Interaction, button: discord.ui.Button):
        if ROLE_SOUDCE_ID not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("❌ Na toto rozhodnutí má právo pouze Soudce!", ephemeral=True)
            return

        # Namísto podpisu nyní soudce doplňuje i kauci a noční prohlídku
        await interaction.response.send_modal(SoudceZatykacModal(interaction.message, self))

    @discord.ui.button(label="Zamítnout", style=discord.ButtonStyle.danger, custom_id="zatykac_zamitnout", emoji="🔴")
    async def btn_zamitnout(self, interaction: discord.Interaction, button: discord.ui.Button):
        if ROLE_SOUDCE_ID not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("❌ Na toto rozhodnutí má právo pouze Soudce!", ephemeral=True)
            return

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = "📄 ZÁDOST O ZATYKAČ ZAMÍTNUTA"
        embed.description = embed.description + f"\n\n**👨‍⚖️ Rozhodnutí soudu:** Zamítnuto soudcem {interaction.user.mention}"

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message("✅ Žádost byla zamítnuta.", ephemeral=True)


# --- TŘÍDA PRO FORMULÁŘ (POLICISTA) ---
class ZatykacModal(discord.ui.Modal, title='Příprava Zatykače - Policie'):
    cislo_prukazu = discord.ui.TextInput(
        label='Číslo průkazu (ID hráče)', 
        style=discord.TextStyle.short, 
        required=True
    )
    
    obvineni = discord.ui.TextInput(
        label='Trestné činy (Obvinění)', 
        style=discord.TextStyle.paragraph,
        placeholder='Vypsat jednotlivé paragrafy a obvinění...', 
        required=True,
        max_length=1000
    )
    
    adresa = discord.ui.TextInput(
        label='Poslední známá adresa (Místo)', 
        style=discord.TextStyle.short,
        placeholder='Např: Motel na Vinewoodu, pokoj 12', 
        required=True
    )
    
    fyzicky_popis = discord.ui.TextInput(
        label='Pohlaví / Rasa / Vzhled / Jizvy / Tetování', 
        style=discord.TextStyle.paragraph,
        placeholder='Např: Muž, Kavkazská rasa, černé vlasy, jizva na tváři...', 
        required=True
    )
    
    dalsi_info = discord.ui.TextInput(
        label='Další informace k zatykači', 
        style=discord.TextStyle.paragraph,
        placeholder='Nezbytné detaily k provedení zatčení (ozbrojen a nebezpečný)...', 
        required=False
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        # 1. Zjistíme informace z databáze
        db = nacti_databazi()
        hrac_id = self.cislo_prukazu.value.strip()
        
        jmeno_hrace = "Neznámá identita"
        vozidla_text = "Žádná registrovaná vozidla"

        if hrac_id in db:
            jmeno_hrace = db[hrac_id].get("jmeno", "Neznámá identita")
            # Pokud má registrovaná vozidla, uděláme z nich seznam. Pokud ne, zůstane text výše.
            vozidla_seznam = db[hrac_id].get("vozidla", [])
            if vozidla_seznam:
                # Zkusí vypsat modely vozidel (upraveno na model/spz pokud existují)
                vozidla_text = ", ".join([str(v) for v in vozidla_seznam]) 

        # Generování náhodného čísla zatykače
        cislo_zatykace = random.randint(10000, 99999)

        # 2. Sestavení obrovské šablony zatykače
        zatykac_text = f"""**VRCHNÍ SOUD STÁTU KALIFORNIE**
Okres Los Angeles

**ZATYKAČ**
Běžný zatykač
Trestní zákoník §§ 813-5

**LID STÁTU KALIFORNIE**
Všem kalifornským strážcům zákona
Zatykač č. **FW-{cislo_zatykace}**

**Jméno obžalovaného:** {jmeno_hrace}

**Příkaz:** Vzhledem k tomu, že k tomuto soudu byla dnešního dne podána stížnost pod přísahou, která viní výše uvedeného obžalovaného z níže uvedeného trestného činu (trestných činů), nařizuje se vám tímto, abyste výše uvedeného obžalovaného neprodleně zatkli a předvedli jej přede mne, nebo v případě mé nepřítomnosti či neschopnosti jednat, před nejbližšího a nejdostupnějšího smírčího soudce v tomto okrese.

**Obvinění z trestných činů:** {self.obvineni.value}

**Povolení k výkonu v noci:** [ČEKÁ NA ROZHODNUTÍ SOUDCE - NOC]

**Kauce:** [ČEKÁ NA ROZHODNUTÍ SOUDCE - KAUCE]

**Datum a čas vydání zatykače:** [ČEKÁ NA ČAS VYDÁNÍ]
**Soudce vrchního soudu:** *[ČEKÁ NA PODPIS SOUDCE]*

---
♦ **Informace o zatýkaném** ♦
*Pouze pro účely identifikace*

**Jméno:** {jmeno_hrace}
**Známý také jako (AKA's):** -
**Poslední známá adresa:** {self.adresa.value}
**Fyzický popis:** {self.fyzicky_popis.value}
**Vozidla spojená se zatýkaným:** {vozidla_text}
**Další informace:** {self.dalsi_info.value if self.dalsi_info.value else "Žádné"}
"""

        embed = discord.Embed(title="⚖️ NOVÁ ŽÁDOST O ZATYKAČ", color=discord.Color.orange(), description=zatykac_text)
        embed.set_footer(text=f"Číslo průkazu cíle: {hrac_id}")

        await interaction.response.send_message("✅ Tvá žádost (se všemi údaji z databáze) byla odeslána soudu k posouzení.", ephemeral=True)

        kanal_soud = self.bot.get_channel(KANAL_SOUD_ID)
        if kanal_soud:
            await kanal_soud.send(embed=embed, view=ZatykacView())

# --- SAMOTNÝ PŘÍKAZ ---
class ZatykacCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="zadost_zatykac", description="Vytvoří plně formátovanou žádost o zatykač na soud.")
    async def zadost_zatykac_command(self, interaction: discord.Interaction):
        if ROLE_POLICIE_ID not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("❌ Tento příkaz může použít pouze Policie!", ephemeral=True)
            return

        await interaction.response.send_modal(ZatykacModal(self.bot))

async def setup(bot):
    await bot.add_cog(ZatykacCog(bot))
