import discord
from discord.ext import commands
from discord import app_commands

# Tvoje ID z HLAVNÍHO serveru
KANAL_ID = 1394695582760571070
ROLE_IMIGRANT_ID = 1394695578801148018
ROLE_OBCAN_ID = 1394695578801148019

# Tvoje ID z MDT serveru
MDT_SERVER_ID = 1453744303691137045  # DOPLŇ
MDT_FORUM_ID = 1453745209643896933   # DOPLŇ

class IDModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Vytvoření postavy")

    roblox_nick = discord.ui.TextInput(label="Roblox nick", placeholder="Roblox nick, ne display nick", required=True)
    rp_jmeno = discord.ui.TextInput(label="Jméno a Příjmení (v RP)", placeholder="Např. Oliver Brown", required=True)
    datum_narozeni = discord.ui.TextInput(label="Datum narození", placeholder="Např. 15/08/1995", required=True)
    misto_narozeni = discord.ui.TextInput(label="Místo narození", placeholder="Např. Los Angeles, CA", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        # PŘIDÁNO ČÍSLO ID PŘÍMO DO POPISU KARTY
        popis = (
            f"{interaction.user.mention}\n\n"
            f"**Číslo ID:** `{interaction.user.id}`\n"
            f"**Roblox nick:** {self.roblox_nick.value}\n"
            f"**Jméno a Příjmení:** {self.rp_jmeno.value}\n"
            f"**Datum narození:** {self.datum_narozeni.value}\n"
            f"**Místo narození:** {self.misto_narozeni.value}"
        )

        embed = discord.Embed(title="ID Karta", description=popis, color=discord.Color.blue())
        embed.set_footer(text="CaliCore DMV System | Los Angeles")

        # 1. Odeslání na hlavní server
        kanal = interaction.guild.get_channel(KANAL_ID)
        if kanal:
            await kanal.send(embed=embed)
            
        # 2. PROPOJENÍ NA MDT SERVER (Vytvoření příspěvku ve fóru)
        mdt_server = interaction.client.get_guild(MDT_SERVER_ID)
        if mdt_server:
            forum_kanal = mdt_server.get_channel(MDT_FORUM_ID)
            
            if isinstance(forum_kanal, discord.ForumChannel):
                try:
                    await forum_kanal.create_thread(
                        name=self.rp_jmeno.value, 
                        content=f"Složka občana: **{self.rp_jmeno.value}**\nČíslo ID: `{interaction.user.id}`",
                        embed=embed
                    )
                except discord.Forbidden:
                    print("CaliCore nemá oprávnění tvořit příspěvky ve fóru.")
            else:
                print("Zadané MDT_FORUM_ID nepatří Forum kanálu!")
        else:
            print("CaliCore nenašel MDT server.")
        
        # 3. Změna přezdívky
        nova_prezdivka = f"{self.rp_jmeno.value} | {self.roblox_nick.value}"
        if len(nova_prezdivka) > 32:
            nova_prezdivka = nova_prezdivka[:32]
        
        try:
            await interaction.user.edit(nick=nova_prezdivka)
        except discord.Forbidden:
            pass 

        # 4. Úprava rolí (Automaticky)
        role_obcan = interaction.guild.get_role(ROLE_OBCAN_ID)
        role_imigrant = interaction.guild.get_role(ROLE_IMIGRANT_ID)
        try:
            if role_obcan:
                await interaction.user.add_roles(role_obcan)
            if role_imigrant:
                await interaction.user.remove_roles(role_imigrant)
        except discord.Forbidden:
            pass

        # 5. Potichu zavře formulář
        await interaction.response.defer()

class IDKartaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="id", description="Vytvoř si kalifornský průkaz pro svou postavu.")
    async def id_command(self, interaction: discord.Interaction):
        await interaction.response.send_modal(IDModal())

async def setup(bot):
    await bot.add_cog(IDKartaCog(bot))
