import discord, re, time, os, requests, aiohttp, io, asyncio
from discord.ext import commands
from discord import app_commands
from typing import List, Callable
from functools import wraps
from PIL import Image, ImageEnhance, ImageFilter
# import numpy as np
from pathlib import Path
from config import API_KEY, API_URL
from core.logger import logger

# reader = easyocr.Reader(['en'], gpu=False, verbose=False, recognizer="Transformer") 
cog_files = [filename[:-3] for filename in os.listdir("./cogs") if filename.endswith(".py")]

def create_embed(title=None, description=None, color=None) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
    )
    return embed

async def get_user_id(ctx: commands.Context | discord.Interaction, args: tuple[str, ] | str | discord.User | discord.Member) -> int | None:
    if isinstance(args, (discord.User, discord.Member)):
        return args.id
    
    args = args if isinstance(args, tuple) else (args,)
    if not args: return ctx.author.id if isinstance(ctx, commands.Context) else ctx.user.id
    arg = " ".join(args).strip()

    if arg.isdigit(): return int(arg)

    match = re.match(r"<@!?(\d+)>", arg)
    if match: return int(match[1])

    arg = arg.lstrip("@")
    if ctx.guild:
        arg_lower = arg.lower()
        member = discord.utils.find(lambda m: m.name.lower() == arg_lower, ctx.guild.members)
        if member: return member.id
        member = discord.utils.find(lambda m: m.display_name.lower() == arg.lower(), ctx.guild.members)
        if member: return member.id

    return None

def get_user_by_id(ctx: commands.Context | discord.Interaction, id: int) -> discord.Member | None:
    if ctx.guild:
        return ctx.guild.get_member(id)
    return None

#with closer
def auto_complete(list: List[str]) -> Callable:
    async def _callback(interaction: discord.Interaction, current: str)  -> List[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=obj, value=obj)
            for obj in list if current.lower() in obj.lower()
        ]
    return _callback

# with closer
def with_api_config(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        headers = {"api-key": API_KEY}
        if "headers" not in kwargs:
            kwargs["headers"] = headers
        if "url" not in kwargs:
            kwargs["url"] = API_URL
        return func(*args, **kwargs)
    return wrapper

# get image text
# def gettext_from_image(region_box: tuple, image: Image.Image):
#     cropped = image.crop(region_box)
#     cropped = cropped.filter(ImageFilter.MedianFilter()) 
#     cropped = cropped.resize((cropped.width*4, cropped.height*4), resample=Image.Resampling.LANCZOS) 

#     cropped_np = np.array(cropped)
#     result = reader.readtext(cropped_np, detail=0, paragraph=True) 
#     return ' '.join(result)

# name_region = (45, 55, 245, 110)
# series_region = (45, 310, 245, 365)
# offset = 274

# async def get_info_from_card(attachment: discord.Attachment):
#     if type(attachment) == discord.Attachment:
#         async with aiohttp.ClientSession() as session:
#             async with session.get(attachment.url) as resp:
#                 if resp.status != 200:
#                     return None
#                 image_bytes = await resp.read()
#                 image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
#     else:
#         image = Image.open(attachment).convert("RGB")

#     try:

#         enchancer = ImageEnhance.Contrast(image)
#         image = enchancer.enhance(4)

#         result = []
#         for i in range(3):
#             name_box = (name_region[0] + i*offset, name_region[1], name_region[2] + i*offset, name_region[3])
#             series_box = (series_region[0] + i*offset, series_region[1], series_region[2] + i*offset, series_region[3])
            
#             name_text = gettext_from_image(name_box, image)
#             series_text = gettext_from_image(series_box, image)

#             result.append((name_text, series_text))

#         return result
        
#     except Exception as e:
#         logger.error(f"Failed to open image: {e}")
#         return None

# async def correct_with_jikan(ocr_text: str) -> str:
#     url = "https://api.jikan.moe/v4/characters"
#     params = {"q": ocr_text, "limit": 1}  # Fuzzy search, top match only
    
#     async with aiohttp.ClientSession() as session:
#         async with session.get(url, params=params) as resp:
#             if resp.status == 200:
#                 data = await resp.json()
#                 results = data.get("data", [])
#                 if results:
#                     return results[0]["name"]  # Official full name (e.g., "Rem")
#     return ocr_text  # Fallback

# if __name__ == "__main__":
#     async def test():
#         count = 0
#         for image in Path("C:/Users/Mix/Downloads/karuta-test").glob("*.png"):
#             if count >= 3:
#                 break
#             # count += 1

#             info = await get_info_from_card(image)
#             for name, series in info:
#                 print(name, "|", await correct_with_jikan(name), "|", series)      

#     asyncio.run(test())