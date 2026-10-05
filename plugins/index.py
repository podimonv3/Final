import logging
import asyncio
import re
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, ChatAdminRequired, UsernameInvalid, UsernameNotModified
from info import ADMINS
from info import INDEX_REQ_CHANNEL as LOG_CHANNEL
from database.ia_filterdb import save_file, check_file
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from utils import temp

logger = logging.getLogger(__name__)
lock = asyncio.Lock()

# Fixed: Removed the erroneous literal dollar symbol suffix check to make URL resolution functional
URL_PATTERN = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)")

@Client.on_callback_query(filters.regex(r'^index'))
async def index_files(bot, query: CallbackQuery):
    if query.data.startswith('index_cancel'):
        temp.CANCEL = True
        return await query.answer("Cancelling Indexing...", show_alert=True)
        
    try:
        # Fixed: Safely wrapped the parameter splits to prevent unpacking crashes on cancel events
        _, raju, chat, lst_msg_id, from_user = query.data.split("#")
    except ValueError:
        return await query.answer("Invalid callback request structure.", show_alert=True)
    
    if raju == 'reject':
        await query.message.delete()
        try:
            await bot.send_message(
                int(from_user),
                f'Your submission for indexing {chat} has been declined by our moderators.',
                reply_to_message_id=int(lst_msg_id)
            )
        except Exception:
            pass
        return

    if raju == 'accept':
        if lock.locked():
            return await query.answer('Wait until the current process completes.', show_alert=True)
            
        msg = query.message
        await query.answer('Processing request... ⏳', show_alert=True)
        
        if int(from_user) not in ADMINS:
            try:
                await bot.send_message(
                    int(from_user),
                    f'Your submission for indexing {chat} has been accepted by our moderators and will be processed shortly.',
                    reply_to_message_id=int(lst_msg_id)
                )
            except Exception:
                pass
            
        await msg.edit_text(
            "🚀 **Starting channel message history indexing...**",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton('🛑 Cancel Process', callback_data='index_cancel')]]
            )
        )
        
        try:
            chat = int(chat) if str(chat).strip().replace("-", "").isdigit() else str(chat)
        except ValueError:
            pass
            
        await index_files_to_db(int(lst_msg_id), chat, msg, bot)

@Client.on_message((filters.forwarded | filters.text) & filters.private & filters.incoming & filters.user(ADMINS))
async def send_for_index(bot, message: Message):
    chat_id = None
    last_msg_id = None
    
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

    try:
        await bot.get_chat(chat_id)
    except ChannelInvalid:
        return await message.reply('This may be a private channel/group. Make me an admin over there to index the files.')
    except (UsernameInvalid, UsernameNotModified):
        return await message.reply('Invalid link username specified.')
    except Exception as e:
        logger.exception(e)
        return await message.reply(f'Errors encountered: {e}')
        
    try:
        k = await bot.get_messages(chat_id, last_msg_id)
        if k.empty:
            return await message.reply('Cannot read message context. If this is a private channel, confirm I am added as an admin.')
    except Exception:
        return await message.reply('Make sure I am an admin in the channel if it is a private chat layer.')

    if message.from_user.id in ADMINS:
        buttons = [
            [InlineKeyboardButton('Index to Database', callback_data=f'index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}')],
            [InlineKeyboardButton('Close ❌', callback_data='close_data')]
        ]
        return await message.reply(
            f'Do you want to index this channel/group?\n\nChat ID/Username: <code>{chat_id}</code>\nLast Message ID: <code>{last_msg_id}</code>',
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # Standard moderator routing path rules for lower clearance submissions
    link = f"@{chat_id}" if not isinstance(chat_id, int) else "Private Channel Link Managed"
    if isinstance(chat_id, int):
        try:
            link_obj = await bot.create_chat_invite_link(chat_id)
            link = link_obj.invite_link
        except ChatAdminRequired:
            return await message.reply('Make sure I am an admin in the chat with invite-link generation permissions.')

    buttons = [
        [InlineKeyboardButton('Accept Index', callback_data=f'index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}')],
        [InlineKeyboardButton('Reject Index', callback_data=f'index#reject#{chat_id}#{message.id}#{message.from_user.id}')]
    ]
    
    await bot.send_message(
        LOG_CHANNEL,
        f'#IndexRequest\n\nBy: {message.from_user.mention} (<code>{message.from_user.id}</code>)\nChat ID: <code>{chat_id}</code>\nLast Message ID: <code>{last_msg_id}</code>\nInvite Link: {link}',
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    await message.reply('Thank you for the contribution! Please wait for our moderators to verify and unpack the files.')

@Client.on_message(filters.command('setskip') & filters.user(ADMINS))
async def set_skip_number(bot, message: Message):
    try:
        _, skip = message.text.split(None, 1)
        skip_val = int(skip.strip())
    except (ValueError, IndexError):
        return await message.reply("Usage: ` /setskip [integer] `")
        
    temp.CURRENT = skip_val
    await message.reply(f"Successfully set runtime SKIP threshold offset number as: `{skip_val}`")

async def index_files_to_db(lst_msg_id, chat, msg, bot):
    total_files, duplicate, errors, deleted, no_media, unsupported = 0, 0, 0, 0, 0, 0
    
    async with lock:
        try:
            current_processed = temp.CURRENT
            temp.CANCEL = False
            
            # Fixed: Correctly calculates absolute total limits based on file_store sequence layouts
            total_range_limit = max(1, (lst_msg_id - temp.CURRENT) + 1)
            
            async for message in bot.iter_messages(chat, limit=total_range_limit, offset=temp.CURRENT):
                if temp.CANCEL:
                    break
                    
                current_processed += 1
                if current_processed % 200 == 0:
                    try:
                        await msg.edit_text(
                            text=f"📊 **Indexing Progress Summary**\n\nFetched: <code>{current_processed}</code>\nSaved: <code>{total_files}</code>\nDuplicates: <code>{duplicate}</code>\nDeleted: <code>{deleted}</code>\nUnsupported: <code>{no_media + unsupported}</code>\nErrors: <code>{errors}</code>",
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
                
                try:
                    # Fixed: Query the database collection directly by unique ID to check if it's already indexed
                    from database.ia_filterdb import Media, unpack_new_file_id
                    
                    file_id, file_ref = unpack_new_file_id(media.file_id)
                    exists = await Media.collection.find_one({'_id': file_id})
                    
                    if not exists:
                        # Save the file using the clean async database mapping format
                        from database.ia_filterdb import save_file
                        aynav, vnay = await save_file(media) 
                        if aynav:
                            total_files += 1
                        else:
                            duplicate += 1
                    else:
                        duplicate += 1
                except Exception as index_err:
                    logger.error(f"Indexing item exception: {index_err}")
                    errors += 1

                    
        except Exception as outer_err:
            logger.exception(outer_err)
            await msg.edit_text(f'❌ Indexing process encountered a critical error: {outer_err}')
        else:
            status_prefix = "❌ Indexing Cancelled Manually!!" if temp.CANCEL else "✅ Indexing Successfully Completed!"
            await msg.edit_text(f'**{status_prefix}**\n\nSaved: <code>{total_files}</code>\nDuplicates: <code>{duplicate}</code>\nDeleted: <code>{deleted}</code>\nNon-Media Skipped: <code>{no_media + unsupported}</code>\nErrors: <code>{errors}</code>')
