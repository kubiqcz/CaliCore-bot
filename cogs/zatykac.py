import discord
from discord.ext import commands
from discord import app_commands
import pymongo

# ==========================================
# NASTAVENÍ OPRÁVNĚNÍ A KANÁLŮ
# ==========================================
ROLE_POLICIE_ID = 1523660335406383164  # Kdo může psát /zadost_zatykac
ROLE_SOUDCE_ID = 1524106694915788870   # Kdo může zatykač schválit
KANAL_SOUD_ID = 1524108627353538803    # Kam se žádost pošle soudu k posouzení
KANAL_AKTIVNI_ZATYKACE_ID = 1524108142206652416 # Kam se pošle schválený zatykač všem policistům

MONGO_URI = "mongodb+srv://kubiqcz1:Aluska78@calicore.kmnmj4h.mongodb.net/?appName=CaliCore"
klient = pymongo.MongoClient(MONGO_URI)
db_cloud = klient["calicore_databaze"]
kolekce_hraci = db_cloud["hraci"]

def nacti_databazi():
    data = {}
    for hrac in kolekce_hraci.find():
        data[str(hrac["_id"])] = hrac
    return data

# --- TŘÍDA PRO TLAČÍTKA (SOUDCE) ---
class ZatykacView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Vydat zatykač", style=discord.ButtonStyle.success, custom_id="zatykac_vydat", emoji="🟢")
    async def btn_vydat(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Kontrola, jestli má klikač roli soudce
        if ROLE_SOUDCE_ID not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("❌ Na toto rozhodnutí má právo pouze Soudce!", ephemeral=True)
            return

        embed = interaction.message.embeds[0]
        
        # Přečtení ID cíle ze skrytého footeru, abychom věděli, kam to poslat
        footer_text = embed.footer.text
        hrac_id = footer_text.replace("Číslo průkazu cíle: ", "")

        # 1. Úprava zprávy pro soudce (zežloutne na zelenou, tlačítka zmizí)
        embed.color = discord.Color.green()
        embed.title = "📄 ZATYKAČ VYDÁN (Schváleno)"
        embed.add_field(name="👨‍⚖️ Rozhodnutí soudu", value=f"Schválil a vydal: {interaction.user.mention}", inline=False)

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(embed=embed, view=self)

        # 2. Odeslání do kanálu "Přehled aktivních zatykačů"
        kanal_aktivni = interaction.client.get_channel(KANAL_AKTIVNI_ZATYKACE_ID)
        if kanal_aktivni:
            await kanal_aktivni.send(embed=embed)

        # 3. Odeslání přímo do složky hráče ve fóru MDT
        db = nacti_databazi()
        if hrac_id in db:
            vlakno_id = db[hrac_id].get("mdt_vlakno_id")
            if vlakno_id:
                vlakno = interaction.client.get_channel(vlakno_id)
                if vlakno:
                    await vlakno.send(embed=embed)

        await interaction.response.send_message("✅ Zatykač byl úspěšně vydán a rozeslán do databází.", ephemeral=True)

    @discord.ui.button(label="Zamítnout", style=discord.ButtonStyle.danger, custom_id="zatykac_zamitnout", emoji="🔴")
    async def btn_zamitnout(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Kontrola, jestli má klikač roli soudce
        if ROLE_SOUDCE_ID not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("❌ Na toto rozhodnutí má právo pouze Soudce!", ephemeral=True)
            return

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = "📄 ZÁDOST O ZATYKAČ ZAMÍTNUTA"
        embed.add_field(name="👨‍⚖️ Rozhodnutí soudu", value=f"Zamítl: {interaction.user.mention}", inline=False)

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message("✅ Žádost byla zamítnuta.", ephemeral=True)

# --- TŘÍDA PRO FORMULÁŘ (POLICISTA) ---
class ZatykacModal(discord.ui.Modal, title='Žádost o vydání zatykače'):
    cislo_prukazu = discord.ui.TextInput(
        label='Číslo průkazu (ID hráče)', 
        style=discord.TextStyle.short, 
        placeholder='Sem vlož to číslo v uvozovkách ze složky...', 
        required=True
    )
    
    spis = discord.ui.TextInput(
        label='Znění zatykače (Předloha)', 
        style=discord.TextStyle.paragraph, # Toto vytvoří to obrovské textové pole (až 4000 znaků)
        placeholder='Vložte předlohu zatykače a vyplňte ji...', 
        required=True,
        max_length=4000
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Tvá žádost byla odeslána soudu k posouzení.", ephemeral=True)

        embed = discord.Embed(title="⚖️ NOVÁ ŽÁDOST O ZATYKAČ", color=discord.Color.orange())
        embed.description = f"**Žadatel:** {interaction.user.mention}\n\n{self.spis.value}"
        
        # Tohle tajně uloží ID hráče, aby ho bot našel, když soudce klikne na "Vydat"
        embed.set_footer(text=f"Číslo průkazu cíle: {self.cislo_prukazu.value}")

        kanal_soud = self.bot.get_channel(KANAL_SOUD_ID)
        if kanal_soud:
            await kanal_soud.send(embed=embed, view=ZatykacView())

# --- SAMOTNÝ PŘÍKAZ ---
class ZatykacCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="zadost_zatykac", description="Odešle soudu žádost o zatykač. Po schválení se rozešle.")
    async def zadost_zatykac_command(self, interaction: discord.Interaction):
        if ROLE_POLICIE_ID not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("❌ Tento příkaz může použít pouze Policie!", ephemeral=True)
            return

        await interaction.response.send_modal(ZatykacModal(self.bot))

async def setup(bot):
    await bot.add_cog(ZatykacCog(bot))
