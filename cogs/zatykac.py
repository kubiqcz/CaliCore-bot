import discord
from discord.ext import commands, tasks
from discord import app_commands
import pymongo
import random
from datetime import datetime, timedelta

# ==========================================
# NASTAVENÍ OPRÁVNĚNÍ A KANÁLŮ
# ==========================================
ROLE_POLICIE_ID = 1523660335406383164  
ROLE_SOUDCE_ID = 1524106694915788870   

# Kanál, kam policisté píšou /zadost_zatykac a kde zůstává trvalá stopa (Archiv)
KANAL_ZADOST_ARCHIV_ID = 1524108627353538803 # <--- DOPLŇ ID KANÁLU "žádost-o-zatykač"

# Soudcův stůl (jen tlačítka, zprávy po kliknutí mizí)
KANAL_SOUD_ID = 1524108627353538803    

# Aktivní zatykače pro policii (po uzavření se mažou)
KANAL_AKTIVNI_ZATYKACE_ID = 1524108142206652416 

# ==========================================
# DATABÁZE
# ==========================================
MONGO_URI = "mongodb+srv://kubiqcz1:Aluska78@calicore.kmnmj4h.mongodb.net/?appName=CaliCore"
klient = pymongo.MongoClient(MONGO_URI)
db_cloud = klient["calicore_databaze"]
kolekce_hraci = db_cloud["hraci"]
kolekce_zatykace = db_cloud["zatykace_log"] 

def nacti_hrace():
    data = {}
    for hrac in kolekce_hraci.find():
        data[str(hrac["_id"])] = hrac
    return data

# --- TŘÍDA PRO FORMULÁŘ SOUDCE (Vydání) ---
class SoudceZatykacModal(discord.ui.Modal, title='Doplnění zatykače soudu'):
    jmeno_soudce = discord.ui.TextInput(label='Jméno soudce (Postava)', style=discord.TextStyle.short, required=True)
    vykon_noc = discord.ui.TextInput(label='Výkon v noci', style=discord.TextStyle.short, required=True)
    kauce = discord.ui.TextInput(label='Kauce', style=discord.TextStyle.short, required=True)

    def __init__(self, puvodni_zprava, puvodni_view):
        super().__init__()
        self.puvodni_zprava = puvodni_zprava
        self.puvodni_view = puvodni_view

    async def on_submit(self, interaction: discord.Interaction):
        embed = self.puvodni_zprava.embeds[0]
        
        # Získání ID hráče a ID zprávy v archivu z patičky (footeru)
        footer_text = embed.footer.text
        hrac_id = footer_text.split(" | ")[0].replace("Číslo průkazu cíle: ", "").strip()
        archiv_msg_id = int(footer_text.split(" | ")[1].replace("Archiv ID: ", "").strip())
        
        ted = datetime.now()

        # Doplnění textu
        novy_text = embed.description.replace("[ČEKÁ NA ROZHODNUTÍ SOUDCE - NOC]", self.vykon_noc.value)
        novy_text = novy_text.replace("[ČEKÁ NA ROZHODNUTÍ SOUDCE - KAUCE]", self.kauce.value)
        novy_text = novy_text.replace("[ČEKÁ NA PODPIS SOUDCE]", self.jmeno_soudce.value)
        novy_text = novy_text.replace("[ČEKÁ NA ČAS VYDÁNÍ]", ted.strftime("%d.%m.%Y %H:%M"))

        embed.description = novy_text
        embed.color = discord.Color.green()
        embed.title = "📄 ZATYKAČ VYDÁN (Aktivní)"

        # 1. Okamžité SMAZÁNÍ zprávy ze stolu soudu
        await self.puvodni_zprava.delete()

        # 2. Úprava existující zprávy v kanálu žádost-o-zatykač (Archiv)
        kanal_archiv = interaction.client.get_channel(KANAL_ZADOST_ARCHIV_ID)
        if kanal_archiv:
            try:
                msg_archiv = await kanal_archiv.fetch_message(archiv_msg_id)
                await msg_archiv.edit(embed=embed)
            except discord.NotFound: pass

        # 3. Odeslání do Přehledu aktivních zatykačů
        kanal_aktivni = interaction.client.get_channel(KANAL_AKTIVNI_ZATYKACE_ID)
        msg_aktivni = await kanal_aktivni.send(embed=embed) if kanal_aktivni else None

        # 4. Odeslání do složky hráče (databáze-občanů)
        db_hraci = nacti_hrace()
        msg_forum_id = None
        vlakno_id = None
        if hrac_id in db_hraci:
            vlakno_id = db_hraci[hrac_id].get("mdt_vlakno_id")
            if vlakno_id:
                vlakno = interaction.client.get_channel(vlakno_id)
                if vlakno:
                    msg_forum = await vlakno.send(embed=embed)
                    msg_forum_id = msg_forum.id

        # 5. Uložení ID do databáze pro budoucí smazání/úpravu
        kolekce_zatykace.insert_one({
            "hrac_id": hrac_id,
            "msg_archiv_id": archiv_msg_id,
            "msg_aktivni_id": msg_aktivni.id if msg_aktivni else None,
            "msg_forum_id": msg_forum_id,
            "vlakno_id": vlakno_id,
            "vydano": ted,
            "status": "aktivni"
        })

        await interaction.response.send_message("✅ Zatykač byl vydán a rozeslán do databází.", ephemeral=True)

