import discord
from discord.ext import commands, tasks
from discord import app_commands
import pymongo
import random
from datetime import datetime, timedelta

# ==========================================
# NASTAVENÍ OPRÁVNĚNÍ A KANÁLŮ (Doplň správná ID pro Search Warrants!)
# ==========================================
ROLE_POLICIE_ID = 1523660335406383164  
ROLE_SOUDCE_ID = 1524106694915788870   

# Zde doplň ID nových kanálů podle tvého obrázku:
KANAL_ZADOST_ARCHIV_SW_ID = 1524108627353538803 # "# žádost-search-warrant" (Archiv)
KANAL_SOUD_SW_ID = 1524154021806608444          # "# search-warranty" (Stůl soudu)
KANAL_AKTIVNI_SW_ID = 1524134603357421659       # "# aktivní-search-warrant" (Rozeslání)

# ==========================================
# DATABÁZE
# ==========================================
MONGO_URI = "mongodb+srv://kubiqcz1:Aluska78@calicore.kmnmj4h.mongodb.net/?appName=CaliCore"
klient = pymongo.MongoClient(MONGO_URI)
db_cloud = klient["calicore_databaze"]
# Nová tabulka speciálně pro Search Warrants
kolekce_sw = db_cloud["search_warrants_log"] 

# --- TŘÍDA PRO FORMULÁŘ SOUDCE (Vydání SW) ---
class SoudceSWModal(discord.ui.Modal, title='Doplnění povolení k prohlídce'):
    jmeno_soudce = discord.ui.TextInput(label='Jméno soudce (Postava)', style=discord.TextStyle.short, required=True)
    nocni_sluzba = discord.ui.TextInput(label='Noční služba (Povoleno / Zamítnuto)', style=discord.TextStyle.short, required=True)
    no_knock = discord.ui.TextInput(label='Vstup bez zaklepání (Povoleno / Zamítnuto)', style=discord.TextStyle.short, required=True)

    def __init__(self, puvodni_zprava, puvodni_view):
        super().__init__()
        self.puvodni_zprava = puvodni_zprava
        self.puvodni_view = puvodni_view

    async def on_submit(self, interaction: discord.Interaction):
        embed = self.puvodni_zprava.embeds[0]
        
        # Přečtení metadat z footeru
        footer_text = embed.footer.text
        sw_cislo = footer_text.split(" | ")[0].replace("SW Číslo: ", "").strip()
        archiv_msg_id = int(footer_text.split(" | ")[1].replace("Archiv ID: ", "").strip())
        
        ted = datetime.now()

        # Doplnění textu zatykače
        novy_text = embed.description.replace("[ČEKÁ NA SOUDCE - NOC]", self.nocni_sluzba.value)
        novy_text = novy_text.replace("[ČEKÁ NA SOUDCE - NOKNOCK]", self.no_knock.value)
        novy_text = novy_text.replace("[ČEKÁ NA PODPIS SOUDCE]", self.jmeno_soudce.value)
        novy_text = novy_text.replace("[ČEKÁ NA ČAS VYDÁNÍ]", ted.strftime("%d.%m.%Y %H:%M"))

        embed.description = novy_text
        embed.color = discord.Color.green()
        embed.title = f"🏠 PŘÍKAZ K PROHLÍDCE VYDÁN (Aktivní)"

        # 1. Okamžité SMAZÁNÍ ze stolu soudu
        await self.puvodni_zprava.delete()

        # 2. Úprava zprávy v archivu
        kanal_archiv = interaction.client.get_channel(KANAL_ZADOST_ARCHIV_SW_ID)
        if kanal_archiv:
            try:
                msg_archiv = await kanal_archiv.fetch_message(archiv_msg_id)
                await msg_archiv.edit(embed=embed)
            except discord.NotFound: pass

        # 3. Odeslání do Přehledu aktivních SW
        kanal_aktivni = interaction.client.get_channel(KANAL_AKTIVNI_SW_ID)
        msg_aktivni = await kanal_aktivni.send(embed=embed) if kanal_aktivni else None

        # 4. Uložení do databáze (zde nepotřebujeme fórum)
        kolekce_sw.insert_one({
            "sw_cislo": sw_cislo,
            "msg_archiv_id": archiv_msg_id,
            "msg_aktivni_id": msg_aktivni.id if msg_aktivni else None,
            "vydano": ted,
            "status": "aktivni"
        })

        await interaction.response.send_message("✅ Povolení k prohlídce bylo vydáno a rozesláno.", ephemeral=True)

