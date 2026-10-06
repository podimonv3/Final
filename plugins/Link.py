import re
import urllib.parse
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from info import ADMINS
from utils import temp

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("link") & filters.user(ADMINS))
async def generate_link(client, message):
    """Generate a dynamic bot startup deep-link and build a verified valid Telegram share URL"""
    command_text = message.text.split(maxsplit=1)
    if len(command_text) < 2:
        await message.reply("Please provide the name for the movie! Example: `/link game of thrones`")
        return
        
    # Extract string, remove dangerous characters and replace spaces cleanly
    target_movie = str(command_text[1]).strip()
    target_movie = re.sub(r'[\u200b\u200c\u200d\ufeff\u200e\u200f]', '', target_movie)
    movie_name = target_movie.replace(" ", "-")
    
    # Extract bot username safely from temp parameters or directly from get_me profile setup
    bot_username = temp.U_NAME
    if not bot_username:
        try:
            bot_profile = await client.get_me()
            bot_username = bot_profile.username
            temp.U_NAME = bot_username
        except Exception as error:
            logger.error(f"Failed to fetch bot profile details: {error}")
            return await message.reply("Error: Unable to fetch bot username dynamically.")

    # Constructed the deep-link string format parameters securely
    link = f"https://t.me/{bot_username}?start=getfile-{movie_name}"
    
    # URL encode the link layout safely and swap legacy endpoint domain to standard t.me/share layout
    encoded_link = urllib.parse.quote(link, safe='')
    share_url = f"https://t.me/share/url?url={encoded_link}"
    
    try:
        await message.reply(
            text=f"Here is your link:\n`{link}`",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Share Link", url=share_url)]]
            ),
            disable_web_page_preview=True
        )
    except Exception as send_error:
        logger.error(f"Failed to deliver message package under generated URL limits: {send_error}")
        await message.reply(f"Here is your link:\n`{link}`\n\n*(Note: Share button failed due to invalid URL formats)*")
