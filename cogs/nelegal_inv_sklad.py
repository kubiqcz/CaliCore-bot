import discord
from discord.ext import commands
from discord import app_commands
import pymongo
import asyncio
import random

# ==========================================
# NASTAVENÍ OPRÁVNĚNÍ A KANÁLŮ
# ==========================================
POVOLENY_SERVER_ID = 1532110413028659452  # <--- ZDE DOPLŇ ID TVÉHO SERVERU (GUILD ID)
POVOLENE_KANALY_ID = [1532455920141996122, 1532455929759399956, 1532455949518901249, 1532455958838513888] # <--- ZDE DOPLŇ ID 4 KANÁLŮ

# ==========================================
# DATABÁZE
# ==========================================
MONGO_URI = "mongodb+srv://kubiqcz1:Aluska78@calicore.kmnmj4h.mongodb.net/?appName=CaliCore"
klient = pymongo.MongoClient(MONGO_URI)
db_cloud = klient["calicore_databaze"]
kolekce_hraci = db_cloud["hraci"]
kolekce_sklady = db_cloud["sklady"] # Nová kolekce pro domovní sklady

LOKACE_HLEDANI = ["Postal 407", "Postal 802", "Postal 903", "Postal 509", "Postal 302", "Postal 408"]
SOUCASTKY = ["Hlaveň", "Pažba", "Závěr", "Spoušťový mechanismus"]

# --- TŘÍDA PRO TLAČÍTKO HLEDÁNÍ ---
class HledaniView(discord.ui.View):
    def __init__(self, hrac_id):
        super().__init__(timeout=600) # Má 10 minut na to dojet na místo
        self.hrac_id = hrac_id

    @discord.ui.button(label="📍 Jsem na místě", style=discord.ButtonStyle.success)
    async def btn_na_miste(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.hrac_id:
            return await interaction.response.send_message("Toto není tvá lokace k prohledání!", ephemeral=True)

        # Deaktivace tlačítka, aby na to neklikal víckrát
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

        await interaction.response.send_message("Začínáš prohledávat okolí... Bude to trvat 60 sekund. Zůstaň na místě!", ephemeral=True)
        
        # RP Odpočet 60 sekund
        await asyncio.sleep(60)

        # Náhodný drop součástky
        nalezeno = random.choice(SOUCASTKY)

        # Uložení do nelegal inventáře hráče
        hrac = kolekce_hraci.find_one({"_id": self.hrac_id})
        if not hrac:
            kolekce_hraci.insert_one({"_id": self.hrac_id, "nelegal_inventar": [nalezeno]})
        else:
            kolekce_hraci.update_one({"_id": self.hrac_id}, {"$push": {"nelegal_inventar": nalezeno}})

        embed = discord.Embed(title="🕵️ Nález úspěšný", color=discord.Color.dark_grey())
        embed.description = f"Po důkladném prohledání jsi našel: **{nalezeno}**!\n*Předmět byl potichu přidán do tvého nelegálního inventáře.*"
        
        await interaction.followup.send(embed=embed, ephemeral=True)


class DarkwebCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- KONTROLNÍ FUNKCE PRO SERVER A KANÁLY ---
    def ma_povoleni(self, interaction: discord.Interaction):
        # Vrátí True, pokud je příkaz použit na správném serveru a ve správném kanálu
        if interaction.guild_id != POVOLENY_SERVER_ID:
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
    @app_commands.command(name="zalozit_sklad", description="[Admin/Boss] Založí nový utajený sklad na konkrétní číslo budovy.")
    @app_commands.describe(cislo_domu="Číslo budovy (např. 14)", heslo="Heslo pro přístup do skladu")
    async def zalozit_sklad(self, interaction: discord.Interaction, cislo_domu: str, heslo: str):
        if not self.ma_povoleni(interaction):
            return await interaction.response.send_message("❌ Tento příkaz zde nelze použít.", ephemeral=True)

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

    # --- 4. PŘÍSTUP DO SKLADU ---
    @app_commands.command(name="nelegal_sklad", description="Nahlédneš do tajného skladu budovy, pokud znáš heslo.")
    @app_commands.describe(cislo_domu="Číslo budovy", heslo="Zadej přístupové heslo")
    async def otevrit_sklad(self, interaction: discord.Interaction, cislo_domu: str, heslo: str):
        if not self.ma_povoleni(interaction):
            return await interaction.response.send_message("❌ Tento příkaz zde nelze použít.", ephemeral=True)

        sklad = kolekce_sklady.find_one({"_id": cislo_domu.strip()})
        
        # Kontrola existence a hesla s tichým odepřením přístupu
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

async def setup(bot):
    await bot.add_cog(DarkwebCog(bot))
