import time, asyncio, discord, os, pathlib
import core.utils as utils
import requests, io, mimetypes
from discord.ext import commands
from discord import app_commands
from core.db import Database
from pathlib import Path
from core.logger import logger
from config import GUILD, USERS_PROFILE_IMAGE_PATH
from core.utils import with_api_config
from bot import MyBot

image_extensions = ["png", "gif", "jpg", "jpeg"]
os.makedirs(USERS_PROFILE_IMAGE_PATH, exist_ok=True)

class Utility(commands.Cog):
    def __init__(self, bot: MyBot):
        self.bot = bot
        self.db: Database = bot.database

    @commands.command(description="Tesuto.")
    async def test(self, ctx: commands.Context, *args):
        text = " ".join(args)
        await ctx.reply(f"私は {text}")

    @app_commands.command(name="pig", description="Respects ur pig.")
    async def pig_(self, interaction: discord.Interaction):
        start_time = time.perf_counter()
        bot_latency = round(self.bot.latency*1000)
        template = '🐖 Bot latency: {bot}ms\n🥩 Send latency: {send}'

        await interaction.response.send_message(template.format(bot = bot_latency, send='...'))
        final_time = round((time.perf_counter() - start_time) * 1000)
        msg = await interaction.original_response()
        
        await msg.edit(content=template.format(bot = bot_latency, send=f'{final_time}ms'))

    @commands.command(description="If you're imbecile u can try use it.")
    async def remind(self, ctx: commands.Context, arg1, arg2):
        arg1 = int(arg1)
        await asyncio.sleep(arg1)
        await ctx.send(content=f"{arg1}s passed: {arg2}")

    @commands.hybrid_command(description="Unbeliveable.")
    async def commands(self, ctx: commands.Context):
        embed = discord.Embed(
            title="📋 Commands:",
            color=discord.Colour.dark_teal())
        description = ""
        loaded = []
        # get_commands() without doubling in groups, walk_commands() gonna be doubled
        groups = [com for com in self.bot.tree.get_commands() if isinstance(com, app_commands.Group)]
        commands = [com for com in self.bot.tree.get_commands() if isinstance(com, app_commands.Command)]
        
        for slash_command in commands:
            if slash_command.name in loaded: continue
            description += f"`/{slash_command.name}` " + (slash_command.description if slash_command.description else "") + "\n"
            loaded.append(slash_command.name)


        for group_command in groups:
            for comm in group_command.commands:
                if comm.name in loaded: continue
                description += f"`/{group_command.name} {comm.name}`"+ (" " + comm.description if comm.description else "") + "\n"
                loaded.append(comm.name)


        for comm in self.bot.commands:
            if comm.name in loaded: continue
            description += f"`!{comm.name}` " + (comm.description if comm.description else "") + "\n"
            loaded.append(comm.name)

        embed.description = description
        await ctx.send(embed=embed, ephemeral=True)

class ProfileGroup(commands.GroupCog, name="profile", description="Profile commands"):
    # group = app_commands.Group(name="Profile", description="Profile commands", guild_ids=[GUILD])
    def __init__(self, bot: MyBot):
        self.bot = bot
        self.db: Database = bot.database
    
    # if group.command then will be /profile Profile view
    @app_commands.command(name="view", description="Check user's profile")
    @app_commands.describe(user="Mention, ID, or name")
    async def view_profile(self, interaction: discord.Interaction, user: str | None = None):
        user_id = await utils.get_user_id(interaction, user or interaction.user.name)
        if user_id is None:
            await interaction.response.send_message(f"❌ Wrong user. User {user} is not found.", ephemeral=True)
            return
        
        member = utils.get_user_by_id(interaction, user_id)
        if member is None:
            await interaction.response.send_message(f"❌ Member with ID `{user_id}` not found in this guild.", ephemeral=True)
            return
    
        data = await self.db.get_user_data(user_id)
        level_up_cost = await self.db.get_level_up_cost(user_id)

        bar = create_progress_bar(data.exp, level_up_cost, length=20)
        description = f"{member.mention}'s profile:\n{bar}\n\n"

        try:
            if data: 
                for k,v in data:
                    description += f"**• {k.capitalize()}:**" + f"`{v}`\n"
        except Exception as e:
            logger.error(f"Error while generating profile data for user {user_id}: {e}")

        embed = discord.Embed(
            title=f"Profile Info",
            description=description,
            color=discord.Colour.dark_teal()
            )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await interaction.response.defer(ephemeral=False)

        @with_api_config
        def fetch_profile_image(*, url: str, headers: dict, user_id: int):
            params = {"user_id": user_id}
            response: requests.Response = requests.get(url + f"get_avatar_decoration_image/{user_id}", headers=headers, params=params)
            return response

        response: requests.Response = fetch_profile_image(user_id=user_id)
        if response.status_code == 200:
            file_bytes = io.BytesIO(response.content)
            content_type = response.headers.get("Content-Type", "application/octet-stream")
            ext = mimetypes.guess_extension(content_type) or ".png"  # fallback to .png
            
            file_name = f"avatar_{user_id}{ext}"
            embed.set_image(url=f"attachment://{file_name}")
            file = discord.File(file_bytes, filename=file_name)

            await interaction.followup.send(embed=embed, file=file, allowed_mentions=discord.AllowedMentions.none())        
        else:
            await interaction.followup.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())        

    @app_commands.command(name="set_image", description="Change background of your profile")
    @app_commands.describe(image="Upload an image (max 1MB) Formats: png, gif, jpg, jpeg")
    async def set_background_profile(self, interaction: discord.Interaction, image: discord.Attachment):
        if image is None or image.content_type is None:
            await interaction.response.send_message("❌ You must upload a file.", ephemeral=True)
            return
        
        if not image.content_type.startswith("image/"):
            await interaction.response.send_message("❌ File must be an image.", ephemeral=True)
            return
        if image.size > 1_000_000:
            await interaction.response.send_message("❌ Image is too large. Max is 1MB", ephemeral=True)
            return
        
        image_format = image.filename.split(".")[-1].lower()
        if image_format not in image_extensions:
            await interaction.response.send_message("❌ This format doesn't supports.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        file_bytes = await image.read()
        try:
            @with_api_config
            def upload_image(*, url: str, headers: dict, user_id: int, image_filename: str, file_bytes: bytes):
                params = {"user_id": user_id}
                files = {"file": (image_filename, file_bytes)}  # tuple with filename and bytes
                response: requests.Response = requests.post(url + "upload_avatar_decoration_image/", headers=headers, params=params, files=files)
                return response

            response = upload_image(
                user_id=interaction.user.id,
                image_filename=f"{interaction.user.id}.{image_format}",
                file_bytes=file_bytes
            )
            if response.status_code != 200:
                raise Exception(f"API responded with status code {response.status_code}: {response.text}")
            else:
                logger.info(f"Profile image uploaded successfully for user {interaction.user.id}")
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to save image: {e}", ephemeral=True)
        else:
            await interaction.followup.send("✅ Uploaded succesfully!", ephemeral=True)        


        
async def setup(bot: MyBot):
    await bot.add_cog(ProfileGroup(bot))
    await bot.add_cog(Utility(bot))

def create_progress_bar(current: int, maximum: int, length: int = 10) -> str:
    if maximum == 0:
        return "[---------- 0%"

    filled_length = int((current / maximum) * length)
    bar = '█' * filled_length + '-' * (length - filled_length)
    percentage = (current / maximum) * 100

    return f"[{bar}] {int(percentage)}%"