import discord
from discord.ext import commands
from discord import app_commands
import pymongo
import datetime

# ==========================================
# NASTAVENÍ ID (DOPLŇ VAŠE ÚDAJE)
# ==========================================
ID_MDT_SERVERU = 1453744303691137045
POVOLENE_SERVERY_ID = [1532110413028659452, ID_MDT_SERVERU] 

# Zde doplň ID role "On-Duty", kterou bot policistům přiřadí na MDT serveru
ID_ROLE_ONDUTY = 1533451480541958255 # <--- DOPLŇ ID ROLE

# ==========================================
# DATABÁZE A SEZNAMY
# ==========================================
MONGO_URI = "mongodb+srv://kubiqcz1:Aluska78@calicore.kmnmj4h.mongodb.net/?appName=CaliCore"
klient = pymongo.MongoClient(MONGO_URI)
db_cloud = klient["calicore_databaze"]

kolekce_sluzba = db_cloud["aktivni_sluzba"]
kolekce_config = db_cloud["config"]

HODNOSTI_LAPD = [
    "✰✰✰✰ Chief of Police ✰✰✰✰", "✰✰✰ Assistent Chief ✰✰✰", "✰✰ Deputy Chief ✰✰", 
    "✰ Commander ✰", "Captain", "Lieutenant", "Sergeant II", "Sergeant I", 
    "Detective III", "Detective II", "Detective I", "Police Officer III+I", 
    "Police Officer III", "Police Officer II", "Police Officer I"
]

HODNOSTI_LASD = [
    "✰✰✰✰✰ Sheriff ✰✰✰✰✰", "✰✰✰✰ UnderSheriff ✰✰✰✰", "✰✰✰ Assistant Sheriff ✰✰✰", 
    "✰✰ Division Chief ✰✰", "✰ Area Commander ✰", "Captain", "Lieutenant", "Sergeant", 
    "Deputy Sheriff Master", "Deputy Sheriff Bonus II.", "Deputy Sheriff Bonus I.", "Deputy Sheriff"
]

SUPERVIZORI = [
    "✰✰✰✰ Chief of Police ✰✰✰✰", "✰✰✰ Assistent Chief ✰✰✰", "✰✰ Deputy Chief ✰✰", "✰ Commander ✰", 
    "Captain", "Lieutenant", "Sergeant II", "Sergeant I",
    "✰✰✰✰✰ Sheriff ✰✰✰✰✰", "✰✰✰✰ UnderSheriff ✰✰✰✰", "✰✰✰ Assistant Sheriff ✰✰✰", "✰✰ Division Chief ✰✰", 
    "✰ Area Commander ✰", "Sergeant"
]

class SluzbaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def ma_povoleni(self, interaction: discord.Interaction):
        return interaction.guild_id in POVOLENE_SERVERY_ID

    # --- NAŠEPTÁVAČ HODNOSTÍ ---
    async def hodnost_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        sbor = interaction.namespace.sbor
        if sbor == "LAPD":
            dostupne = HODNOSTI_LAPD
        elif sbor == "LASD":
            dostupne = HODNOSTI_LASD
        else:
            dostupne = HODNOSTI_LAPD + HODNOSTI_LASD
            
        return [app_commands.Choice(name=h, value=h) for h in dostupne if current.lower() in h.lower()][:25]

    # --- 1. NÁSTUP DO SLUŽBY ---
    @app_commands.command(name="onduty", description="[Policie] Nastoupíš do aktivní služby.")
    @app_commands.describe(
        sbor="Vyber svůj sbor", 
        hodnost="Začni psát a vyber svou hodnost", 
        prijmeni="Tvé příjmení v RP", 
        odznak="Tvé číslo odznaku (např. 105)"
    )
    @app_commands.choices(sbor=[
        app_commands.Choice(name="LAPD", value="LAPD"),
        app_commands.Choice(name="LASD", value="LASD")
    ])
    @app_commands.autocomplete(hodnost=hodnost_autocomplete)
    async def onduty(self, interaction: discord.Interaction, sbor: app_commands.Choice[str], hodnost: str, prijmeni: str, odznak: str):
        if not self.ma_povoleni(interaction):
            return await interaction.response.send_message("❌ Tento příkaz zde nelze použít.", ephemeral=True)

        hrac_id = str(interaction.user.id)
        existuje = kolekce_sluzba.find_one({"_id": hrac_id})

        if existuje:
            return await interaction.response.send_message("❌ Už jsi vedený v aktivní službě! Pokud chceš údaje změnit, dej nejdřív /offduty.", ephemeral=True)

        kolekce_sluzba.insert_one({
            "_id": hrac_id,
            "sbor": sbor.value,
            "hodnost": hodnost,
            "prijmeni": prijmeni,
            "odznak": odznak,
            "nastup": datetime.datetime.now().strftime("%H:%M")
        })

        if interaction.guild:
            role = interaction.guild.get_role(ID_ROLE_ONDUTY)
            if role:
                try:
                    await interaction.user.add_roles(role)
                except discord.Forbidden:
                    pass

        await interaction.response.send_message(f"✅ Úspěšně jsi nastoupil do služby jako **{sbor.value} | {hodnost} {prijmeni} [{odznak}]**.", ephemeral=True)
        await self.aktualizovat_panely()

    # --- 2. ODCHOD ZE SLUŽBY ---
    @app_commands.command(name="offduty", description="[Policie] Ukončíš aktivní službu.")
    async def offduty(self, interaction: discord.Interaction):
        if not self.ma_povoleni(interaction):
            return await interaction.response.send_message("❌ Tento příkaz zde nelze použít.", ephemeral=True)

        hrac_id = str(interaction.user.id)
        zaznam = kolekce_sluzba.find_one_and_delete({"_id": hrac_id})

        if not zaznam:
            return await interaction.response.send_message("❌ Nejsi vedený v aktivní službě.", ephemeral=True)

        if interaction.guild:
            role = interaction.guild.get_role(ID_ROLE_ONDUTY)
            if role:
                try:
                    await interaction.user.remove_roles(role)
                except discord.Forbidden:
                    pass

        await interaction.response.send_message("💤 Úspěšně jsi ukončil službu a odevzdal výstroj.", ephemeral=True)
        await self.aktualizovat_panely()

    # --- 3. AKTUALIZACE OBOU PANELŮ ---
    async def aktualizovat_panely(self):
        sluzici = list(kolekce_sluzba.find())
        
        supervizori_seznam = []
        jednotky_seznam = []

        for s in sluzici:
            text_zaznamu = f"• **{s['sbor']}** | {s['hodnost']} {s['prijmeni']} [{s['odznak']}] *(Od {s['nastup']})*"
            
            if s['hodnost'] in SUPERVIZORI:
                supervizori_seznam.append(text_zaznamu)
            else:
                jednotky_seznam.append(text_zaznamu)

        # --- AKTUALIZACE MDT PANELU (Detailní rozpis) ---
        konfig_mdt = kolekce_config.find_one({"_id": "panel_sluzba_mdt"})
        if konfig_mdt:
            kanal = self.bot.get_channel(konfig_mdt["channel_id"])
            if kanal:
                try:
                    zprava = await kanal.fetch_message(konfig_mdt["message_id"])
                    embed_mdt = discord.Embed(title="🚓 Policejní databáze: Aktivní služba", color=discord.Color.blue())
                    
                    text_sup = "\n".join(supervizori_seznam) if supervizori_seznam else "Žádný supervizor není ve službě."
                    embed_mdt.add_field(name="👑 Supervizoři ve službě", value=text_sup, inline=False)
                    
                    text_jednotky = "\n".join(jednotky_seznam) if jednotky_seznam else "Žádné další jednotky nejsou ve službě."
                    embed_mdt.add_field(name="🚔 Dostupné jednotky", value=text_jednotky, inline=False)
                    
                    embed_mdt.set_footer(text=f"Celkem ve službě: {len(sluzici)} policistů")
                    await zprava.edit(embed=embed_mdt)
                except discord.NotFound:
                    pass

        # --- AKTUALIZACE HLAVNÍHO PANELU (Sloučený celkový počet) ---
        konfig_hlavni = kolekce_config.find_one({"_id": "panel_sluzba_hlavni"})
        if konfig_hlavni:
            kanal_hl = self.bot.get_channel(konfig_hlavni["channel_id"])
            if kanal_hl:
                try:
                    zprava_hl = await kanal_hl.fetch_message(konfig_hlavni["message_id"])
                    embed_hl = discord.Embed(
                        title="🚨 Informace o státních složkách", 
                        description="Aktuální přehled dostupnosti policie ve městě.", 
                        color=discord.Color.dark_blue()
                    )
                    
                    celkovy_pocet = len(sluzici)
                    embed_hl.add_field(
                        name="🚔 Počet jednotek ve službě", 
                        value=f"**{celkovy_pocet}** {'aktivní jednotka' if celkovy_pocet == 1 else ('aktivní jednotky' if 2 <= celkovy_pocet <= 4 else 'aktivních jednotek')}", 
                        inline=False
                    )
                    
                    await zprava_hl.edit(embed=embed_hl)
                except discord.NotFound:
                    pass

    # --- 4. SETUP PŘÍKAZY PRO ADMINY ---
    @app_commands.command(name="setup_onduty_mdt", description="[Admin] Vytvoří detailní MDT tabulku aktivních policistů.")
    async def setup_mdt(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Nemáš oprávnění.", ephemeral=True)

        embed = discord.Embed(title="🚓 Policejní databáze: Aktivní služba", description="Načítám systém...", color=discord.Color.blue())
        await interaction.response.send_message("Vytvářím MDT tabulku...", ephemeral=True)
        zprava = await interaction.channel.send(embed=embed)

        kolekce_config.update_one(
            {"_id": "panel_sluzba_mdt"},
            {"$set": {"channel_id": interaction.channel.id, "message_id": zprava.id}},
            upsert=True
        )
        await self.aktualizovat_panely()

    @app_commands.command(name="setup_onduty_main", description="[Admin] Vytvoří veřejnou tabulku s celkovým počtem jednotek.")
    async def setup_main(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Nemáš oprávnění.", ephemeral=True)

        embed = discord.Embed(title="🚨 Informace o státních složkách", description="Načítám systém...", color=discord.Color.dark_blue())
        await interaction.response.send_message("Vytvářím hlavní tabulku...", ephemeral=True)
        zprava = await interaction.channel.send(embed=embed)

        kolekce_config.update_one(
            {"_id": "panel_sluzba_hlavni"},
            {"$set": {"channel_id": interaction.channel.id, "message_id": zprava.id}},
            upsert=True
        )
        await self.aktualizovat_panely()

async def setup(bot):
    await bot.add_cog(SluzbaCog(bot))
