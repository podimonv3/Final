import os
import logging
import random
import sys
import asyncio
import io
import re
import json
import base64
import pymongo
from asyncio import sleep

from Script import script
from pyrogram import Client, filters, enums
from pyrogram.enums import ChatType
from pyrogram.errors import ChatAdminRequired, FloodWait, UserIsBlocked
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
# Fixed: Moved the 403 error catch to its proper class to prevent compiler crashes
from pyrogram.errors.exceptions.bad_request_400 import MessageTooLong, PeerIdInvalid
from pyrogram.errors.exceptions.forbidden_403 import MessageDeleteForbidden

# 🚀 കൺഫ്യൂഷൻ ഒഴിവാക്കാൻ എല്ലാ ഡാറ്റാബേസ് ഇമ്പോർട്ടുകൾക്കും കൃത്യമായ തനത് പേരുകൾ നൽകുന്നു ✨
from database.ia_filterdb import Media, get_file_details, db as clientDB
from database.users_chats_db import db # db മാറ്റി user_db ആക്കി ⚡
from database.connections_mdb import active_connection
from database.requests_db import get_all_missing_movies, clear_all_missing_movies 
from database.postersave import get_db_stats, clear_entire_poster_db

# info ഫയലിൽ നിന്നുള്ള ആവശ്യമായ വേരിയബിളുകൾ ഒന്നിച്ച് ഇമ്പോർട്ട് ചെയ്യുന്നു
from info import (CHANNELS, ADMINS, REQ_CHANNEL1, REQ_CHANNEL2, LOG_CHANNEL, 
                  PICS, BATCH_FILE_CAPTION, CUSTOM_FILE_CAPTION, PROTECT_CONTENT, 
                  DATABASE_URI, DATABASE_NAME)

from utils import (get_settings, get_size, is_subscribed, is_requested_one, 
                   is_requested_two, save_group_settings, temp, check_loop_sub, 
                   check_loop_sub1, check_loop_sub2)
from plugins.pm_filter import auto_filter
from dotenv import load_dotenv

load_dotenv("./dynamic.env", override=True, encoding="utf-8")

logger = logging.getLogger(__name__)
BATCH_FILES = {}
DS_REACT = ["⚡"]

should_run_check_loop_sub = False
should_run_check_loop_sub1 = False

# 🚀 ഓട്ടോ ഡിലീറ്റ് സെറ്റിങ്സ് ക്ലയന്റ് ഡ്രൈവർ കൃത്യമാക്കുന്നു ✨
incol = clientDB['auto_del']
infile = clientDB['file_reply_text']
restarti = clientDB['restart']



async def admin_check(message: Message) -> bool:
    if not message.from_user: return False
    if message.chat.type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]: return False
    if message.from_user.id in [777000, 1087968824]: return True
    client = message._client
    chat_id = message.chat.id
    user_id = message.from_user.id
    check_status = await client.get_chat_member(chat_id=chat_id, user_id=user_id)
    admin_strings = [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR]
    if check_status.status not in admin_strings: return False
    else: return True      
    
def convert_time_to_seconds(time_str):
    if time_str.endswith("s"):
        return int(time_str[:-1])
    elif time_str.endswith("m"):
        return int(time_str[:-1]) * 60
    elif time_str.endswith("h"):
        return int(time_str[:-1]) * 3600
    else:
        return 0

async def send_file(client, query, ident, file_id):
    from pyrogram.errors import UserIsBlocked
    files_ = await get_file_details(file_id)
    if not files_:
        return
    files = files_[0]
    title = files.file_name
    size = get_size(files.file_size)
    f_caption = files.file_name
    if CUSTOM_FILE_CAPTION:
        try:
            f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption, mention=query.from_user.mention)
        except Exception as e:
            logger.exception(e)
            f_caption = f_caption
    if f_caption is None:
        f_caption = f"{title}"

    # 🛠️ കാപ്ഷന്റെ കൂടെ ഓട്ടോ ഡിലീറ്റ് ടെക്സ്റ്റ് Quote ആയി ചേർക്കുന്നു
    final_caption = f"{f_caption}"

    try:
        # 1. Send File with quote caption
        ok = await client.send_cached_media(
            chat_id=query.from_user.id,
            file_id=file_id,
            caption=final_caption,
            parse_mode=enums.ParseMode.HTML,
            protect_content=True if ident == 'checksubp' else False
        )                
    except UserIsBlocked:
        logger.warning(f"യൂസർ ({query.from_user.id}) ബോട്ടിനെ ബ്ലോക്ക് ചെയ്തിരിക്കുന്നു. ഫയൽ അയക്കാൻ കഴിഞ്ഞില്ല.")
    except Exception as e:
        logger.error(f"ഫയൽ അയക്കുന്നതിൽ പരാജയപ്പെട്ടു: {e}")

