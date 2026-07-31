import discord
from discord.ext import commands
from discord import app_commands
import pymongo
import asyncio
import random

# ==========================================
# NASTAVENÍ OPRÁVNĚNÍ A KANÁLŮ
# ==========================================
# DOPLŇ ID MDT SERVERU A KANÁLU MÍSTO NUL:
ID_MDT_SERVERU = 1453744303691137045  # <--- ZDE DOPLŇ ID VAŠEHO MDT SERVERU
ID_MDT_KANALU = 1532746320543088853 # <--- ZDE DOPLŇ ID KANÁLU NA MDT SERVERU (např. #sw-zaznamy)

# Seznam všech povolených serverů (Hlavní město + MDT)
POVOLENE_SERVERY_ID = [1532110413028659452, ID_MDT_SERVERU] 

# Seznam všech povolených kanálů (Hlavní město + MDT kanál)
POVOLENE_KANALY_ID = [
    1532455920141996122, 
    1532455929759399956, 
    1532455949518901249, 
    1532455958838513888, 
    ID_MDT_KANALU
]

# ==========================================
# DATABÁZE
# ==========================================
MONGO_URI = "mongodb+srv://kubiqcz1:Aluska78@calicore.kmnmj4h.mongodb.net/?appName=CaliCore"
klient = pymongo.MongoClient(MONGO_URI)
db_cloud = klient["calicore_databaze"]
kolekce_hraci = db_cloud["hraci"]
kolekce_sklady = db_cloud["sklady"] 
db_sw = db_cloud["search_warrants_log"] # Kolekce pro razie
kolekce_config = db_cloud["config"]     # Kolekce pro živou tabulku

LOKACE_HLEDANI = ["Postal 407", "Postal 802", "Postal 903", "Postal 509", "Postal 302", "Postal 408"]
SOUCASTKY = ["Hlaveň", "Pažba", "Závěr", "Spoušťový mechanismus"]

