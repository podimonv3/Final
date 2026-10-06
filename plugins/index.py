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


@Client.on_message((filters.forwarded | (filters.regex(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)\$")) & filters.text ) & filters.private & filters.incoming & filters.user(ADMINS))
async def send_for_index(bot, message):
    if message.text:
        regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)\$")
        match = regex.match(message.text)
        if not match:
            return await message.reply('Invalid link')
        chat_id = match.group(4)
        last_msg_id = int(match.group(5))
        if chat_id.isnumeric():
            chat_id  = int(("-100" + chat_id))
    elif message.forward_from_chat and message.forward_from_chat.type == enums.ChatType.CHANNEL:
        last_msg_id = message.forward_from_message_id
        chat_id = message.forward_from_chat.username or message.forward_from_chat.id
    else:
        return await message.reply('ദയവായി ഒരു പബ്ലിക് ചാനലിൽ നിന്നുള്ള മെസ്സേജ് ഫോർവേഡ് ചെയ്യുക അല്ലെങ്കിൽ ശരിയായ മെസ്സേജ് ലിങ്ക് നൽകുക.')

    try:
        await bot.get_chat(chat_id)
    except ChannelInvalid:
        return await message.reply('This may be a private channel / group. Make me an admin over there to index the files.')
    except (UsernameInvalid, UsernameNotModified):
        return await message.reply('Invalid Link specified.')
    except Exception as e:
        logger.exception(e)
        return await message.reply(f'Errors - {e}')
        
    try:
        k = await bot.get_messages(chat_id, last_msg_id)
    except:
        return await message.reply('Make Sure That Iam An Admin In The Channel, if channel is private')
        
    if k.empty:
        return await message.reply('This may be group and iam not a admin of the group.')

    # ബട്ടണുകൾ ഒരൊറ്റ ഇൻഡെക്സ് ഓപ്ഷൻ മാത്രമാക്കി ലളിതമാക്കി
    if message.from_user.id in ADMINS:
        buttons = [
            [
                InlineKeyboardButton('Index to Database',
                                     callback_data=f'index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}')
            ],
            [
                InlineKeyboardButton('Close', callback_data='close_data'),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        return await message.reply(
            f'Do you Want To Index This Channel/ Group ?\n\nChat ID/ Username: <code>{chat_id}</code>\nLast Message ID: <code>{last_msg_id}</code>',
            reply_markup=reply_markup)

    if type(chat_id) is int:
        try:
            link = (await bot.create_chat_invite_link(chat_id)).invite_link
        except ChatAdminRequired:
            return await message.reply('Make sure iam an admin in the chat and have permission to invite users.')
    else:
        username = message.forward_from_chat.username if message.forward_from_chat else chat_id
        link = f"@{username}"
        
    buttons = [
        [
            InlineKeyboardButton('Accept Index',
                                 callback_data=f'index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}')
        ],
        [
            InlineKeyboardButton('Reject Index',
                                 callback_data=f'index#reject#{chat_id}#{message.id}#{message.from_user.id}'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await bot.send_message(
        LOG_CHANNEL,
        f'#IndexRequest\n\nBy : {message.from_user.mention} (<code>{message.from_user.id}</code>)\nChat ID/ Username - <code> {chat_id}</code>\nLast Message ID - <code>{last_msg_id}</code>\nInviteLink - {link}',
        reply_markup=reply_markup
    )
    await message.reply('ThankYou For the Contribution, Wait For My Moderators to verify the files.')


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
            
            # 🚀 1. FIXED TOTAL BATCH COUNT RANGE CALCULATIONS ✨
            # Prevents looping over infinite ranges or hitting deep FloodWait freezes
            total_range_limit = max(1, (int(lst_msg_id) - int(temp.CURRENT)) + 1)
            
            # 🚀 2. NAMED ARGUMENTS INTERFACE ALIGNMENT ✨
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
                
                # 🚀 3. FIXED MONGO COLLECTION VALIDATION PIPELINE ✨
                # Bypasses the broken umongo check wrapper and queries by direct unique binary ID hashes
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
