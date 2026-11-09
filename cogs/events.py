import time, asyncio, discord, random
from discord.ext import commands
from core.db import Database
from bot import MyBot
from core.logger import logger

with open("data/bot_mention_phrases.txt", "r", encoding="utf-8") as f:
    bot_mention_phrases = [line for line in f.readlines()]

with open("data/kamojies.txt", "r", encoding="utf-8") as f:
    kamojies = [line for line in f.readlines()]

class Events(commands.Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot
        self.db: Database = bot.database
        
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # if message.author.id == karuta_id and message.content.find("dropping"):
        #     image_attachment = message.attachments[0] if message.attachments else None
        #     if image_attachment.filename.lower().endswith(('png', 'jpg', 'jpeg', 'webp', 'gif')):
        #         data = await get_info_from_card(image_attachment)
        #         kamojie = random.choice(kamojies)
        #         description = ""

        #         for name, series in data:
        #             description += f"**``klu {name}``**\n"

        #         embed = discord.Embed(
        #             title=f"📥 Karuta Card Drop Detected! {kamojie}",
        #             description=description,
        #             color=discord.Colour.light_gray()
        #         )
        #         await message.channel.send(embed=embed)


        #     return
        
        if message.author.bot:
            return
        
        user_id = message.author.id
        await self.db.add_value_user_data(user_id, "messages", 1)
        await self.db.add_value_user_data(user_id, "exp", 1)
        
        if message.content.startswith("goida"):
            await message.channel.send("respect")
        if message.content == self.bot.user.mention:
            phrase = random.choice(bot_mention_phrases)
            await message.reply(phrase)

        await self.db.sync_user_level(user_id)
            

            
    


async def setup(bot: MyBot) -> None:
    await bot.add_cog(Events(bot))
