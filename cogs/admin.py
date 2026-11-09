import discord
from discord.ext import commands
from discord import app_commands
from typing import List, Optional
from core.utils import cog_files, auto_complete
from bot import MyBot

class Admin(commands.Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot
        self.previous_reloaded = ''
    
    @commands.hybrid_command(name="reload", description="Reloads a cog.")
    @commands.is_owner()
    @app_commands.autocomplete(cog_name=auto_complete(cog_files))
    async def reload_cog(self, ctx:commands.Context, cog_name: Optional[str] = None):
        try:
            cog_name = cog_name if cog_name else self.previous_reloaded

            await self.bot.reload_extension(f"cogs.{cog_name}")
            await ctx.send(f"✅ Reloaded cog '{cog_name}' succesfully.")
            
            self.previous_reloaded = cog_name
        except Exception as e:
            await ctx.send(f"⚠️ An error occured while reloadeding cog '{cog_name}': {e}")

    @commands.hybrid_command(name="load", description="Loads a cog.")
    @commands.is_owner()
    @app_commands.autocomplete(cog_name=auto_complete(cog_files))
    async def load_cog(self, ctx:commands.Context, cog_name: str):
        try:
            await self.bot.load_extension(f"cogs.{cog_name}")
            await ctx.send(f"✅ Loaded cog '{cog_name}' succesfully.")
        except Exception as e:
            await ctx.send(f"⚠️ An error occured while loading cog '{cog_name}': {e}")


async def setup(bot: MyBot) -> None:
    await bot.add_cog(Admin(bot))