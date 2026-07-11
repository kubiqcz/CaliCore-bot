import discord
from discord.ext import commands, tasks

# ==========================================
# NASTAVENÍ ID KANÁLŮ A SERVERU
# ==========================================
GUILD_ID = 1394695578394558524          # <--- Zde doplň ID celého tvého serveru
KANAL_VSICHNI_ID = 1394695580344647757  # <--- ID kanálu "Všichni členi: X"
KANAL_CLENI_ID = 1394695580344647758    # <--- ID kanálu "Členi: X"
KANAL_BOTI_ID = 1394695580344647759     # <--- ID kanálu "Boti: X"

class ServerStatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Spustí smyčku při načtení modulu
        self.aktualizace_statistik.start()

    def cog_unload(self):
        # Vypne smyčku, pokud by se modul vypínal
        self.aktualizace_statistik.cancel()

    # Smyčka běží každých 30 minut, aby nás Discord nezablokoval za spam
    @tasks.loop(minutes=30)
    async def aktualizace_statistik(self):
        # Počkáme, až bude bot po startu plně ready
        await self.bot.wait_until_ready()
        
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return

        # Vypočítáme aktuální čísla přímo z paměti Discordu (nevyužívá cloud!)
        celkem = guild.member_count
        boti = len([m for m in guild.members if m.bot])
        lidi = celkem - boti

        # Sestavíme nové názvy přesně podle tvého obrázku
        nazev_vsichni = f"〔🔊〕Všichni členi: {celkem}"
        nazev_cleni = f"〔🔊〕Členi: {lidi}"
        nazev_boti = f"〔🔊〕Boti: {boti}"

        try:
            # Kanál "Všichni členi"
            k_vsichni = guild.get_channel(KANAL_VSICHNI_ID)
            # Přejmenuje ho jen tehdy, pokud se počet reálně změnil
            if k_vsichni and k_vsichni.name != nazev_vsichni:
                await k_vsichni.edit(name=nazev_vsichni)

            # Kanál "Členi" (Lidi)
            k_cleni = guild.get_channel(KANAL_CLENI_ID)
            if k_cleni and k_cleni.name != nazev_cleni:
                await k_cleni.edit(name=nazev_cleni)

            # Kanál "Boti"
            k_boti = guild.get_channel(KANAL_BOTI_ID)
            if k_boti and k_boti.name != nazev_boti:
                await k_boti.edit(name=nazev_boti)
                
        except discord.Forbidden:
            print("Chyba: Bot nemá práva 'Manage Channels' (Spravovat kanály).")
        except Exception as e:
            print(f"Chyba při updatu statistik kanálů: {e}")

async def setup(bot):
    await bot.add_cog(ServerStatsCog(bot))