@Client.on_message(filters.command("start"))
async def start(client, message):
    chat_type = message.chat.type
    user_id = message.from_user.id if message.from_user else None
    # Fixed: Extracted the first_name parameter cleanly to provide a fallback value for user_name
    user_name = message.from_user.first_name if message.from_user else "User"

    if user_id:
        try:
            # Use the non-blocking async method we verified inside database/users_chats_db.py
            if not await db.is_user_exist(user_id):
                await db.add_user(user_id, user_name)                    
        except Exception as e:
            logger.error(f"Error saving user to DB: {e}", exc_info=True)

    if chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        try:
            # Fixed: Changed user_db over to the imported db instance to align with your top imports layout
            if not await db.get_chat(int(message.chat.id)):
                await db.add_chat(chat=int(message.chat.id), title=str(message.chat.title))
        except Exception as e:
            logger.error(f"Error saving group to DB: {e}", exc_info=True)


    if len(message.command) != 2:
        btn = [
            [InlineKeyboardButton("👥 Jᴏɪɴ Oᴜʀ Gʀᴏᴜᴘ 👥", url="https://t.me/+eb__Eg3RS2IyZWQ1")]
        ]
        
        # 🔐 അഡ്മിൻമാർക്ക് മാത്രം കാണിക്കുന്ന പ്രത്യേക ബട്ടണുകൾ
        if message.from_user.id in ADMINS:
            btn.append([InlineKeyboardButton("🛠️ Commands", callback_data="bot_commands"), InlineKeyboardButton("📊 Statistics", callback_data="stats")])
            btn.append([InlineKeyboardButton("🖥️ Server", callback_data="koyeb_stats"), InlineKeyboardButton("❌ Close", callback_data="close")])
        else:
            # 👥 സാധാരണ ഉപയോക്താക്കൾക്ക് ബോട്ട് ഗ്രൂപ്പിലേക്ക് ആഡ് ചെയ്യാനുള്ള ബട്ടണും ക്ലോസ് ബട്ടണും
            btn.append([InlineKeyboardButton("➕ Aᴅᴅ Mᴇ Tᴏ Yᴏᴜʀ Gʀᴏᴜᴘ ➕", url=f"https://t.me/{temp.U_NAME}?startgroup=true")])
            btn.append([InlineKeyboardButton("❌ Close", callback_data="close")])
            
        caption = script.START_TXT.format(message.from_user.mention if message.from_user else "User")
        try:
            await message.reply_photo(photo="https://files.catbox.moe/egu0ip.jpg", caption=caption, reply_markup=InlineKeyboardMarkup(btn))
        except Exception:
            try:
                await message.reply_text(caption, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
            except Exception:
                pass
        return


    # കമാൻഡിനൊപ്പം ഫയൽ ഐഡിയോ റീഡയറക്ഷൻ കീയോ വന്നിട്ടുണ്ടെങ്കിൽ (Deep Linking)
    data = message.command[1]
    try:
        pre, file_id = data.split("_", 1)
    except Exception:
        pre, file_id = "", data

    # ================= PM SEARCH REDIRECTION =================
    if data.startswith("key_"):
        try:
            req_key = data.replace("key_", "")
            from plugins.pm_filter import BUTTONS, auto_filter
            button_data = BUTTONS.get(req_key)
            
            if not button_data:
                try:
                    await message.reply_text("<b>🚫 Expired Please Search Again In Group\n❌ ഈ സെർച്ചിന്റെ കാലാവധി കഴിഞ്ഞു. ദയവായി ഗ്രൂപ്പിൽ വീണ്ടും സെർച്ച് ചെയ്യുക!</b>")
                except Exception:
                    pass
                return

            if isinstance(button_data, dict):
                query = button_data.get("query")
            else:
                query = button_data

            if not query:
                try:
                    await message.reply_text("<b>🚫 Expired Please Search Again In Group\n❌ ഈ സെർച്ചിന്റെ കാലാവധി കഴിഞ്ഞു. ദയവായി ഗ്രൂപ്പിൽ വീണ്ടും സെർച്ച് ചെയ്യുക!</b>")
                except Exception:
                    pass
                return

            from database.ia_filterdb import get_search_results
            files, offset, total_results = await get_search_results(query.lower(), offset=0, filter=True)
            
            if files:
                await auto_filter(client, message, spoll=(query, files, offset, total_results))
            else:
                try:
                    await message.reply_text("<b>❌ ꜰɪʟᴇs ɴᴏᴛ ꜰᴏᴜ่นᴅ ɪɴ ᴅᴀᴛᴀʙᴀsᴇ!</b>")
                except Exception:
                    pass
            return
        except Exception as e:
            logger.exception(e)
            return

    # ================= DYNAMIC LINK (GETFILE) REDIRECTION =================
    elif data.startswith("getfile-"):
        try:
            from plugins.pm_filter import auto_filter
            query = data.replace("getfile-", "").replace("-", " ")
            
            from database.ia_filterdb import get_search_results
            files, offset, total_results = await get_search_results(query.lower(), offset=0, filter=True)
            
            if files:
                await auto_filter(client, message, spoll=(query, files, offset, total_results))
            else:
                message.text = query
                await auto_filter(client, message)
            return
        except Exception as e:
            logger.exception(e)
            return

    # ================= FORCE SUB CHANNELS =================
    if REQ_CHANNEL1 and not await is_requested_one(client, message):
        btn = [[InlineKeyboardButton("📢 Join Channel 1", url=client.req_link1)]]
        join_msg = await message.reply_text(script.JOIN_TXT, reply_markup=InlineKeyboardMarkup(btn))
        if await check_loop_sub1(client, message):
            try: await join_msg.delete()
            except Exception: pass
        else: return

    if REQ_CHANNEL2 and not await is_requested_two(client, message):
        btn = [[InlineKeyboardButton("📢 Join Channel 2", url=client.req_link2)]]
        join_msg = await message.reply_text(script.JOIN_TXT, reply_markup=InlineKeyboardMarkup(btn))
        if await check_loop_sub2(client, message):
            try: await join_msg.delete()
            except Exception: pass
        else: return

    # ================= GETFILE =================
    if data.startswith("getfile"):
        try:
            message.text = data.split("-", 1)[1].replace("-", " ")
            await auto_filter(client, message, spoll=False)
        except Exception as e:
            logger.exception(e)
        return
    
    # ================= SPECIAL COMMANDS =================
    if data in ["subscribe", "error", "okay", "help"]:
        # 👥 എല്ലാ യൂസർമാർക്കും കാണാവുന്ന ഗ്രൂപ്പ് ബട്ടൺ
        btn = [
            [InlineKeyboardButton("👥 Jᴏɪɴ Oᴜʀ Gʀᴏᴜᴘ 👥", url="https://t.me/+eb__Eg3RS2IyZWQ1")]
        ]
        
        # 🔐 അഡ്മിൻമാർക്ക് മാത്രം കാണിക്കുന്ന പ്രത്യേക ബട്ടണുകൾ
        if message.from_user and message.from_user.id in ADMINS:
            btn.append([InlineKeyboardButton("🛠️ Commands", callback_data="bot_commands"), InlineKeyboardButton("📊 Statistics", callback_data="stats")])
            btn.append([InlineKeyboardButton("🖥️ Server", callback_data="koyeb_stats"), InlineKeyboardButton("❌ Close", callback_data="close")])
        else:
            # 👥 സാധാരണ ഉപയോക്താക്കൾക്ക് ബോട്ട് ഗ്രൂപ്പിലേക്ക് ആഡ് ചെയ്യാനുള്ള ബട്ടണും ക്ലോസ് ബട്ടണും
            btn.append([InlineKeyboardButton("➕ Aᴅᴅ Mᴇ Tᴏ Yᴏᴜʀ Gʀᴏᴜᴘ ➕", url=f"https://t.me{temp.U_NAME}?startgroup=true")])
            btn.append([InlineKeyboardButton("❌ Close", callback_data="close")])
            
        try:
            await message.reply_text(text=script.START_TXT.format(message.from_user.mention if message.from_user else "User"), reply_markup=InlineKeyboardMarkup(btn))
        except Exception as e:
            logger.exception(e)
        return


    # ================= BATCH =================
    if data.split("-", 1)[0] == "BATCH":
        try:
            sts = await message.reply("Please wait")
            file_id = data.split("-", 1)[1]
            msgs = BATCH_FILES.get(file_id)

            if not msgs:
                file = await client.download_media(file_id)
                try:
                    with open(file) as file_data:
                        msgs = json.loads(file_data.read())
                except Exception:
                    try:
                        await sts.edit("FAILED")
                    except Exception:
                        pass
                    await client.send_message(LOG_CHANNEL, "UNABLE TO OPEN FILE.")
                    return
                os.remove(file)
                BATCH_FILES[file_id] = msgs

            # ❌ ഇവിടെ ഉണ്ടായിരുന്ന batch_msg_ids ലിസ്റ്റ് ഒഴിവാക്കി

            for msg in msgs:
                title = msg.get("title")
                size = get_size(int(msg.get("size", 0)))
                f_caption = msg.get("caption", "")

                if BATCH_FILE_CAPTION:
                    try:
                        f_caption = BATCH_FILE_CAPTION.format(
                            file_name="" if title is None else title,
                            file_size="" if size is None else size,
                            file_caption="" if f_caption is None else f_caption
                        )
                    except Exception as e:
                        logger.exception(e)

                if f_caption is None:
                    f_caption = f"{title}"

                final_caption = f"{f_caption}"

                try:
                    await client.send_cached_media(
                        chat_id=message.from_user.id,
                        file_id=msg.get("file_id"),
                        caption=final_caption,
                        parse_mode=enums.ParseMode.HTML,
                        protect_content=msg.get("protect", False)
                    )

                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    try:
                        await client.send_cached_media(
                            chat_id=message.from_user.id,
                            file_id=msg.get("file_id"),
                            caption=final_caption,
                            parse_mode=enums.ParseMode.HTML,
                            protect_content=msg.get("protect", False)
                        )
                    except Exception:
                        continue

                except UserIsBlocked:
                    return

                except Exception as e:
                    logger.warning(e, exc_info=True)
                    continue

                await asyncio.sleep(1)

            # ❌ ഓട്ടോ ഡിലീറ്റ് ചെയ്യുന്ന ഭാഗം (asyncio.create_task) ഇവിടെ നിന്നും പൂർണ്ണമായി ഒഴിവാക്കി.

            try:
                await sts.delete()
            except Exception:
                pass

        except Exception as e:
            logger.exception(e)

        return


    # ================= DSTORE =================
    if data.split("-", 1)[0] == "DSTORE":
        try:
            sts = await message.reply("Please wait")
            b_string = data.split("-", 1)[1]
            decoded = base64.urlsafe_b64decode(
                b_string + "=" * (-len(b_string) % 4)
            ).decode("ascii")

            try:
                f_msg_id, l_msg_id, f_chat_id, protect = decoded.split("_", 3)
            except Exception:
                f_msg_id, l_msg_id, f_chat_id = decoded.split("_", 2)
                protect = "/pbatch" if PROTECT_CONTENT else "batch"

            # ❌ ഇവിടെ ഉണ്ടായിരുന്ന dstore_msg_ids ലിസ്റ്റ് ഒഴിവാക്കി

            async for msg in client.iter_messages(
                int(f_chat_id), int(l_msg_id), int(f_msg_id)
            ):
                try:
                    if msg.media:
                        media_type = msg.media.value if hasattr(msg.media, "value") else str(msg.media)
                        media = getattr(msg, media_type, None)

                        if not media:
                            continue

                        if BATCH_FILE_CAPTION:
                            try:
                                f_caption = BATCH_FILE_CAPTION.format(
                                    file_name=getattr(media, "file_name", ""),
                                    file_size=getattr(media, "file_size", ""),
                                    file_caption=getattr(msg, "caption", "")
                                )
                            except Exception:
                                f_caption = getattr(msg, "caption", "")
                        else:
                            f_caption = getattr(
                                msg, "caption",
                                getattr(media, "file_name", "")
                            )

                        # ❌ ക്യാപ്ഷന്റെ കൂടെയുണ്ടായിരുന്ന \n\n{AUTO_DEL_TEXT} ഒഴിവാക്കി
                        await msg.copy(
                            message.chat.id,
                            caption=f"{f_caption}",
                            parse_mode=enums.ParseMode.HTML,
                            protect_content=protect == "/pbatch"
                        )
                    elif not msg.empty:
                        await msg.copy(
                            message.chat.id,
                            protect_content=protect == "/pbatch"
                        )
                    else:
                        continue

                except FloodWait as e:
                    await asyncio.sleep(e.x)
                except UserIsBlocked:
                    return
                except Exception as e:
                    logger.exception(e)

                await asyncio.sleep(1)

            # ❌ ഓട്ടോ ഡിലീറ്റ് ചെയ്യുന്ന ഭാഗം (asyncio.create_task) ഇവിടെ നിന്നും പൂർണ്ണമായി ഒഴിവാക്കി.

            try:
                await sts.delete()
            except Exception:
                pass

        except Exception as e:
            logger.exception(e)

        return

    # ================= NORMAL FILE =================
    try:
        files_ = await get_file_details(file_id)
    except Exception as e:
        logger.exception(e)
        files_ = None

    if not files_:
        try:
            pre, file_id = base64.urlsafe_b64decode(
                data + "=" * (-len(data) % 4)
            ).decode("ascii").split("_", 1)

            msg = await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=file_id,
                protect_content=pre == "filep"
            )

            file = getattr(
                msg,
                msg.media.value if hasattr(msg.media, "value") else str(msg.media),
                None
            ) if msg.media else None

            if not file:
                return await message.reply("No such file exist.")

            title = file.file_name
            size = get_size(file.file_size)
            f_caption = f"<code>{title}</code>"

            if CUSTOM_FILE_CAPTION:
                try:
                    f_caption = CUSTOM_FILE_CAPTION.format(
                        file_name="" if title is None else title,
                        file_size="" if size is None else size,
                        file_caption=f_caption,
                        mention=message.from_user.mention
                    )
                except Exception:
                    return

            # ❌ ആദ്യത്തെ സെക്ഷനിലെ ക്യാപ്ഷനിൽ നിന്നും AUTO_DEL_TEXT ഒഴിവാക്കി
            await msg.edit_caption(
                f"{f_caption}",
                parse_mode=enums.ParseMode.HTML
            )
            return

        except UserIsBlocked:
            return
        except Exception:
            return await message.reply("No such file exist.")

    files = files_[0]
    title = files.file_name
    size = get_size(files.file_size)
    f_caption = files.caption

    if CUSTOM_FILE_CAPTION:
        try:
            f_caption = CUSTOM_FILE_CAPTION.format(
                file_name="" if title is None else title,
                file_size="" if size is None else size,
                file_caption="" if f_caption is None else f_caption,
                mention=message.from_user.mention
            )
        except Exception as e:
            logger.exception(e)

    if f_caption is None:
        f_caption = f"{title}"

    try:
        # ❌ രണ്ടാമത്തെ സെക്ഷനിലെ ക്യാപ്ഷനിൽ നിന്നും AUTO_DEL_TEXT ഒഴിവാക്കി
        await client.send_cached_media(
            chat_id=message.from_user.id,
            file_id=file_id,
            caption=f"{f_caption}",
            parse_mode=enums.ParseMode.HTML,
            protect_content=pre == "filep"
        )

        # ❌ രണ്ടാമത്തെ സെക്ഷനിലെ ഓട്ടോ ഡിലീറ്റ് ടാസ്ക് ഒഴിവാക്കി

    except UserIsBlocked:
        logger.warning("User %s blocked the bot", message.from_user.id)
    except Exception as e:
        logger.error(e, exc_info=True)

   
    
    
