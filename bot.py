import os, discord, asyncio
from discord.ext import commands
from config import TOKEN, PREFIX, GUILD
from core.logger import logger
from core.db import Database
from core.utils import cog_files

class MyBot(commands.Bot):
    database = Database

    def __init__(self):
        intets = discord.Intents.default()
        intets.message_content = True
        intets.members = True
        
        super().__init__(command_prefix=PREFIX, intents=intets)
        self.remove_command("help")

    async def setup_hook(self) -> None:
        await self._load_cogs()

        guild = discord.Object(id=GUILD)
        await self.tree.sync(guild=guild)
        await self.tree.sync()

    async def _load_cogs(self):
        loaded_cogs = []

        for cog_name in cog_files:
            name = f"cogs.{cog_name}"
            if name not in self.extensions:
                await self.load_extension(name)
                logger.info(f"Loaded cog: {cog_name}")
                loaded_cogs.append(cog_name)


    async def on_ready(self):
        await Database.create_pool()
        logger.info(f"✅ Bot connected as {self.user} (ID: {self.user.id})")


    async def close(self) -> None:
        await Database.close_pool()
        logger.info("✅ Database connection closed")
        await super().close()


bot = MyBot()

async def main(): 
    try:
        await bot.start(str(TOKEN))
    finally:
        await bot.close()    

if __name__ == "__main__":
    asyncio.run(main())
