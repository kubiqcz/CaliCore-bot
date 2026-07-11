import discord
from discord.ext import commands

# ==========================================
# NASTAVENÍ KANÁLU
# ==========================================
UVITACI_KANAL_ID = 1394695580344647761 # <--- DOPLŇ ID KANÁLU (např. #vítejte)

class UvitaniCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Tento "listener" čeká na moment, kdy se někdo nový připojí na server
    @commands.Cog.listener()
    async def on_member_join(self, member):
        kanal = self.bot.get_channel(UVITACI_KANAL_ID)
        if not kanal:
            return

        # VÝPOČET STATISTIK:
        # member.guild.members obsahuje úplně všechny (lidi i boty)
        celkem_clenu = member.guild.member_count
        
        # Projedeme všechny členy a spočítáme jen ty, co mají flag .bot == True
        pocet_botu = len([m for m in member.guild.members if m.bot])
        
        # Lidi jsou logicky celkový počet mínus boti
        pocet_lidi = celkem_clenu - pocet_botu

        # --- TVORBA UVÍTACÍHO EMBEDU ---
        embed = discord.Embed(
            title="👋 Vítej v CaliCore RP!",
            description=f"Ahoj {member.mention}, jsme rádi, že ses připojil k naší komunitě!\n\n"
                        f"**📝 Tvé první kroky:**\n"
                        f"**1.** Přečti si pravidla v <#1394695582261710891>\n"
                        f"**2.** Založ si u nás občanku v <#1394695582760571070>\n"
                        f"Pokud budeš mít jakýkoliv dotaz, neboj se založit si ticket.\n"
                        f"Užij si RP.",
            color=discord.Color.blue()
        )
        
        # Přidá do rohu profilový obrázek nového hráče
        if member.display_avatar:
            embed.set_thumbnail(url=member.display_avatar.url)

        # Přidá statistiky o lidech a botech
        embed.add_field(
            name="📊 Aktuální statistiky serveru", 
            value=f"👥 Občané: **{pocet_lidi}**\n🤖 Boti: **{pocet_botu}**\n📈 Celkem nás je: **{celkem_clenu}**", 
            inline=False
        )

        embed.set_footer(text="CaliCore RP | Los Angeles County")

        # Odeslání zprávy. Content = pingne hráče, Embed = ukáže ten hezký panel
        await kanal.send(content=member.mention, embed=embed)

async def setup(bot):
    await bot.add_cog(UvitaniCog(bot))