@Client.on_message(filters.command('channel') & filters.user(ADMINS))
async def channel_info(bot, message):
           
    """Send basic information of channel"""
    if isinstance(CHANNELS, (int, str)):
        channels = [CHANNELS]
    elif isinstance(CHANNELS, list):
        channels = CHANNELS
    else:
        raise ValueError("Unexpected type of CHANNELS")

    text = '📑 **Indexed channels/groups**\n'
    for channel in channels:
        chat = await bot.get_chat(channel)
        if chat.username:
            text += '\n@' + chat.username
        else:
            text += '\n' + chat.title or chat.first_name

    text += f'\n\n**Total:** {len(CHANNELS)}'

    if len(text) < 4096:
        await message.reply(text)
    else:
        file = 'Indexed channels.txt'
        with open(file, 'w') as f:
            f.write(text)
        await message.reply_document(file)
        os.remove(file)


@Client.on_message(filters.command('logs') & filters.user(ADMINS))
async def log_file(bot, message):
    """Send log file"""
    try:
        await message.reply_document('TelegramBot.log')
    except Exception as e:
        await message.reply(str(e))

@Client.on_message(filters.command('delete') & filters.user(ADMINS))
async def delete(bot, message):
    """Delete file from database"""
    reply = message.reply_to_message
    if reply and reply.media:
        msg = await message.reply("Processing...⏳", quote=True)
    else:
        await message.reply('Reply to the file with /delete that you want to delete', quote=True)
        return

    for file_type in ("document", "video", "audio"):
        media = getattr(reply, file_type, None)
        if media is not None:
            break
    else:
        return await message.reply_text('This is not a supported file format', quote=True)
    
    try:
        file_id, file_ref = unpack_new_file_id(media.file_id)
        # Fixed: Assures strict database lookup syntax parameters are tracked safely
        result_media = await Media.collection.find_one({'_id': file_id})

        if result_media:
            await Media.collection.delete_one({'_id': file_id})
            await message.reply_text('✅ File successfully deleted from the database.', quote=True)
        else:
            await message.reply_text('❌ File not found in the database.', quote=True)
    except Exception as e:
        logger.error(f"Error executing manual file deletion: {e}")
        await message.reply_text(f"❌ Deletion failed: {e}", quote=True)