# --- TŘÍDA PRO TLAČÍTKA SOUDCE ---
class SearchWarrantView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Vydat povolení", style=discord.ButtonStyle.success, custom_id="sw_vydat", emoji="🟢")
    async def btn_vydat(self, interaction: discord.Interaction, button: discord.ui.Button):
        if ROLE_SOUDCE_ID not in [role.id for role in interaction.user.roles]:
            return await interaction.response.send_message("❌ Pouze Soudce!", ephemeral=True)
        await interaction.response.send_modal(SoudceSWModal(interaction.message, self))

    @discord.ui.button(label="Zamítnout", style=discord.ButtonStyle.danger, custom_id="sw_zamitnout", emoji="🔴")
    async def btn_zamitnout(self, interaction: discord.Interaction, button: discord.ui.Button):
        if ROLE_SOUDCE_ID not in [role.id for role in interaction.user.roles]:
            return await interaction.response.send_message("❌ Pouze Soudce!", ephemeral=True)

        embed = interaction.message.embeds[0]
        footer_text = embed.footer.text
        archiv_msg_id = int(footer_text.split(" | ")[1].replace("Archiv ID: ", "").strip())

        embed.color = discord.Color.red()
        embed.title = "📄 ŽÁDOST O PROHLÍDKU ZAMÍTNUTA"
        embed.description += f"\n\n**👨‍⚖️ Rozhodnutí soudu:** Zamítnuto soudcem {interaction.user.mention}"

        await interaction.message.delete()

        kanal_archiv = interaction.client.get_channel(KANAL_ZADOST_ARCHIV_SW_ID)
        if kanal_archiv:
            try:
                msg_archiv = await kanal_archiv.fetch_message(archiv_msg_id)
                await msg_archiv.edit(embed=embed)
            except discord.NotFound: pass
        
        await interaction.response.send_message("✅ Žádost byla zamítnuta a zaznamenána v archivu.", ephemeral=True)

# --- FORMULÁŘ PRO POLICISTU ---
class SearchWarrantModal(discord.ui.Modal, title='Příprava Search Warrant - Policie'):
    adresa = discord.ui.TextInput(label='Adresa / Lokace', style=discord.TextStyle.short, required=True)
    popis_mista = discord.ui.TextInput(label='Popis místa a vozidel k prohlídce', style=discord.TextStyle.paragraph, max_length=500, required=True)
    predmety = discord.ui.TextInput(label='Předměty k zabavení (Důkazy, drogy, zbraně)', style=discord.TextStyle.paragraph, max_length=800, required=True)
    duvod = discord.ui.TextInput(label='Důvodné podezření (Probable Cause)', style=discord.TextStyle.paragraph, max_length=800, required=True)
    pozadavky = discord.ui.TextInput(label='Speciální žádosti (Noc / Vstup bez zaklepání)', placeholder='Např. Žádáme o noční službu z důvodu...', style=discord.TextStyle.short, required=False)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        sw_cislo = str(random.randint(10000, 99999))

        sw_text = f"""**VRCHNÍ SOUD STÁTU KALIFORNIE, OKRES LOS ANGELES**
(SUPERIOR COURT OF CALIFORNIA, COUNTY OF LOS ANGELES)

**PŘÍKAZ K PROHLÍDCE (SEARCH WARRANT)**
Číslo příkazu: **SW-2026-{sw_cislo}**

**Žadatel (Affiant):** {interaction.user.mention}

**1. MÍSTO NEBO OSOBA K PROHLÍDCE:**
**Adresa/Lokace:** {self.adresa.value}
**Popis místa a vozidel:** {self.popis_mista.value}

**2. PŘEDMĚTY K ZABAVENÍ:**
{self.predmety.value}

**3. DŮVODNÉ PODEZŘENÍ (Probable Cause):**
{self.duvod.value}

**4. ZVLÁŠTNÍ OPRÁVNĚNÍ:**
*Poznámka žádajícího:* {self.pozadavky.value if self.pozadavky.value else "Žádné"}
**Noční služba (Night Service):** [ČEKÁ NA SOUDCE - NOC]
**Vstup bez zaklepání (No-Knock):** [ČEKÁ NA SOUDCE - NOKNOCK]

**PŘÍKAZ:**
Tímto nařizuji jakémukoliv strážci zákona (Peace Officer) v okrese Los Angeles vykonat tento příkaz k prohlídce, zajistit uvedené důkazy a doručit je soudu nebo zajistit jejich uložení v evidenci.

**Vydáno dne:** [ČEKÁ NA ČAS VYDÁNÍ]
**Podpis soudce:** *[ČEKÁ NA PODPIS SOUDCE]*
*(L.A. County Superior Court Judge)*"""

        embed = discord.Embed(title="⏳ ŽÁDOST O PROHLÍDKU (Čeká na soud)", color=discord.Color.orange(), description=sw_text)

        # 1. Odeslání do archivu
        kanal_archiv = self.bot.get_channel(KANAL_ZADOST_ARCHIV_SW_ID)
        msg_archiv = None
        if kanal_archiv:
            msg_archiv = await kanal_archiv.send(embed=embed)
        
        if msg_archiv:
            embed.set_footer(text=f"SW Číslo: {sw_cislo} | Archiv ID: {msg_archiv.id}")
            await msg_archiv.edit(embed=embed)

        # 2. Odeslání na stůl soudu
        kanal_soud = self.bot.get_channel(KANAL_SOUD_SW_ID)
        if kanal_soud:
            await kanal_soud.send(embed=embed, view=SearchWarrantView())
            await interaction.response.send_message(f"✅ Žádost SW-2026-{sw_cislo} odeslána k soudu.", ephemeral=True)