# --- TŘÍDA PRO TLAČÍTKA SOUDCE ---
class ZatykacView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Vydat zatykač", style=discord.ButtonStyle.success, custom_id="zatykac_vydat", emoji="🟢")
    async def btn_vydat(self, interaction: discord.Interaction, button: discord.ui.Button):
        if ROLE_SOUDCE_ID not in [role.id for role in interaction.user.roles]:
            return await interaction.response.send_message("❌ Pouze Soudce!", ephemeral=True)
        await interaction.response.send_modal(SoudceZatykacModal(interaction.message, self))

    @discord.ui.button(label="Zamítnout", style=discord.ButtonStyle.danger, custom_id="zatykac_zamitnout", emoji="🔴")
    async def btn_zamitnout(self, interaction: discord.Interaction, button: discord.ui.Button):
        if ROLE_SOUDCE_ID not in [role.id for role in interaction.user.roles]:
            return await interaction.response.send_message("❌ Pouze Soudce!", ephemeral=True)

        embed = interaction.message.embeds[0]
        
        # Přečtení ID archivu pro úpravu
        footer_text = embed.footer.text
        archiv_msg_id = int(footer_text.split(" | ")[1].replace("Archiv ID: ", "").strip())

        embed.color = discord.Color.red()
        embed.title = "📄 ŽÁDOST O ZATYKAČ ZAMÍTNUTA"
        embed.description += f"\n\n**👨‍⚖️ Rozhodnutí soudu:** Zamítnuto soudcem {interaction.user.mention}"

        # 1. Okamžité SMAZÁNÍ ze stolu soudu
        await interaction.message.delete()

        # 2. Úprava zprávy v žádost-o-zatykač (Archiv)
        kanal_archiv = interaction.client.get_channel(KANAL_ZADOST_ARCHIV_ID)
        if kanal_archiv:
            try:
                msg_archiv = await kanal_archiv.fetch_message(archiv_msg_id)
                await msg_archiv.edit(embed=embed)
            except discord.NotFound: pass
        
        await interaction.response.send_message("✅ Žádost byla zamítnuta a zaznamenána v archivu.", ephemeral=True)

