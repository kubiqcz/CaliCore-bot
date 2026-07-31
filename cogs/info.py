import discord
from discord.ext import commands
from discord import app_commands

# ==========================================
# 1. TŘÍDA PRO TLAČÍTKA (VIEW)
# ==========================================
class InformaceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # timeout=None znamená, že tlačítka nikdy nevyprší
        
        # Přidání URL tlačítek (Zde si uprav odkazy na vaše reálné)
        self.add_item(discord.ui.Button(label="Web-(pracujeme na tom)", url="https://tvuj-web.cz"))
        self.add_item(discord.ui.Button(label="Discord", url="https://discord.gg/znmG3tNBbg"))
        self.add_item(discord.ui.Button(label="Group", url="https://www.roblox.com/share/g/983671369"))


# ==========================================
# 2. HLAVNÍ TŘÍDA COGU
# ==========================================
class InformaceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="info_panel", description="[Admin] Pošle hlavní informační panel na server.")
    async def info_panel(self, interaction: discord.Interaction):
        # Ochrana, aby to mohl poslat jen admin
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Nemáš oprávnění. Tento příkaz je pouze pro administrátory.", ephemeral=True)

        barva_bila = 0xffffff # Hex kód pro bílou barvu proužku na kraji

        # --- EMBED 1: Pouze banner (obrázek) ---
        embed1 = discord.Embed(color=barva_bila)
        embed1.set_image(url="https://i.imgur.com/TVUJ_BANNER.png") # Zde dej přímý odkaz na váš banner

        # --- EMBED 2: Uvítání a text ---
        embed2 = discord.Embed(
            description="Vítejte na místě, kde každý příběh vzniká z vašich rozhodnutí. CaliCore je projekt postavený na kvalitním RP, stabilním zázemí a komunitě, který má skutečný význam.",
            color=barva_bila
        )
        embed2.set_author(
            name="Vítejte na CaliCore", 
            icon_url="https://i.imgur.com/TVOJE_LOGO.png" # Zde dej odkaz na vaše kulaté logo
        )

        # --- EMBED 3: Klikací odkazy v textu ---
        # Pomocí syntaxe [Text](odkaz) uděláš klikací modrý text
        embed3 = discord.Embed(
            description="[Oficiální pravidla - CaliCore](https://odkaz-na-pravidla.cz)\n[Nelegální discord - CaliCore](https://discord.gg/nelegal)",
            color=barva_bila
        )

        # Odeslání všech 3 embedů najednou jako LIST (v hranatých závorkách) + připojení tlačítek
        await interaction.channel.send(embeds=[embed1, embed2, embed3], view=InformaceView())
        
        # Potvrzení pro admina, že se to odeslalo (zpráva jen pro tebe)
        await interaction.response.send_message("✅ Informační panel byl úspěšně odeslán do tohoto kanálu!", ephemeral=True)


# ==========================================
# 3. NAHRÁNÍ COGU BOTA
# ==========================================
async def setup(bot):
    await bot.add_cog(InformaceCog(bot))