# --- HLAVNÍ TŘÍDA A PŘÍKAZY ---
class SearchWarrantCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.kontrola_expirace_sw.start() 

    # --- UZAVŘENÍ MANUÁLNĚ ---
    @app_commands.command(name="sw_uzavrit", description="Uzavře příkaz k prohlídce pomocí jeho 5místného čísla.")
    @app_commands.describe(cislo_prikazu="Pouze těch 5 čísel na konci (např. 12345)")
    async def sw_uzavrit_command(self, interaction: discord.Interaction, cislo_prikazu: str):
        if ROLE_POLICIE_ID not in [role.id for role in interaction.user.roles]:
            return await interaction.response.send_message("❌ Pouze Policie!", ephemeral=True)

        sw = kolekce_sw.find_one({"sw_cislo": cislo_prikazu.strip(), "status": "aktivni"})
        if not sw:
            return await interaction.response.send_message(f"❌ Nenašel jsem žádný aktivní příkaz s číslem SW-2026-{cislo_prikazu}.", ephemeral=True)

        await self.proved_uzavreni_sw(sw, f"Prohlídka vykonána/uzavřena: {interaction.user.mention}")
        await interaction.response.send_message(f"✅ Příkaz SW-2026-{cislo_prikazu} byl úspěšně uzavřen a stažen z aktivních.", ephemeral=True)

    # --- FUNKCE PRO UZAVŘENÍ SW ---
    async def proved_uzavreni_sw(self, sw_data, duvod_text):
        # 1. Zešednutí v Archivu
        kanal_archiv = self.bot.get_channel(KANAL_ZADOST_ARCHIV_SW_ID)
        if kanal_archiv and sw_data.get("msg_archiv_id"):
            try:
                msg_archiv = await kanal_archiv.fetch_message(sw_data["msg_archiv_id"])
                embed = msg_archiv.embeds[0]
                embed.color = discord.Color.dark_grey()
                embed.title = "🔒 PŘÍKAZ K PROHLÍDCE VYKONÁN / UZAVŘEN"
                embed.add_field(name="🚓 Uzavření operace", value=duvod_text, inline=False)
                await msg_archiv.edit(embed=embed)
            except discord.NotFound: pass

        # 2. Smazání z Aktivních
        kanal_aktivni = self.bot.get_channel(KANAL_AKTIVNI_SW_ID)
        if kanal_aktivni and sw_data.get("msg_aktivni_id"):
            try:
                msg_aktivni = await kanal_aktivni.fetch_message(sw_data["msg_aktivni_id"])
                await msg_aktivni.delete()
            except discord.NotFound: pass

        # Zápis do DB
        kolekce_sw.update_one({"_id": sw_data["_id"]}, {"$set": {"status": "uzavren"}})

    # --- AUTO-ZAVŘENÍ PO 48h ---
    @tasks.loop(hours=1)
    async def kontrola_expirace_sw(self):
        limit = datetime.now() - timedelta(hours=48)
        expirovane_sw = kolekce_sw.find({"status": "aktivni", "vydano": {"$lt": limit}})
        for sw in expirovane_sw:
            await self.proved_uzavreni_sw(sw, "Vypršela lhůta 48 hodin platnosti příkazu. Status: Uzavřeno.")

    @kontrola_expirace_sw.before_loop
    async def pred_spustenim(self):
        await self.bot.wait_until_ready()

    # --- SPOUŠTĚCÍ PŘÍKAZ ---
    @app_commands.command(name="zadost_search_warrant", description="Vytvoří žádost o příkaz k domovní prohlídce (Search Warrant).")
    async def zadost_sw_command(self, interaction: discord.Interaction):
        if ROLE_POLICIE_ID not in [role.id for role in interaction.user.roles]:
            return await interaction.response.send_message("❌ Pouze Policie!", ephemeral=True)
        await interaction.response.send_modal(SearchWarrantModal(self.bot))

async def setup(bot):
    await bot.add_cog(SearchWarrantCog(bot))