# --- FORMULÁŘ PRO POLICISTU ---
class ZatykacModal(discord.ui.Modal, title='Příprava Zatykače - Policie'):
    cislo_prukazu = discord.ui.TextInput(label='Číslo průkazu (ID hráče)', style=discord.TextStyle.short, required=True)
    obvineni = discord.ui.TextInput(label='Trestné činy (Obvinění)', style=discord.TextStyle.paragraph, max_length=1000, required=True)
    adresa = discord.ui.TextInput(label='Obvyklá známá adresa', style=discord.TextStyle.short, required=True)
    fyzicky_popis = discord.ui.TextInput(label='Fyzický popis', style=discord.TextStyle.paragraph, required=True)
    dalsi_info = discord.ui.TextInput(label='Další informace', style=discord.TextStyle.paragraph, required=False)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        db_hraci = nacti_hrace()
        hrac_id = self.cislo_prukazu.value.strip()
        jmeno_hrace = db_hraci.get(hrac_id, {}).get("jmeno", "Neznámá identita")
        
        vozidla_seznam = db_hraci.get(hrac_id, {}).get("vozidla", [])
        vozidla_text = ", ".join([str(v) for v in vozidla_seznam]) if vozidla_seznam else "Žádná registrovaná vozidla"
        cislo_zatykace = random.randint(10000, 99999)

        zatykac_text = f"""**VRCHNÍ SOUD STÁTU KALIFORNIE**
Okres Los Angeles\n\n**ZATYKAČ**\nBěžný zatykač\nTrestní zákoník §§ 813-5\n\n**LID STÁTU KALIFORNIE**
Všem kalifornským strážcům zákona
Zatykač č. **FW-{cislo_zatykace}**\n\n**Jméno obžalovaného:** {jmeno_hrace}
\n**Příkaz:** Vzhledem k tomu, že k tomuto soudu byla dnešního dne podána stížnost pod přísahou, která viní výše uvedeného obžalovaného z níže uvedeného trestného činu (trestných činů), nařizuje se vám tímto, abyste výše uvedeného obžalovaného neprodleně zatkli a předvedli jej přede mne, nebo v případě mé nepřítomnosti či neschopnosti jednat, před nejbližšího a nejdostupnějšího smírčího soudce v tomto okrese.
\n**Obvinění z trestných činů:** {self.obvineni.value}
\n**Povolení k výkonu v noci:** [ČEKÁ NA ROZHODNUTÍ SOUDCE - NOC]
**Kauce:** [ČEKÁ NA ROZHODNUTÍ SOUDCE - KAUCE]
\n**Datum a čas vydání zatykače:** [ČEKÁ NA ČAS VYDÁNÍ]
**Soudce vrchního soudu:** *[ČEKÁ NA PODPIS SOUDCE]*
\n---\n♦ **Informace o zatýkaném** ♦\n*Pouze pro účely identifikace*\n
**Jméno:** {jmeno_hrace}
**Známý také jako (AKA's):** -
**Obvyklá známá adresa:** {self.adresa.value}
**Fyzický popis:** {self.fyzicky_popis.value}
**Vozidla spojená se zatýkaným:** {vozidla_text}
**Další informace:** {self.dalsi_info.value if self.dalsi_info.value else "Žádné"}"""

        embed = discord.Embed(title="⏳ ŽÁDOST O ZATYKAČ (Čeká na soud)", color=discord.Color.orange(), description=zatykac_text)

        # 1. Pošle žádost rovnou do archivu (žádost-o-zatykač), aby tam vznikla trvalá zpráva
        kanal_archiv = self.bot.get_channel(KANAL_ZADOST_ARCHIV_ID)
        msg_archiv = None
        if kanal_archiv:
            msg_archiv = await kanal_archiv.send(embed=embed)
        
        # Obohacení Embedu o Footer, který si nese ID hráče i ID zprávy v archivu
        if msg_archiv:
            embed.set_footer(text=f"Číslo průkazu cíle: {hrac_id} | Archiv ID: {msg_archiv.id}")
            await msg_archiv.edit(embed=embed)

        # 2. Pošle žádost soudci na stůl (s tlačítky)
        kanal_soud = self.bot.get_channel(KANAL_SOUD_ID)
        if kanal_soud:
            await kanal_soud.send(embed=embed, view=ZatykacView())
            await interaction.response.send_message("✅ Žádost odeslána k soudu.", ephemeral=True)

