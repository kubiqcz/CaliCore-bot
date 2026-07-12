import discord
from discord.ext import commands
import asyncio

# ==========================================
# NASTAVENÍ MAJITELE
# ==========================================
TVOJE_DISCORD_ID = 828545265531093063 # <--- ZDE DOPLŇ SVÉ OSOBNÍ DISCORD ID

class BezpecnostCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def posli_dm_majiteli(self, embed):
        """Pomocná funkce, která ti pošle soukromou zprávu i s PINGEM."""
        majitel = self.bot.get_user(TVOJE_DISCORD_ID)
        if not majitel:
            try:
                majitel = await self.bot.fetch_user(TVOJE_DISCORD_ID)
            except discord.NotFound:
                print("Chyba: Nepodařilo se najít majitele pro odeslání bezpečnostního varování.")
                return

        try:
            # Explicitní ping v DM (content=majitel.mention)
            await majitel.send(content=majitel.mention, embed=embed)
        except discord.Forbidden:
            print("Chyba: Bot ti nemůže poslat DM. Zkontroluj, zda máš povolené soukromé zprávy od členů serveru.")

    def ziskej_seznam_admin_roli(self, guild):
        """Pomocná funkce, která vyfiltruje a vypíše všechny role s adminem."""
        admin_role = [role.mention for role in guild.roles if role.permissions.administrator]
        seznam = ", ".join(admin_role) if admin_role else "Žádné role nemají právo Administrátor."
        # Discord limit pro jedno políčko v embedu je 1024 znaků, pro jistotu ořízneme
        return seznam[:1024]

    # ---------------------------------------------------------
    # 1. KONTROLA ÚPRAVY ROLE (Pouze Zapnutí / Vypnutí Admina)
    # ---------------------------------------------------------
    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        # Hlídáme POUZE to, zda se změnilo právo Administrátor
        if before.permissions.administrator != after.permissions.administrator:
            
            await asyncio.sleep(2)
            pachatel = "Neznámý uživatel (zkontroluj Audit Log)"
            
            async for entry in after.guild.audit_logs(action=discord.AuditLogAction.role_update, limit=3):
                if entry.target.id == after.id:
                    pachatel = entry.user.mention
                    break

            stav = "✅ ZÍSKALA" if after.permissions.administrator else "❌ ZTRATILA"
            barva = discord.Color.red() if after.permissions.administrator else discord.Color.green()
            
            # Získáme aktuální seznam všech admin rolí
            vsechny_admin_role = self.ziskej_seznam_admin_roli(after.guild)

            embed = discord.Embed(
                title="⚠️ BEZPEČNOSTNÍ UPOZORNĚNÍ: Změna práv role",
                description=f"Roli **{after.name}** bylo změněno právo Administrátor: **{stav}**",
                color=barva
            )
            embed.add_field(name="Role", value=after.mention, inline=True)
            embed.add_field(name="Kdo změnu provedl", value=pachatel, inline=False)
            embed.add_field(name="📋 Aktuální seznam všech Admin rolí na serveru", value=vsechny_admin_role, inline=False)
            
            await self.posli_dm_majiteli(embed)

    # ---------------------------------------------------------
    # 2. KONTROLA PŘIDĚLENÍ / ODEBRÁNÍ ADMIN ROLE HRÁČI
    # ---------------------------------------------------------
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        pridane_role = set(after.roles) - set(before.roles)
        odebrane_role = set(before.roles) - set(after.roles)

        # Hlídáme jen role, které mají Administrátora
        pridane_admin_role = [role for role in pridane_role if role.permissions.administrator]
        odebrane_admin_role = [role for role in odebrane_role if role.permissions.administrator]

        # Hráč DOSTAL admin roli
        if pridane_admin_role:
            await asyncio.sleep(2)
            pachatel = "Neznámý uživatel (zkontroluj Audit Log)"
            
            async for entry in after.guild.audit_logs(action=discord.AuditLogAction.member_role_update, limit=3):
                if entry.target.id == after.id:
                    pachatel = entry.user.mention
                    break
                    
            vsechny_admin_role = self.ziskej_seznam_admin_roli(after.guild)

            for role in pridane_admin_role:
                embed = discord.Embed(
                    title="🚨 KRITICKÉ UPOZORNĚNÍ: Přidělení Admin Role",
                    description=f"Uživatel **{after.name}** dostal roli s Administrátorskými právy!",
                    color=discord.Color.dark_red()
                )
                embed.add_field(name="Cíl (Hráč)", value=after.mention, inline=True)
                embed.add_field(name="Přidělená role", value=role.name, inline=True)
                embed.add_field(name="Kdo roli přidělil", value=pachatel, inline=False)
                embed.add_field(name="📋 Aktuální seznam všech Admin rolí na serveru", value=vsechny_admin_role, inline=False)
                
                await self.posli_dm_majiteli(embed)

        # Hráči byla admin role ODEBRÁNA
        if odebrane_admin_role:
            await asyncio.sleep(2)
            pachatel = "Neznámý uživatel (zkontroluj Audit Log)"
            
            async for entry in after.guild.audit_logs(action=discord.AuditLogAction.member_role_update, limit=3):
                if entry.target.id == after.id:
                    pachatel = entry.user.mention
                    break

            vsechny_admin_role = self.ziskej_seznam_admin_roli(after.guild)

            for role in odebrane_admin_role:
                embed = discord.Embed(
                    title="🛡️ BEZPEČNOSTNÍ UPOZORNĚNÍ: Odebrání Admin Role",
                    description=f"Uživateli **{after.name}** byla odebrána role s Administrátorskými právy.",
                    color=discord.Color.green()
                )
                embed.add_field(name="Cíl (Hráč)", value=after.mention, inline=True)
                embed.add_field(name="Odebraná role", value=role.name, inline=True)
                embed.add_field(name="Kdo roli odebral", value=pachatel, inline=False)
                embed.add_field(name="📋 Aktuální seznam všech Admin rolí na serveru", value=vsechny_admin_role, inline=False)
                
                await self.posli_dm_majiteli(embed)

async def setup(bot):
    await bot.add_cog(BezpecnostCog(bot))
