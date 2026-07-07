import discord
from discord.ext import commands

# Seznam ID rolí, které se mají přidat (v hranatých závorkách)
AUTOROLE_IDS = [
    1394695578801148020, 
    1394695578801148018, 
    1394695578755272875, 
    1394695578419593232, 
    1394695578419593229
]

class AutoRoleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        print(f"🚨 Detekován nový hráč {member.name} na serveru, jdu přidělovat role!")
        
        # Tento řádek projde seznam a vybere jen ty role, které na serveru reálně existují
        role_k_pridani = [member.guild.get_role(role_id) for role_id in AUTOROLE_IDS if member.guild.get_role(role_id) is not None]
        
        if role_k_pridani:
            try:
                # Ta hvězdička (*) před 'role_k_pridani' rozbalí ten seznam a přidá mu je všechny naráz
                await member.add_roles(*role_k_pridani)
                print(f"✅ Hráči {member.name} byly úspěšně přiděleny automatické role.")
            except discord.Forbidden:
                print("❌ Bot nemá oprávnění přidělit některé role. Zkontroluj hierarchii!")
            except Exception as e:
                print(f"❌ Nastala chyba při přidělování rolí: {e}")
        else:
            print("❌ Žádná z rolí nebyla nalezena. Zkontroluj zadaná ID.")

async def setup(bot):
    await bot.add_cog(AutoRoleCog(bot))