@Client.on_message(filters.command('deleteall') & filters.user(ADMINS))
async def delete_all_index(bot, message):
    await message.reply_text(
        'This will delete all indexed files.\nDo you want to continue??',
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="YES", callback_data="autofilter_delete"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="CANCEL", callback_data="close_data"
                    )
                ],
            ]
        ),
        quote=True,
    )


@Client.on_callback_query(filters.regex(r'^autofilter_delete'))
# Fixed: Formatted parameters to use correct CallbackQuery contexts to prevent interface block hangs
async def delete_all_index_confirm(bot, query: CallbackQuery):
    await Media.collection.delete_many({})
    await query.answer('Piracy Is Crime', show_alert=True)
    await query.message.edit_text('✅ Succesfully Deleted All The Indexed Files From Database.')



# ====================================================================
# 🧹 ഡാറ്റാബേസിലെ മുഴുവൻ ലോക്ക് സെറ്റിങ്സുകളും ക്ലിയർ ചെയ്യാനുള്ള അഡ്മിൻ കമാൻഡ് ✨
# ====================================================================

# ഫങ്ഷൻ കൃത്യമായി വർക്ക് ചെയ്യാൻ ആവശ്യമായ എല്ലാ പ്രധാന ഒബ്ജക്റ്റുകളും ഇവിടെ നേരിട്ട് ഇമ്പോർട്ട് ചെയ്യുന്നു ⚡

