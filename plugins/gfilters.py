import io
import logging
from pyrogram import filters, Client, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from info import ADMINS
from database.gfilters_mdb import add_gfilter, get_gfilters, delete_gfilter, count_gfilters, del_allg
from utils import get_file_id, gfilterparser, split_quotes

logger = logging.getLogger(__name__)

@Client.on_message(filters.command(['add', 'addg']) & filters.incoming & filters.user(ADMINS))
async def addgfilter(client, message: Message):
    # Fixed: Corrected HTML string access parsing approach to prevent AttributeError crashes
    html_text = message.text.html if message.text else ""
    args = html_text.split(None, 1)

    if len(args) < 2:
        return await message.reply_text("Command Incomplete :(", quote=True)

    extracted = split_quotes(args[1])
    text = extracted[0].lower()

    if not message.reply_to_message and len(extracted) < 2:
        return await message.reply_text("Add some content to save your filter!", quote=True)

    fileid = None
    btn = []
    alert = None
    reply_text = ""

    if len(extracted) >= 2 and not message.reply_to_message:
        reply_text, btn, alert = gfilterparser(extracted[1], text)
        if not reply_text:
            return await message.reply_text("You cannot have buttons alone, give some text to go with it!", quote=True)

    elif message.reply_to_message and message.reply_to_message.reply_markup:
        try:
            rm = message.reply_to_message.reply_markup
            btn = rm.inline_keyboard
            msg = get_file_id(message.reply_to_message)
            if msg:
                fileid = msg.file_id
                # Fixed: Added a safe string fallback checking parameter logic
                caption_obj = message.reply_to_message.caption
                reply_text = caption_obj.html if caption_obj else ""
            else:
                reply_text = message.reply_to_message.text.html if message.reply_to_message.text else ""
        except Exception as e:
            logger.error(f"Error parsing markup filters layout: {e}")

    elif message.reply_to_message and message.reply_to_message.media:
        try:
            msg = get_file_id(message.reply_to_message)
            fileid = msg.file_id if msg else None
            
            caption_obj = message.reply_to_message.caption
            caption_html = caption_obj.html if caption_obj else ""
            
            if message.reply_to_message.sticker:
                reply_text, btn, alert = gfilterparser(extracted[1], text) if len(extracted) >= 2 else ("", [], None)
            else:
                reply_text, btn, alert = gfilterparser(caption_html, text)
        except Exception as e:
            logger.error(f"Error parsing media layout elements: {e}")
            
    elif message.reply_to_message and message.reply_to_message.text:
        try:
            reply_text, btn, alert = gfilterparser(message.reply_to_message.text.html, text)
        except Exception as e:
            logger.error(f"Error mapping text node markup elements: {e}")

    # Fire direct update mapping hooks out to database storage layer cleanly
    await add_gfilter('gfilters', text, reply_text, btn, fileid, alert)
    await message.reply_text(
        f"GFilter for `{text}` added successfully.",
        quote=True,
        parse_mode=enums.ParseMode.MARKDOWN
    )

@Client.on_message(filters.command(['viewgfilters', 'gfilters']) & filters.incoming & filters.user(ADMINS))
async def get_all_gfilters(client, message: Message):
    texts = await get_gfilters('gfilters')
    count = await count_gfilters('gfilters')
    
    if count:
        gfilterlist = f"Total number of global filters: {count}\n\n"
        for text in texts:
            gfilterlist += f" × `{text}`\n"

        if len(gfilterlist) > 4096:
            with io.BytesIO(str.encode(gfilterlist.replace("`", ""))) as keyword_file:
                keyword_file.name = "keywords.txt"
                return await message.reply_document(document=keyword_file, quote=True)
    else:
        gfilterlist = "There are no active global filters configured."

    await message.reply_text(
        text=gfilterlist,
        quote=True,
        parse_mode=enums.ParseMode.MARKDOWN
    )
        
@Client.on_message(filters.command('delg') & filters.incoming & filters.user(ADMINS))
async def deletegfilter(client, message: Message):
    try:
        _, text = message.text.split(None, 1)
    except ValueError:
        return await message.reply_text(
            "<i>Mention the gfiltername which you wanna delete!</i>\n\n"
            "<code>/delg gfiltername</code>\n\n"
            "Use /viewgfilters to view all available gfilters",
            quote=True
        )

    query = text.lower().strip()
    # Fixed: Passes 'gfilters' database target key context signature parameters correctly
    await delete_gfilter('gfilters', query)
    await message.reply_text(f"🗑️ Global filter `{query}` deleted successfully.", quote=True)

@Client.on_message(filters.command('delallg') & filters.user(ADMINS))
async def delallgfilters(client, message: Message):
    await message.reply_text(
        "Do you want to clear all global filters completely?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(text="YES, DELETE ALL", callback_data="gfiltersdeleteallconfirm")],
            [InlineKeyboardButton(text="CANCEL", callback_data="gfiltersdeleteallcancel")]
        ]),
        quote=True
    )

@Client.on_callback_query(filters.regex("^gfiltersdeleteallconfirm\$"))
async def dellacbd(client, query: CallbackQuery):
    await del_allg('gfilters')
    await query.answer("All Global Filters Deleted! 👍")
    await query.message.edit_text("✅ All global filters have been completely removed from database.")

@Client.on_callback_query(filters.regex("^gfiltersdeleteallcancel\$"))
async def cancel_delall(client, query: CallbackQuery):
    await query.answer("Action Cancelled!")
    await query.message.edit_text("Process Cancelled. ❌")