# --- HLAVNÍ TŘÍDA ---
class ZatykacCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.kontrola_expirace.start() 

    @app_commands.command(name="zatykac_uzavrit", description="Uzavře aktivní zatykač na občana podle čísla průkazu.")
    @app_commands.describe(cislo_prukazu="ID hráče, jehož zatykač chceš uzavřít")
    async def zatykac_uzavrit_command(self, interaction: discord.Interaction, cislo_prukazu: str):
        if ROLE_POLICIE_ID not in [role.id for role in interaction.user.roles]:
            return await interaction.response.send_message("❌ Pouze Policie!", ephemeral=True)

        zatykac = kolekce_zatykace.find_one({"hrac_id": cislo_prukazu.strip(), "status": "aktivni"})
        if not zatykac:
            return await interaction.response.send_message(f"❌ Nenašel jsem žádný aktivní zatykač pro průkaz {cislo_prukazu}.", ephemeral=True)

        await self.proved_uzavreni(zatykac, f"Zatykač vykonal/uzavřel: {interaction.user.mention}")
        await interaction.response.send_message(f"✅ Zatykač byl úspěšně uzavřen a stažen z aktivních databází.", ephemeral=True)

    # --- FUNKCE PRO ÚPRAVU A MAZÁNÍ (Zavírací proces) ---
    async def proved_uzavreni(self, zatykac_data, duvod_text):
        # 1. Aktualizace zprávy v kanálu žádost-o-zatykač (Archivu) -> Zešedne
        kanal_archiv = self.bot.get_channel(KANAL_ZADOST_ARCHIV_ID)
        if kanal_archiv and zatykac_data.get("msg_archiv_id"):
            try:
                msg_archiv = await kanal_archiv.fetch_message(zatykac_data["msg_archiv_id"])
                embed = msg_archiv.embeds[0]
                embed.color = discord.Color.dark_grey()
                embed.title = "🔒 ZATYKAČ UZAVŘEN / VYKONÁN"
                embed.add_field(name="🚓 Uzavření případu", value=duvod_text, inline=False)
                await msg_archiv.edit(embed=embed)
            except discord.NotFound: pass

        # 2. ÚPLNÉ SMAZÁNÍ zprávy z přehledu aktivních zatykačů
        kanal_aktivni = self.bot.get_channel(KANAL_AKTIVNI_ZATYKACE_ID)
        if kanal_aktivni and zatykac_data.get("msg_aktivni_id"):
            try:
                msg_aktivni = await kanal_aktivni.fetch_message(zatykac_data["msg_aktivni_id"])
                await msg_aktivni.delete()
            except discord.NotFound: pass

        # 3. ÚPLNÉ SMAZÁNÍ zprávy z hráčova fóra
        if zatykac_data.get("vlakno_id") and zatykac_data.get("msg_forum_id"):
            vlakno = self.bot.get_channel(zatykac_data["vlakno_id"])
            if vlakno:
                try:
                    msg_forum = await vlakno.fetch_message(zatykac_data["msg_forum_id"])
                    await msg_forum.delete()
                except discord.NotFound: pass

        # Změna statusu v databázi
        kolekce_zatykace.update_one({"_id": zatykac_data["_id"]}, {"$set": {"status": "uzavren"}})

    # --- STOPKY: KONTROLA 48 HODIN ---
    @tasks.loop(hours=1)
    async def kontrola_expirace(self):
        limit = datetime.now() - timedelta(hours=48)
        expirovane_zatykace = kolekce_zatykace.find({"status": "aktivni", "vydano": {"$lt": limit}})
        for z in expirovane_zatykace:
            await self.proved_uzavreni(z, "Vypršela lhůta 48 hodin pro výkon zatykače. Status: Uzavřeno.")

    @kontrola_expirace.before_loop
    async def pred_spustenim(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="zadost_zatykac", description="Vytvoří plně formátovanou žádost o zatykač na soud.")
    async def zadost_zatykac_command(self, interaction: discord.Interaction):
        if ROLE_POLICIE_ID not in [role.id for role in interaction.user.roles]:
            return await interaction.response.send_message("❌ Pouze Policie!", ephemeral=True)
        await interaction.response.send_modal(ZatykacModal(self.bot))

async def setup(bot):
    await bot.add_cog(ZatykacCog(bot))
