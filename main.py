import discord
from discord.ext import commands
import os
from keep_alive import keep_alive
from discord import app_commands

# ID čísla tvého serveru
KANAL_ID = 1394695582760571070
ROLE_IMIGRANT_ID = 1394695578801148018
ROLE_OBCAN_ID = 1394695578801148019

# Třída pro vyskakovací okno (Modal)
class IDModal(discord.ui.Modal):
    def __init__(self, cislo_postavy):
        super().__init__(title=f"Vytvoření postavy {cislo_postavy}")
        self.cislo_postavy = cislo_postavy

    # Čistě jen 4 políčka podle tvé předlohy
    roblox_nick = discord.ui.TextInput(label="Roblox nick", placeholder="Roblox nick, ne display nick", required=True)
    rp_jmeno = discord.ui.TextInput(label="Jméno a Příjmení (v RP)", placeholder="Např. Oliver Brown", required=True)
    datum_narozeni = discord.ui.TextInput(label="Datum narození", placeholder="Např. 15/08/1995", required=True)
    misto_narozeni = discord.ui.TextInput(label="Místo narození", placeholder="Např. Los Angeles, CA", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        # 1. Poskládání textu pod sebe přesně podle předlohy
        popis = (
            f"{interaction.user.mention}\n\n"
            f"**Roblox nick:** {self.roblox_nick.value}\n"
            f"**Jméno a Příjmení:** {self.rp_jmeno.value}\n"
            f"**Datum narození:** {self.datum_narozeni.value}\n"
            f"**Místo narození:** {self.misto_narozeni.value}"
        )

        # 2. Vytvoření Embedu (bez fotek a profilovek)
        embed = discord.Embed(title=f"ID Karta - Postava {self.cislo_postavy}", description=popis, color=discord.Color.blue())
        embed.set_footer(text="CaliCore DMV System | Los Angeles")

        # 3. Odeslání do evidenčního kanálu
        kanal = interaction.guild.get_channel(KANAL_ID)
        if kanal:
            await kanal.send(embed=embed)
        
        # 4. Změna přezdívky (S ošetřením limitu 32 znaků)
        nova_prezdivka = f"{self.rp_jmeno.value} | {self.roblox_nick.value}"
        if len(nova_prezdivka) > 32:
            nova_prezdivka = nova_prezdivka[:32]
        
        try:
            await interaction.user.edit(nick=nova_prezdivka)
        except discord.Forbidden:
            pass # Skryje varování v konzoli, pokud to zkusí majitel serveru

        # 5. Správa rolí (Odebrání Imigranta a přidání Občana u 1. postavy)
        if self.cislo_postavy == 1:
            role_obcan = interaction.guild.get_role(ROLE_OBCAN_ID)
            role_imigrant = interaction.guild.get_role(ROLE_IMIGRANT_ID)
            
            try:
                if role_obcan:
                    await interaction.user.add_roles(role_obcan)
                if role_imigrant:
                    await interaction.user.remove_roles(role_imigrant)
            except discord.Forbidden:
                pass

        # 6. Potvrzovací zpráva pro uživatele
        await interaction.response.send_message("Tvá ID Karta byla úspěšně vytvořena!", ephemeral=True)

# Nastavení bota
class CaliCore(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        await self.tree.sync()
        print("Slash commandy byly načteny.")

bot = CaliCore()

@bot.event
async def on_ready():
    print(f'Přihlášen jako {bot.user}!')

# Command: /ping
@bot.tree.command(name="ping", description="Zkontroluje, jestli CaliCore žije.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong! CaliCore je online a připraven na RP v Los Angeles.")

# Command: /id
@bot.tree.command(name="id", description="Vytvoř si kalifornský průkaz pro svou postavu.")
@app_commands.describe(postava="Vyber, kterou postavu chceš upravit/vytvořit")
@app_commands.choices(postava=[
    app_commands.Choice(name="Postava 1", value=1),
    app_commands.Choice(name="Postava 2", value=2)
])
async def id_command(interaction: discord.Interaction, postava: app_commands.Choice[int]):
    await interaction.response.send_modal(IDModal(cislo_postavy=postava.value))

keep_alive()

token = os.environ.get("DISCORD_TOKEN")
bot.run(token)
