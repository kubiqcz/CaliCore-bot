import discord
from discord.ext import commands

# Sem zadej ID role (nebo rolí), které má bot nováčkům automaticky dát
AUTOROLE_ID = 1394695578801148020, 1394695578801148018, 1394695578755272875, 1394695578419593232, 1394695578419593229 # Nahraď nulami skutečné ID role

class AutoRoleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Tento "listener" číhá na pozadí. Spustí se JEN tehdy, když se někdo nový připojí na server.
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # Najde roli na serveru podle zadaného ID
        role = member.guild.get_role(AUTOROLE_ID)
        
        if role:
            try:
                # Přiřadí roli nováčkovi
                await member.add_roles(role)
                print(f"✅ Hráči {member.name} byla automaticky přidělena role {role.name}.")
            except discord.Forbidden:
                print(f"❌ Bot nemá oprávnění přidělit roli {role.name}. Zkontroluj, jestli je role bota v nastavení serveru VÝŠ než tato role!")
            except Exception as e:
                print(f"❌ Nastala chyba při přidělování role: {e}")
        else:
            print("❌ Role nenalezena. Zkontroluj, zda jsi vložil správné AUTOROLE_ID.")

async def setup(bot):
    await bot.add_cog(AutoRoleCog(bot))
