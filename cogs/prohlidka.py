import discord
from discord.ext import commands
from discord import app_commands

# ==========================================
# NASTAVENÍ OPRÁVNĚNÍ A KANÁLŮ
# ==========================================
ROLE_POLICIE_ID = 1523660335406383164  # Kdo může psát /zadost_prohlidka
ROLE_SOUDCE_ID = 1524106694915788870   # Kdo může povolení schválit
KANAL_SOUD_ID = 1524134941066006680    # Kam se žádost pošle soudu k posouzení

# SEM ZADEJ ID KANÁLU, KAM SE POŠLOU SCHVÁLENÉ PROHLÍDKY:
KANAL_AKTIVNI_PROHLIDKY_ID = 1524134603357421659 

# --- TŘÍDA PRO FORMULÁŘ PODPISU SOUDCE ---
class SoudcePodpisProhlidkaModal(discord.ui.Modal, title='Oficiální podpis soudce'):
    jmeno_soudce = discord.ui.TextInput(
        label='Tvé jméno a příjmení (Postava)', 
        style=discord.TextStyle.short, 
        placeholder='Např. JUDr. Antonín Sova', 
        required=True
    )

    def __init__(self, puvodni_zprava, puvodni_view):
        super().__init__()
        self.puvodni_zprava = puvodni_zprava
        self.puvodni_view = puvodni_view

    async def on_submit(self, interaction: discord.Interaction):
        embed = self.puvodni_zprava.embeds[0]
        
        # 1. Úprava zprávy pro soudce
        embed.color = discord.Color.green()
        embed.title = "🏠 POVOLENÍ K PROHLÍDCE VYDÁNO (Schváleno)"
        
        # Přidání jména soudce kurzívou na úplný konec
        embed.description += f"\n\n*Oficiálně schválil a vydal: {self.jmeno_soudce.value}*"

        # Vypnutí tlačítek
        for child in self.puvodni_view.children:
            child.disabled = True
        await self.puvodni_zprava.edit(embed=embed, view=self.puvodni_view)

        # 2. Odeslání do kanálu "Přehled aktivních prohlídek"
        kanal_aktivni = interaction.client.get_channel(KANAL_AKTIVNI_PROHLIDKY_ID)
        if kanal_aktivni:
            await kanal_aktivni.send(embed=embed)

        await interaction.response.send_message("✅ Povolení k prohlídce bylo podepsáno a vydáno.", ephemeral=True)

# --- TŘÍDA PRO TLAČÍTKA (SOUDCE) ---
class ProhlidkaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Vydat povolení", style=discord.ButtonStyle.success, custom_id="prohlidka_vydat", emoji="🟢")
    async def btn_vydat(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Kontrola oprávnění
        if ROLE_SOUDCE_ID not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("❌ Na toto rozhodnutí má právo pouze Soudce!", ephemeral=True)
            return

        # Okno pro podpis soudce
        await interaction.response.send_modal(SoudcePodpisProhlidkaModal(interaction.message, self))

    @discord.ui.button(label="Zamítnout", style=discord.ButtonStyle.danger, custom_id="prohlidka_zamitnout", emoji="🔴")
    async def btn_zamitnout(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Kontrola oprávnění
        if ROLE_SOUDCE_ID not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("❌ Na toto rozhodnutí má právo pouze Soudce!", ephemeral=True)
            return

        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = "🏠 ŽÁDOST O PROHLÍDKU ZAMÍTNUTA"
        embed.add_field(name="👨‍⚖️ Rozhodnutí soudu", value=f"Zamítl: {interaction.user.mention}", inline=False)

        for child in self.children:
            child.disabled = True
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message("✅ Žádost byla zamítnuta.", ephemeral=True)

# --- TŘÍDA PRO FORMULÁŘ (POLICISTA) ---
class ProhlidkaModal(discord.ui.Modal, title='Žádost o povolení k prohlídce'):
    spis = discord.ui.TextInput(
        label='Znění žádosti (Předloha)', 
        style=discord.TextStyle.paragraph,
        placeholder='Vložte předlohu pro domovní prohlídku a vyplňte ji...', 
        required=True,
        max_length=4000
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Tvá žádost o prohlídku byla odeslána soudu k posouzení.", ephemeral=True)

        embed = discord.Embed(title="⚖️ NOVÁ ŽÁDOST O PROHLÍDKU", color=discord.Color.orange())
        embed.description = f"**Žadatel:** {interaction.user.mention}\n\n{self.spis.value}"

        kanal_soud = self.bot.get_channel(KANAL_SOUD_ID)
        if kanal_soud:
            await kanal_soud.send(embed=embed, view=ProhlidkaView())

# --- SAMOTNÝ PŘÍKAZ ---
class ProhlidkaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="zadost_prohlidka", description="Odešle soudu žádost o povolení k prohlídce.")
    async def zadost_prohlidka_command(self, interaction: discord.Interaction):
        if ROLE_POLICIE_ID not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("❌ Tento příkaz může použít pouze Policie!", ephemeral=True)
            return

        await interaction.response.send_modal(ProhlidkaModal(self.bot))

async def setup(bot):
    await bot.add_cog(ProhlidkaCog(bot))
