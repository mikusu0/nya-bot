import time, asyncio, random, discord
from discord.ext import commands
from core.db import Database
import core.utils as utils
from bot import MyBot

class Economy(commands.Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot
        self.db: Database = bot.database

    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.command(description="Your first job.")
    async def work(self, ctx: commands.Context):
        reward = random.randint(0, 100)
        user_id = str(ctx.author.id)

        await self.db.add_value_user_data(user_id, "balance", reward)
        balance = await self.db.get_value_user_data(user_id, "balance") 

        embed = discord.Embed(
            color=discord.Colour.dark_teal(),
            title=f"You have worked and gained {reward} 🪙",
            description=f"Current balance: {balance}",
        )
        if ctx.author.avatar:
            embed.set_thumbnail(url=ctx.author.avatar.url)

        await ctx.send(embed=embed)
    
    @commands.command(description="Balance?", aliases=["bal"])
    async def balance(self, ctx: commands.Context, *args):
        user_id = await utils.get_user_id(ctx, args)
        balance = await self.db.get_value_user_data(user_id, "balance")

        if user_id is None:
            await ctx.reply(f"❌ Wrong user. User {" ".join(args)} is not found.")
            return
        
        member = utils.get_user_by_id(ctx, user_id)

        if user_id == ctx.author.id:
            text = f"Your balance: {balance} 🪙"
        else:
            assert member is not None
            text = f"Balance of user {member.mention} is {balance} 🪙"

        await ctx.reply(text, allowed_mentions=discord.AllowedMentions.none())

async def setup(bot: MyBot) -> None:
    await bot.add_cog(Economy(bot))
