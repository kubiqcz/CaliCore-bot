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

    # Políčka
    rp_jmeno = discord.ui.TextInput(label="Jméno a Příjmení (v RP)", placeholder="Např. John Doe", required=True)
    datum_narozeni = discord.ui.TextInput(label="Datum narození", placeholder="Např. 15. 4. 1995", required=True)
    narodnost = discord.ui.TextInput(label="Národnost", placeholder="Např. Americká", required=True)
    pohlavi = discord.ui.TextInput(label="Pohlaví", placeholder="Muž / Žena", required=True)
    roblox_jmeno = discord.ui.TextInput(label="Roblox Jméno", placeholder="Přesné jméno v ER:LC (ne Display Nick!)", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        # 1. Vytvoření Embedu
        embed = discord.Embed(title=f"🪪 Občanský průkaz - Postava {self.cislo_postavy}", color=discord.Color.blue())
        embed.add_field(name="Majitel účtu", value=interaction.user.mention, inline=False)
        embed.add_field(name="Jméno", value=self.rp_jmeno.value, inline=True)
        embed.add_field(name="Datum narození", value=self.datum_narozeni.value, inline=True)
        embed.add_field(name="Národnost", value=self.narodnost.value, inline=True)
        embed.add_field(name="Pohlaví", value=self.pohlavi.value, inline=True)
        embed.add_field(name="Roblox Jméno", value=self.roblox_jmeno.value, inline=False)
        embed.set_footer(text="CaliCore DMV System | Los Angeles")
        embed.set_thumbnail(url=interaction.user.display_avatar.url) # Přidá profilovku na okrasu

        # 2. Odeslání do evidenčního kanálu
        kanal = interaction.guild.get_channel(KANAL_ID)
        if kanal:
            await kanal.send(embed=embed)
        
        # 3. Změna přezdívky (S ošetřením limitu 32 znaků)
        nova_prezdivka = f"{self.rp_jmeno.value} | {self.roblox_jmeno.value}"
        if len(nova_prezdivka) > 32:
            nova_prezdivka = nova_prezdivka[:32] # Pokud je moc dlouhá, ořízne se
        
        try:
            await interaction.user.edit(nick=nova_prezdivka)
        except discord.Forbidden:
            print(f"Nemám právo přejmenovat hráče {interaction.user.name}.") # Pamatuj: Nelze přejmenovat Majitele serveru

        # 4. Správa rolí (Odebrání Imigranta a přidání Občana, POUZE u první postavy)
        if self.cislo_postavy == 1:
            role_obcan = interaction.guild.get_role(ROLE_OBCAN_ID)
            role_imigrant = interaction.guild.get_role(ROLE_IMIGRANT_ID)
            
            try:
                if role_obcan:
                    await interaction.user.add_roles(role_obcan)
                if role_imigrant:
                    await interaction.user.remove_roles(role_imigrant)
            except discord.Forbidden:
                print("Nemám právo upravovat role. (Bot musí být v hierarchii nad nimi)")

        # 5. Potvrzovací zpráva pro uživatele
        await interaction.response.send_message("Tvá občanka byla úspěšně vytvořena a uložena do databáze!", ephemeral=True)

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
