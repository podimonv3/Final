import logging
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, ChatAdminRequired, UsernameInvalid, UsernameNotModified
from info import ADMINS
from info import INDEX_REQ_CHANNEL as LOG_CHANNEL
from database.ia_filterdb import save_file, check_file
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import temp
import re

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
lock = asyncio.Lock()


@Client.on_callback_query(filters.regex(r'^index'))
async def index_files(bot, query):
    if query.data.startswith('index_cancel'):
        temp.CANCEL = True
        return await query.answer("Cancelling Indexing")
        
    _, raju, chat, lst_msg_id, from_user = query.data.split("#")
    
    if raju == 'reject':
        await query.message.delete()
        await bot.send_message(
            int(from_user),
            f'Your Submission for indexing {chat} has been declined by our moderators.',
            reply_to_message_id=int(lst_msg_id)
        )
        return

    if raju == 'accept':
        if lock.locked():
            return await query.answer('Wait until previous process complete.', show_alert=True)
            
        msg = query.message
        await query.answer('Processing...⏳', show_alert=True)
        
        if int(from_user) not in ADMINS:
            await bot.send_message(
                int(from_user),
                f'Your Submission for indexing {chat} has been accepted by our moderators and will be added soon.',
                reply_to_message_id=int(lst_msg_id)
            )
            
        await msg.edit(
            "Starting Indexing",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton('Cancel', callback_data='index_cancel')]]
            )
        )
        
        try:
            chat = int(chat)
        except:
            chat = chat
            
        await index_files_to_db(int(lst_msg_id), chat, msg, bot)


@Client.on_message((filters.forwarded | filters.text) & filters.private & filters.incoming)
async def send_for_index(bot, message: Message):
    chat_id = None
    last_msg_id = None
    user_id = message.from_user.id if message.from_user else None

    if not user_id:
        return

    # 1. URL / Forward Link Regex Parsing
    if message.text:
        match = URL_PATTERN.search(message.text)
        if not match:
            return await message.reply('❌ Invalid Telegram message link format provided.')
        chat_id = match.group(4)
        last_msg_id = int(match.group(5))
        if chat_id.isnumeric():
            chat_id = int(("-100" + chat_id))
            
    elif message.forward_from_chat and message.forward_from_chat.type == enums.ChatType.CHANNEL:
        last_msg_id = message.forward_from_message_id
        chat_id = message.forward_from_chat.username or message.forward_from_chat.id
    else:
        return await message.reply('ദയവായി ഒരു പബ്ലിക് ചാനലിൽ നിന്നുള്ള മെസ്സേജ് ഫോർവേഡ് ചെയ്യുക അല്ലെങ്കിൽ ശരിയായ മെസ്സേജ് ലിങ്ക് നൽകുക.')

    # 2. Chat Accessibility Verification Checks
    try:
        await bot.get_chat(chat_id)
        k = await bot.get_messages(chat_id, last_msg_id)
        if not k or k.empty:
            return await message.reply('Cannot read message context. If this is a private channel, confirm I am added as an admin.')
    except Exception as chat_err:
        logger.error(f"Chat validation failure in index tool: {chat_err}")
        return await message.reply('Make sure I am an admin in the target channel/group to index its history.')

    # 3. Dynamic Inline UI Menu Panel Construction
    buttons = [
        [InlineKeyboardButton('Index to Database', callback_data=f'index#accept#{chat_id}#{last_msg_id}#{user_id}')],
        [InlineKeyboardButton('Close ❌', callback_data='close_data')]
    ]
    
    # 🚀 FIXED USER INTERFACE GATEWAY SIGNATURE
    # If the user is an Admin, give them the immediate direct trigger controls layout
    if user_id in ADMINS:
        return await message.reply(
            f'Do you want to index this channel/group?\n\nChat ID/Username: <code>{chat_id}</code>\nLast Message ID: <code>{last_msg_id}</code>',
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )

    # 🚀 FIXED LOGGING ISOLATION CHANNEL GATEWAY
    # Wraps the administrator log routing inside a try/except guard so a missing log channel won't silence the bot's reply to the user!
    link = f"@{chat_id}" if not isinstance(chat_id, int) else "Private Channel Managed"
    if isinstance(chat_id, int):
        try:
            link_obj = await bot.create_chat_invite_link(chat_id)
            link = link_obj.invite_link
        except Exception:
            pass

    moderator_buttons = [
        [InlineKeyboardButton('Accept Index', callback_data=f'index#accept#{chat_id}#{last_msg_id}#{user_id}')],
        [InlineKeyboardButton('Reject Index', callback_data=f'index#reject#{chat_id}#{message.id}#{user_id}')]
    ]
    
    try:
        from info import INDEX_REQ_CHANNEL
        await bot.send_message(
            INDEX_REQ_CHANNEL,
            f'#IndexRequest\n\nBy: {message.from_user.mention} (<code>{user_id}</code>)\nChat ID: <code>{chat_id}</code>\nLast Message ID: <code>{last_msg_id}</code>\nInvite Link: {link}',
            reply_markup=InlineKeyboardMarkup(moderator_buttons)
        )
    except Exception as log_error:
        logger.error(f"Failed to push notification to admin indexing log channel: {log_error}")

    # Bypasses logging errors and guarantees the user always receives their submission success prompt
    await message.reply('Thank you for the contribution! Please wait for our moderators to verify and unpack the files.')