# --- TŘÍDA PRO TLAČÍTKO HLEDÁNÍ ---
class HledaniView(discord.ui.View):
    def __init__(self, hrac_id):
        super().__init__(timeout=600)
        self.hrac_id = hrac_id

    @discord.ui.button(label="📍 Jsem na místě", style=discord.ButtonStyle.success)
    async def btn_na_miste(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.hrac_id:
            return await interaction.response.send_message("Toto není tvá lokace k prohledání!", ephemeral=True)

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

        await interaction.response.send_message("Začínáš prohledávat okolí... Bude to trvat 60 sekund. Zůstaň na místě!", ephemeral=True)
        
        await asyncio.sleep(60)

        nalezeno = random.choice(SOUCASTKY)

        hrac = kolekce_hraci.find_one({"_id": self.hrac_id})
        if not hrac:
            kolekce_hraci.insert_one({"_id": self.hrac_id, "nelegal_inventar": [nalezeno]})
        else:
            kolekce_hraci.update_one({"_id": self.hrac_id}, {"$push": {"nelegal_inventar": nalezeno}})

        embed = discord.Embed(title="🕵️ Nález úspěšný", color=discord.Color.dark_grey())
        embed.description = f"Po důkladném prohledání jsi našel: **{nalezeno}**!\n*Předmět byl potichu přidán do tvého nelegálního inventáře.*"
        
        await interaction.followup.send(embed=embed, ephemeral=True)


class NelegalSkladCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- KONTROLNÍ FUNKCE PRO SERVER A KANÁLY ---
    def ma_povoleni(self, interaction: discord.Interaction):
        # Aby nedocházelo k chybám, pokud MDT server/kanál ještě není nastaven (je tam 0)
        if interaction.guild_id not in POVOLENE_SERVERY_ID:
            return False
        if interaction.channel_id not in POVOLENE_KANALY_ID:
            return False
        return True

    # --- 1. HLEDÁNÍ SOUČÁSTEK ---
    @app_commands.command(name="hledat_parts", description="Získáš tip na lokaci, kde by se mohly nacházet součástky zbraní.")
    async def hledat_parts(self, interaction: discord.Interaction):
        if not self.ma_povoleni(interaction):
            return await interaction.response.send_message("❌ Tento příkaz zde nelze použít.", ephemeral=True)

        lokace = random.choice(LOKACE_HLEDANI)
        
        embed = discord.Embed(title="📱 Zašifrovaná zpráva", color=discord.Color.dark_theme())
        embed.description = f"Dostal jsi tip. Běž na lokaci: **{lokace}** a rozhlédni se tam.\n\n*Až dorazíš na místo, klikni na tlačítko níže.*"
        
        await interaction.response.send_message(embed=embed, view=HledaniView(str(interaction.user.id)), ephemeral=True)

    # --- 2. OSOBNÍ NELEGÁLNÍ INVENTÁŘ ---
    @app_commands.command(name="nelegal_inventar", description="Zobrazí tvůj skrytý nelegální inventář.")
    async def nelegal_inventar(self, interaction: discord.Interaction):
        if not self.ma_povoleni(interaction):
            return await interaction.response.send_message("❌ Tento příkaz zde nelze použít.", ephemeral=True)

        hrac = kolekce_hraci.find_one({"_id": str(interaction.user.id)})
        inventar = hrac.get("nelegal_inventar", []) if hrac else []

        embed = discord.Embed(title="🎒 Kapsy (Nelegální předměty)", color=discord.Color.dark_grey())
        
        if not inventar:
            embed.description = "U sebe momentálně nemáš nic nelegálního."
        else:
            pocty = {item: inventar.count(item) for item in set(inventar)}
            vypis = "\n".join([f"• {item} (x{pocet})" for item, pocet in pocty.items()])
            embed.description = vypis

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # --- 3. ZALOŽENÍ SKLADU ---
    @app_commands.command(name="zalozit_sklad", description="[Boss] Založí nový utajený sklad na konkrétní číslo budovy.")
    @app_commands.describe(cislo_domu="Číslo budovy (např. 14)", heslo="Heslo pro přístup do skladu")
    async def zalozit_sklad(self, interaction: discord.Interaction, cislo_domu: str, heslo: str):
        if not self.ma_povoleni(interaction):
            return await interaction.response.send_message("❌ Tento příkaz zde nelze použít.", ephemeral=True)
        
        # KONTROLA ROLE BOSS
        ma_roli_boss = any(role.name.lower() == "boss" for role in interaction.user.roles)
        if not ma_roli_boss:
            return await interaction.response.send_message("❌ Přístup odepřen: Tento příkaz může použít pouze Boss frakce!", ephemeral=True)

        existuje = kolekce_sklady.find_one({"_id": cislo_domu.strip()})
        if existuje:
            return await interaction.response.send_message(f"Sklad v budově č. {cislo_domu} už existuje!", ephemeral=True)

        novy_sklad = {
            "_id": cislo_domu.strip(),
            "heslo": heslo,
            "soucastky": [],
            "hotove_zbrane": [],
            "drogy": []
        }
        kolekce_sklady.insert_one(novy_sklad)
        
        await interaction.response.send_message(f"🏠 Úkryt v budově **č. {cislo_domu}** byl úspěšně zajištěn. Heslo nastaveno.", ephemeral=True)
        
        # AKTUALIZACE TABULKY PO ZALOŽENÍ
        await self.aktualizovat_tabulku()

    # --- 4. PŘÍSTUP DO SKLADU ---
    @app_commands.command(name="nelegal_sklad", description="Nahlédneš do tajného skladu budovy, pokud znáš heslo.")
    @app_commands.describe(cislo_domu="Číslo budovy", heslo="Zadej přístupové heslo")
    async def otevrit_sklad(self, interaction: discord.Interaction, cislo_domu: str, heslo: str):
        if not self.ma_povoleni(interaction):
            return await interaction.response.send_message("❌ Tento příkaz zde nelze použít.", ephemeral=True)

        sklad = kolekce_sklady.find_one({"_id": cislo_domu.strip()})
        
        if not sklad or sklad.get("heslo") != heslo:
            return await interaction.response.send_message("❌ Přístup odepřen.", ephemeral=True)

        soucastky = sklad.get("soucastky", [])
        zbrane = sklad.get("hotove_zbrane", [])

        embed = discord.Embed(title=f"📦 Tajný sklad (Budova č. {cislo_domu})", color=discord.Color.dark_grey())
        
        if not soucastky:
            embed.add_field(name="⚙️ Součástky zbraní", value="Žádné součástky", inline=False)
        else:
            pocty_s = {item: soucastky.count(item) for item in set(soucastky)}
            vypis_s = "\n".join([f"• {item} (x{pocet})" for item, pocet in pocty_s.items()])
            embed.add_field(name="⚙️ Součástky zbraní", value=vypis_s, inline=False)

        if not zbrane:
            embed.add_field(name="🔫 Hotové zbraně", value="Žádné zbraně", inline=False)
        else:
            pocty_z = {item: zbrane.count(item) for item in set(zbrane)}
            vypis_z = "\n".join([f"• {item} (x{pocet})" for item, pocet in pocty_z.items()])
            embed.add_field(name="🔫 Hotové zbraně", value=vypis_z, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # --- 5. VÝROBA ZBRANÍ ZE SKLADU ---
    @app_commands.command(name="vyrobit_zbran", description="Složí nelegální zbraň ze součástek uložených ve skladu.")
    @app_commands.describe(
        zbran="Vyber zbraň k výrobě", 
        cislo_domu="Číslo budovy skladu", 
        heslo="Přístupové heslo do skladu"
    )
    @app_commands.choices(zbran=[
        app_commands.Choice(name="AK-47", value="AK-47"),
        app_commands.Choice(name="Remington MSR", value="Remington MSR"),
        app_commands.Choice(name="TEC-9", value="TEC-9"),
        app_commands.Choice(name="Desert Eagle", value="Desert Eagle"),
        app_commands.Choice(name="Kriss Vector", value="kriss vector"),
        app_commands.Choice(name="Skorpion", value="skorpion")
    ])
    async def vyrobit_zbran(self, interaction: discord.Interaction, zbran: app_commands.Choice[str], cislo_domu: str, heslo: str):
        if not self.ma_povoleni(interaction):
            return await interaction.response.send_message("❌ Tento příkaz zde nelze použít.", ephemeral=True)

        sklad = kolekce_sklady.find_one({"_id": cislo_domu.strip()})
        if not sklad or sklad.get("heslo") != heslo:
            return await interaction.response.send_message("❌ Přístup odepřen.", ephemeral=True)

        soucastky = sklad.get("soucastky", [])
        
        potrebne_dily = ["Hlaveň", "Pažba", "Závěr", "Spoušťový mechanismus"]
        
        chceni_chybi = []
        temp_soucastky = list(soucastky)
        for dil in potrebne_dily:
            if dil in temp_soucastky:
                temp_soucastky.remove(dil)
            else:
                chceni_chybi.append(dil)

        if chceni_chybi:
            zchybi_str = ", ".join(chceni_chybi)
            return await interaction.response.send_message(f"❌ Ve skladu chybí tyto součástky pro výrobu: **{zchybi_str}**.", ephemeral=True)

        for dil in potrebne_dily:
            soucastky.remove(dil)

        hotove_zbrane = sklad.get("hotove_zbrane", [])
        hotove_zbrane.append(zbran.value)

        kolekce_sklady.update_one(
            {"_id": cislo_domu.strip()},
            {"$set": {"soucastky": soucastky, "hotove_zbrane": hotove_zbrane}}
        )

        embed = discord.Embed(title="🛠️ Výroba úspěšná", color=discord.Color.green())
        embed.description = f"Ve skladu č. **{cislo_domu}** byla úspěšně sestavena zbraň: **{zbran.name}**!"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # --- 6. POLICEJNÍ RAZIE NA SKLAD (PROVEDENÍ SEARCH WARRANT) ---
    @app_commands.command(name="sw_vykonat", description="[Policie] Provede razii na sklad pomocí aktivního Search Warrantu.")
    @app_commands.describe(
        sw_cislo="Číslo SW příkazu (např. 12345)", 
        cislo_domu="Číslo budovy, kde proběhne razie"
    )
    async def sw_vykonat(self, interaction: discord.Interaction, sw_cislo: str, cislo_domu: str):
        if not self.ma_povoleni(interaction):
            return await interaction.response.send_message("❌ Tento příkaz zde nelze použít.", ephemeral=True)

        sw = db_sw.find_one({"sw_cislo": sw_cislo.strip(), "status": "aktivni"})
        
        if not sw:
            return await interaction.response.send_message(f"❌ Příkaz SW-2026-{sw_cislo} neexistuje nebo již není aktivní.", ephemeral=True)

        sklad = kolekce_sklady.find_one({"_id": cislo_domu.strip()})
        if not sklad:
            return await interaction.response.send_message(f"❌ Budova č. {cislo_domu} neobsahuje žádný registrovaný tajný sklad.", ephemeral=True)

        await interaction.response.send_message(
            f"🚨 **POLICEJNÍ RAZIE ZAHÁJENA!**\n"
            f"Jednotky vyrazily dveře budovy č. **{cislo_domu}** na základě příkazu `SW-2026-{sw_cislo}`.\n"
            f"⏳ *Prohledávání objektu a zajišťování důkazů potrvá 120 sekund...*",
            ephemeral=False
        )

        await asyncio.sleep(120)

        soucastky = sklad.get("soucastky", [])
        zbrane = sklad.get("hotove_zbrane", [])

        kolekce_sklady.update_one(
            {"_id": cislo_domu.strip()},
            {"$set": {"soucastky": [], "hotove_zbrane": [], "drogy": []}}
        )

        db_sw.update_one({"_id": sw["_id"]}, {"$set": {"status": "uzavren"}})

        embed = discord.Embed(title=f"🛑 RAZIE UKONČENA — Budova č. {cislo_domu}", color=discord.Color.red())
        
        vypis_s = "\n".join([f"• {item} (x{soucastky.count(item)})" for item in set(soucastky)]) if soucastky else "Žádné součástky"
        vypis_z = "\n".join([f"• {item} (x{zbrane.count(item)})" for item in set(zbrane)]) if zbrane else "Žádné zbraně"

        embed.add_field(name="⚙️ Zabavené součástky", value=vypis_s, inline=False)
        embed.add_field(name="🔫 Zabavené hotové zbraně", value=vypis_z, inline=False)
        embed.set_footer(text=f"Akci vedl: {interaction.user.display_name} | SW-2026-{sw_cislo} uzavřen")

        await interaction.followup.send(embed=embed)
        
        # AKTUALIZACE TABULKY PO VYČIŠTĚNÍ SKLADU POLICIÍ
        await self.aktualizovat_tabulku()

    # --- 7. AUTOMATICKÁ AKTUALIZACE TABULKY ---
    async def aktualizovat_tabulku(self):
        konfig = kolekce_config.find_one({"_id": "tabulka_budov"})
        if not konfig:
            return 

        kanal = self.bot.get_channel(konfig["channel_id"])
        if not kanal:
            return

        try:
            zprava = await kanal.fetch_message(konfig["message_id"])
        except discord.NotFound:
            return

        sklady = kolekce_sklady.find({}, {"_id": 1})
        zabrane_seznam = [sklad["_id"] for sklad in sklady]
        
        try:
            zabrane_seznam.sort(key=int)
        except ValueError:
            zabrane_seznam.sort()

        embed = discord.Embed(title="🏢 Černý trh: Seznam budov", color=discord.Color.dark_red())
        
        if not zabrane_seznam:
            embed.description = "Všechny budovy ve městě jsou momentálně volné."
        else:
            vypis = "\n".join(f"🏠 Budova č. **{cislo}** - 🔴 Zabráno" for cislo in zabrane_seznam)
            embed.description = f"Seznam aktuálně obsazených budov:\n\n{vypis}"
        
        await zprava.edit(embed=embed)

    # --- 8. PŘÍKAZ PRO VYTVOŘENÍ TABULKY (Zadej jen jednou do kanálu) ---
    @app_commands.command(name="setup_tabulka_budov", description="Vytvoří v tomto kanálu živou tabulku obsazených budov.")
    async def setup_tabulka_budov(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Pouze pro adminy.", ephemeral=True)

        embed = discord.Embed(title="🏢 Seznam Zabraných Budov", description="Načítám data...", color=discord.Color.dark_red())
        await interaction.response.send_message("Vytvářím tabulku...", ephemeral=True)
        
        zprava = await interaction.channel.send(embed=embed)

        kolekce_config.update_one(
            {"_id": "tabulka_budov"},
            {"$set": {"channel_id": interaction.channel.id, "message_id": zprava.id}},
            upsert=True
        )

        await self.aktualizovat_tabulku()


async def setup(bot):
    # Zde je změněn název třídy, aby se to nekřížilo s tvojí anonymní DarkwebCog
    await bot.add_cog(NelegalSkladCog(bot))