@Client.on_message(filters.command("clear_locks") & filters.user(ADMINS))
async def clear_all_locks_cmd(client: Client, message: Message):
    """ഡാറ്റാബേസിലെ മുഴുവൻ ചാറ്റ് ലോക്ക് വിവരങ്ങളും ഒന്നിച്ച് ഡിലീറ്റ് ചെയ്യാനുള്ള കമാൻഡ് 🧹"""
    msg = await message.reply_text("⏳ ഡാറ്റാബേസിലെ ലോക്ക് സെറ്റിങ്സുകൾ ക്ലിയർ ചെയ്തുകൊണ്ടിരിക്കുന്നു...")
    
    try:
        # 🚀 'locks' കളക്ഷനിലെ മുഴുവൻ ഡോക്യുമെന്റുകളും ഒന്നിച്ച് ഡിലീറ്റ് ചെയ്യുന്നു ✨
        result = await clientDB['locks'].delete_many({})
        
        await msg.edit_text(
            f"✅ <b>വിജയകരമായി ഡാറ്റാബേസിലെ എല്ലാ ലോക്ക് സെറ്റിങ്സുകളും പൂർണ്ണമായി ഡിലീറ്റ് ചെയ്തിരിക്കുന്നു!</b>\n\n"
            f"📊 <b>ആകെ നീക്കം ചെയ്ത ഗ്രൂപ്പുകൾ:</b> <code>{result.deleted_count}</code>\n"
            f"💡 <i>ഇനി മുതൽ എല്ലാ ഗ്രൂപ്പുകളിലും ഡിഫോൾട്ട് ലോക്ക് സെറ്റിങ്സ് ആയിരിക്കും പ്രവർത്തിക്കുക.</i>",
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        await msg.edit_text(f"❌ ലോക്ക് സെറ്റിങ്സുകൾ ക്ലിയർ ചെയ്യുന്നതിൽ പരാജയപ്പെട്ടു!\nഎറർ: <code>{e}</code>", parse_mode=enums.ParseMode.HTML)


@Client.on_message(filters.command('restart') & filters.user(ADMINS))
async def restart(b, m):
    if os.path.exists(".git"):
        os.system("git pull")

    oo = await m.reply_text("Restarting...")
    await oo.delete()
    try:
        os.remove("TelegramBot.txt")
    except:
        pass
    os.execl(sys.executable, sys.executable, "bot.py")


            

@Client.on_message(filters.command("setchat1") & filters.user(ADMINS))
async def add_fsub_chats(bot: Client, update: Message):
    await update.react("🌭")
    chat = update.command[1] if len(update.command) > 1 else None
    if not chat:
        await update.reply_text("Invalid chat id.", quote=True)
        return
    else:
        chat = int(chat)
    await db.add_fsub_chat(chat)

    text = f"Added chat <code>{chat}</code> to the database."
    await update.reply_text(text=text, quote=True, parse_mode=enums.ParseMode.HTML)
    with open("./dynamic.env", "wt+") as f:
        f.write(f"REQ_CHANNEL1={chat}\n")
    restarti.update_one(
        {"_id": "frestart"},
        {"$set": {"restart": "on"}},
        upsert=True
    )
    os.execl(sys.executable, sys.executable, "bot.py")


@Client.on_message(filters.command("delchat1") & filters.user(ADMINS))
async def clear_fsub_chats(bot: Client, update: Message):
    await update.react("👍")
    await db.delete_fsub_chat(chat_id=(await db.get_fsub_chat())['chat_id'])
    await update.reply_text(text="Deleted fsub chat from the database.", quote=True)
    with open("./dynamic.env", "wt+") as f:
        f.write(f"REQ_CHANNEL1=False\n")

    logger.info("Restarting to update REQ_CHANNEL from database...")
    os.execl(sys.executable, sys.executable, "bot.py")
    
@Client.on_message(filters.command("viewchat1") & filters.user(ADMINS))
async def get_fsub_chat(bot: Client, update: Message):
    await update.react("👍")
    chat = await db.get_fsub_chat()
    if not chat:
        await update.reply_text("No fsub chat found in the database.", quote=True)
        return
    else:
        await update.reply_text(f"Fsub chat: <code>{chat['chat_id']}</code>", quote=True, parse_mode=enums.ParseMode.HTML)
        
@Client.on_message(filters.command("setchat2") & filters.user(ADMINS))
async def add_fsub_chats2(bot: Client, update: Message):
    await update.react("🍌")
    chat = update.command[1] if len(update.command) > 1 else None
    if not chat:
        await update.reply_text("Invalid chat id.", quote=True)
        return
    else:
        chat = int(chat)
    await db.add_fsub_chat2(chat)

    text = f"Added chat <code>{chat}</code> to the database."
    await update.reply_text(text=text, quote=True, parse_mode=enums.ParseMode.HTML)
    with open("./dynamic.env", "wt+") as f:
        f.write(f"REQ_CHANNEL2={chat}\n")
    restarti.update_one(
        {"_id": "frestart"},
        {"$set": {"restart": "on"}},
        upsert=True
    )
    os.execl(sys.executable, sys.executable, "bot.py")


@Client.on_message(filters.command("delchat2") & filters.user(ADMINS))
async def clear_fsub_chats2(bot: Client, update: Message):
    await update.react("👍")
    await db.delete_fsub_chat2(chat_id=(await db.get_fsub_chat2())['chat_id'])
    await update.reply_text(text="Deleted fsub chat from the database.", quote=True)
    with open("./dynamic.env", "wt+") as f:
        f.write(f"REQ_CHANNEL2=False\n")

    logger.info("Restarting to update REQ_CHANNEL from database...")
    os.execl(sys.executable, sys.executable, "bot.py")
    
@Client.on_message(filters.command("viewchat2") & filters.user(ADMINS))
async def get_fsub_chat2(bot: Client, update: Message):
    await update.react("👍")
    chat = await db.get_fsub_chat2()
    if not chat:
        await update.reply_text("No fsub chat found in the database.", quote=True)
        return
    else:
        await update.reply_text(f"Fsub chat: <code>{chat['chat_id']}</code>", quote=True, parse_mode=enums.ParseMode.HTML)

    


# 🚀 requests_db ഫയലിൽ നിന്നുള്ള ഫങ്ഷൻ ഇവിടെ ഇമ്പോർട്ട് ചെയ്യുന്നു ✨

@Client.on_message(filters.command("missing") & filters.user(ADMINS))
async def get_missing_requests(bot: Client, message):
    await bot.send_chat_action(chat_id=message.chat.id, action=enums.ChatAction.TYPING)
    
    # ഡാറ്റാബേസിൽ നിന്നും സിനിമകളും കൗണ്ടുകളും എടുക്കുന്നു
    missing_movies = await get_all_missing_movies()
    
    if not missing_movies:
        return await message.reply_text("<b>❌ നിലവിൽ ഡാറ്റാബേസിൽ കിട്ടാത്ത സിനിമകളുടെ ലിസ്റ്റ് ഒന്നും തന്നെയില്ല!</b>")
    
    # ലോഗ് ഫയലിനായുള്ള ടെക്സ്റ്റ് ഫോർമാറ്റ് ചെയ്യുന്നു
    log_content = " Can_Urvashi Theaters™️ - Missing Movie Requests (With Count) \n"
    log_content += f"Total Unique Requests: {len(missing_movies)}\n"
    log_content += "="*65 + "\n\n"
    
    # Alphabetical order-ൽ കൗണ്ട് സഹിതം ലിസ്റ്റ് ചെയ്യുന്നു
    for index, movie in enumerate(missing_movies, start=1):
        log_content += f"{index}. {movie['name'].ljust(40)} | Searches: {movie['count']} times\n"
        
    # ടെക്സ്റ്റ് ഡാറ്റയെ ഒരു ഇൻ-മെമ്മറി ഫയൽ (BytesIO) ആക്കി മാറ്റുന്നു
    file_buffer = io.BytesIO(log_content.encode('utf-8'))
    file_buffer.name = "missing_movies_log.txt"
    
    # അഡ്മിന് ലോഗ് ഫയൽ അയച്ചു കൊടുക്കുന്നു
    await bot.send_document(
        chat_id=message.chat.id,
        document=file_buffer,
        caption=f"<b>📊 <u>Missing Movies Report</u>\n\nTotal unique requests: <code>{len(missing_movies)}</code>\n\n(സിനിമകളുടെ പേരും അവ എത്ര തവണ തിരഞ്ഞു എന്ന വിവരവും ഫയലിൽ ലഭ്യമാണ്)</b>",
        parse_mode=enums.ParseMode.HTML
    )




# requests_db ഫയലിൽ നിന്ന് നമ്മൾ ഉണ്ടാക്കിയ പുതിയ ഫങ്ഷൻ ഇമ്പോർട്ട് ചെയ്യുന്നു

@Client.on_message(filters.command("clear_missing") & filters.user(ADMINS))
async def clear_missing_requests_cmd(client: Client, message: Message):
    """ഡാറ്റാബേസിലെ മുഴുവൻ മൂവി റിക്വസ്റ്റുകളും ഒന്നിച്ച് ഡിലീറ്റ് ചെയ്യാനുള്ള അഡ്മിൻ കമാൻഡ് 🧹"""
    msg = await message.reply_text("⏳ ഡാറ്റാബേസ് ക്ലിയർ ചെയ്തുകൊണ്ടിരിക്കുന്നു...")
    
    # നമ്മൾ requests_db ഫയലിൽ ഉണ്ടാക്കിയ ഫങ്ഷൻ ഇവിടെ വിളിക്കുന്നു
    success = await clear_all_missing_movies()
    
    if success:
        await msg.edit_text("✅ **വിജയകരമായി ഡാറ്റാബേസിലെ എല്ലാ സിനിമാ റിക്വസ്റ്റുകളും പൂർണ്ണമായി ഡിലീറ്റ് ചെയ്തിരിക്കുന്നു!**")
    else:
        await msg.edit_text("❌ ഡാറ്റാബേസ് ക്ലിയർ ചെയ്യുന്നതിൽ ചെറിയൊരു പ്രശ്നം ഉണ്ടായി!")





@Client.on_message(filters.command("dbstatus") & filters.private)
async def show_database_status(client, message):
    # 🔐 സെക്യൂരിറ്റി ചെക്ക്: മെസ്സേജ് അയച്ച ആൾ അഡ്മിൻ ലിസ്റ്റിൽ ഉണ്ടോ എന്ന് നോക്കുന്നു
    if message.from_user.id not in ADMINS:
        await message.reply_text("❌ <b>Access Denied:</b> This command is restricted to Bot Admins only!")
        return

    # അഡ്മിൻ ആണെങ്കിൽ മാത്രം വിവരങ്ങൾ ശേഖരിക്കുന്നു
    status_msg = await message.reply_text("<code>Fetching Database Stats... 📊</code>")
    
    stats = await get_db_stats()
    
    if stats:
        text = (
            "📊 <b><u>ᴍᴏᴠɪᴇ ᴘᴏsᴛᴇʀ ᴅʙ sᴛᴀᴛᴜs</u></b>\n\n"
            f"📂 <b>ᴛᴏᴛᴀʟ ᴘᴏsᴛᴇʀs ᴄᴀᴄʜᴇᴅ:</b> <code>{stats['total']}</code>\n"
            f"💾 <b>ᴜsᴇᴅ sᴘᴀᴄᴇ (sᴛᴏʀᴀɢᴇ):</b> <code>{stats['used']} MB</code>\n"
            f"🆓 <b>ᴇsᴛɪᴍᴀᴛᴇᴅ ғʀᴇᴇ sᴘᴀᴄᴇ:</b> <code>{stats['free']} MB</code>\n\n"
            "⚡ <i>Cache is optimized and running active!</i>"
        )
        await status_msg.edit_text(text)
    else:
        await status_msg.edit_text("❌ Failed to fetch database statistics.")


@Client.on_message(filters.command("clearposterdb") & filters.private)
async def clear_poster_database(client, message):
    # 🔐 സെക്യൂരിറ്റി ചെക്ക്: മെസ്സേജ് അയച്ച ആൾ അഡ്മിൻ ലിസ്റ്റിൽ ഉണ്ടോ എന്ന് നോക്കുന്നു
    if message.from_user.id not in ADMINS:
        await message.reply_text("❌ <b>Access Denied:</b> This command is restricted to Bot Admins only!")
        return

    # ക്ലിയറിങ് പ്രോസസ്സ് സ്റ്റാർട്ട് ചെയ്യുന്നു
    status_msg = await message.reply_text("<code>Clearing all cached movie posters from database... 🧹</code>")
    
    success = await clear_entire_poster_db()
    
    if success:
        await status_msg.edit_text("✅ <b>sᴜᴄᴄᴇss:</b> The movie poster database has been completely cleared!")
    else:
        await status_msg.edit_text("❌ Failed to clear the database due to a database restriction.")