@Client.on_message(filters.command('setskip') & filters.user(ADMINS))
async def set_skip_number(bot, message):
    if ' ' in message.text:
        _, skip = message.text.split(" ")
        try:
            skip = int(skip)
        except:
            return await message.reply("Skip number should be an integer.")
        await message.reply(f"Successfully set SKIP number as {skip}")
        temp.CURRENT = int(skip)
    else:
        await message.reply("Give me a skip number")





async def index_files_to_db(lst_msg_id, chat, msg, bot):
    total_files, duplicate, errors, deleted, no_media, unsupported = 0, 0, 0, 0, 0, 0
    
    async with lock:
        try:
            current_processed = temp.CURRENT
            temp.CANCEL = False
            
            # 🚀 1. FIXED TOTAL BATCH COUNT RANGE CALCULATIONS
            # Prevents looping over infinite ranges or hitting deep FloodWait freezes
            total_range_limit = max(1, (int(lst_msg_id) - int(temp.CURRENT)) + 1)
            
            # 🚀 2. NAMED ARGUMENTS INTERFACE ALIGNMENT
            # Correctly maps the limit and offset parameters to match your bot.py custom iter_messages wrapper
            async for message in bot.iter_messages(chat, limit=total_range_limit, offset=int(temp.CURRENT)):
                if temp.CANCEL:
                    break
                    
                current_processed += 1
                if current_processed % 200 == 0:
                    try:
                        await msg.edit_text(
                            text=f"📊 **Indexing Progress Summary**\n\nFetched: <code>{current_processed}</code>\nSaved: <code>{total_files}</code>\nDuplicates: <code>{duplicate}</code>\nDeleted: <code>{deleted}</code>\nErrors: <code>{errors}</code>",
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🛑 Cancel Process', callback_data='index_cancel')]])
                        )
                    except Exception:
                        pass
                    
                if message.empty:
                    deleted += 1
                    continue
                if not message.media:
                    no_media += 1
                    continue
                if message.media not in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.AUDIO, enums.MessageMediaType.DOCUMENT]:
                    unsupported += 1
                    continue
                    
                media = getattr(message, message.media.value, None)
                if not media:
                    unsupported += 1
                    continue
                    
                media.file_type = message.media.value
                media.caption = message.caption
                
                # 🚀 3. FIXED MONGO COLLECTION VALIDATION PIPELINE
                # Perfectly indented try/except block to eliminate the SyntaxError crash
                try:
                    from database.ia_filterdb import Media, unpack_new_file_id, save_file
                    
                    file_id, file_ref = unpack_new_file_id(media.file_id)
                    exists = await Media.collection.find_one({'_id': file_id})
                    
                    if not exists:
                        aynav, vnay = await save_file(media) 
                        if aynav:
                            total_files += 1
                        else:
                            duplicate += 1
                    else:
                        duplicate += 1
                except Exception as loop_err:
                    logger.error(f"Error indexing item in manual loop: {loop_err}")
                    errors += 1
                    
        except Exception as outer_err:
            logger.exception(outer_err)
            await msg.edit_text(f'❌ Indexing process encountered a critical error: {outer_err}')
        else:
            status_prefix = "❌ Indexing Cancelled Manually!!" if temp.CANCEL else "✅ Indexing Successfully Completed!"
            await msg.edit_text(f'**{status_prefix}**\n\nSaved: <code>{total_files}</code>\nDuplicates: <code>{duplicate}</code>\nDeleted: <code>{deleted}</code>\nNon-Media Skipped: <code>{no_media + unsupported}</code>\nErrors: <code>{errors}</code>')
