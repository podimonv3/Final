import os
import logging
import random
import sys
import asyncio
import io  # ലോഗ് ഫയൽ (Text File) ഇൻ-മെമ്മറി ആയി നിർമ്മിക്കാൻ
from database.requests_db import get_all_missing_movies  # നമ്മൾ ഉണ്ടാക്കിയ പുതിയ DB ഫങ്ക്ഷൻ
from Script import script
from pyrogram import Client, filters, enums
from pyrogram.errors import ChatAdminRequired, FloodWait, MessageDeleteForbidden
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from asyncio import sleep
from pyrogram.enums import ChatType
from database.ia_filterdb import Media, Mediaa, get_file_details, unpack_new_file_id, delete_files_below_threshold
from database.users_chats_db import db
from info import CHANNELS, ADMINS, REQ_CHANNEL1, REQ_CHANNEL2, LOG_CHANNEL, PICS, BATCH_FILE_CAPTION, CUSTOM_FILE_CAPTION, PROTECT_CONTENT, DATABASE_URI, DATABASE_NAME
from utils import get_settings, get_size, is_subscribed, is_requested_one, is_requested_two, save_group_settings, temp, check_loop_sub, check_loop_sub1, check_loop_sub2
from database.connections_mdb import active_connection
from plugins.pm_filter import auto_filter
import re
import json
import base64
import pymongo
logger = logging.getLogger(__name__)

from dotenv import load_dotenv

load_dotenv("./dynamic.env", override=True, encoding="utf-8")

BATCH_FILES = {}
DS_REACT = ["⚡"]

should_run_check_loop_sub = False
should_run_check_loop_sub1 = False

inclient = pymongo.MongoClient(DATABASE_URI)
indb = inclient[DATABASE_NAME]
incol = indb['auto_del']
infile = indb['file_reply_text']
restarti = indb['restart']


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



@Client.on_message(filters.command("start") & filters.private)
async def start(client, message):
    if len(message.command) != 2:
        try:
            if not await db.is_user_exist(message.from_user.id):
                await db.add_user(message.from_user.id, message.from_user.first_name)
        except Exception:
            pass

        btn = [
            [InlineKeyboardButton("👥 Jᴏɪɴ Oᴜʀ Gʀᴏᴜᴘ 👥", url="https://t.me/+eb__Eg3RS2IyZWQ1")],
            [InlineKeyboardButton("📊 Statistics", callback_data="stats"), InlineKeyboardButton("❌ Close", callback_data="close")]
        ]
        caption = script.START_TXT.format(message.from_user.mention)

        try:
            await message.reply_photo(photo="https://files.catbox.moe/egu0ip.jpg", caption=caption, reply_markup=InlineKeyboardMarkup(btn))
        except Exception:
            try:
                await message.reply_text(caption, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
            except Exception:
                pass
        return

    try:
        if not await db.is_user_exist(message.from_user.id):
            await db.add_user(message.from_user.id, message.from_user.first_name)
    except Exception:
        pass

    data = message.command[1]
    try:
        pre, file_id = data.split("_", 1)
    except Exception:
        pre, file_id = "", data

    # ================= PM SEARCH REDIRECTION =================
    if data.startswith("key_"):
        try:
            req_key = data.replace("key_", "")
            # BUTTONS-ൽ നിന്ന് ആ കീ വെച്ച് ഒറിജിനൽ സിനിമയുടെ പേര് തിരിച്ചെടുക്കുന്നു
            from plugins.pm_filter import BUTTONS, auto_filter
            query = BUTTONS.get(req_key)
            
            if not query:
                # ⚡ സുരക്ഷാ മാറ്റം: യൂസർ ബോട്ടിനെ ബ്ലോക്ക് ചെയ്തിട്ടുണ്ടെങ്കിൽ കോഡ് ക്രാഷ് ആകാതിരിക്കാൻ try-except ചേർത്തു
                from pyrogram.errors import UserIsBlocked
                try:
                    await message.reply_text("<b>❌ ഈ സെർച്ചിന്റെ കാലാവധി കഴിഞ്ഞു. ദയവായി ഗ്രൂപ്പിൽ വീണ്ടും സെർച്ച് ചെയ്യുക!</b>")
                except UserIsBlocked:
                    logger.warning(f"User {message.from_user.id} blocked the bot. Cannot send search expired text.")
                except Exception:
                    pass
                return

            from database.ia_filterdb import get_search_results
            files, offset, total_results = await get_search_results(query.lower(), offset=0, filter=True)
            
            if files:
                await auto_filter(client, message, spoll=(query, files, offset, total_results))
            else:
                from pyrogram.errors import UserIsBlocked
                try:
                    await message.reply_text("<b>❌ ꜰɪʟᴇs ɴᴏᴛ ꜰᴏᴜɴᴅ ɪɴ ᴅᴀᴛᴀʙᴀsᴇ!</b>")
                except UserIsBlocked:
                    logger.warning(f"User {message.from_user.id} blocked the bot. Cannot send files not found text.")
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
            # getfile- ഒഴിവാക്കി ബാക്കി എല്ലാ ഹൈഫനുകളെയും തിരികെ സ്പെയ്സ് ആക്കുന്നു
            query = data.replace("getfile-", "").replace("-", " ")
            
            from database.ia_filterdb import get_search_results
            files, offset, total_results = await get_search_results(query.lower(), offset=0, filter=True)
            
            if files:
                # PM-ൽ ഫയലുകൾ ഇൻസ്റ്റന്റ് ആയി ബട്ടണുകളായി ലിസ്റ്റ് ചെയ്യുന്നു
                await auto_filter(client, message, spoll=(query, files, offset, total_results))
            else:
                # ഫയലുകൾ ഇല്ലെങ്കിൽ ബോട്ട് മിസ്സിംഗ് ലിസ്റ്റിലേക്ക് സേവ് ചെയ്ത് സ്പെൽചെക്ക് കാണിക്കും
                message.text = query
                await auto_filter(client, message)
            return
        except Exception as e:
            logger.exception(e)
            return



        

    # ================= FORCE SUB CHANNEL 1 =================
    if REQ_CHANNEL1 and not await is_requested_one(client, message):
        btn = [[InlineKeyboardButton("📢 Join Channel 1", url=client.req_link1)]]
        join_msg = await message.reply_text(
            script.JOIN_TXT,
            reply_markup=InlineKeyboardMarkup(btn)
        )

        if await check_loop_sub1(client, message):
            try:
                await join_msg.delete()
            except Exception:
                pass
        else:
            return

    # ================= FORCE SUB CHANNEL 2 =================
    if REQ_CHANNEL2 and not await is_requested_two(client, message):
        btn = [[InlineKeyboardButton("📢 Join Channel 2", url=client.req_link2)]]
        join_msg = await message.reply_text(
            script.JOIN_TXT,
            reply_markup=InlineKeyboardMarkup(btn)
        )

        if await check_loop_sub2(client, message):
            try:
                await join_msg.delete()
            except Exception:
                pass
        else:
            return

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
        btn = [
            [InlineKeyboardButton("👥 Jᴏɪɴ Oᴜʀ Gʀᴏᴜᴘ 👥", url="https://t.me/+eb__Eg3RS2IyZWQ1")],
            [InlineKeyboardButton("❌ Close", callback_data="close")]
        ]
        try:
            await message.reply_text(                
                text=script.START_TXT.format(message.from_user.mention),
                reply_markup=InlineKeyboardMarkup(btn)
            )
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
        await msg.edit('This is not a supported file format')
        return
    
    file_id, file_ref = unpack_new_file_id(media.file_id)

    # Check if the file exists in Media collection
    result_media = await Media.collection.find_one({'_id': file_id})

    # Check if the file exists in Mediaa collection
    result_mediaa = await Mediaa.collection.find_one({'_id': file_id})   

    if result_media and result_mediaa:
        await Media.collection.delete_one({'_id': file_id})
        await Mediaa.collection.delete_one({'_id': file_id})
        
    if result_media:
        # Delete from Media collection
        await Media.collection.delete_one({'_id': file_id})
    elif result_mediaa:
        # Delete from Mediaa collection
        await Mediaa.collection.delete_one({'_id': file_id})
    else:
        # File not found in both collections
        await msg.edit('File not found in the database')
        return

    await msg.edit('File is successfully deleted from the database')


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
async def delete_all_index_confirm(bot, message):
    await Media.collection.drop()
    await Mediaa.collection.drop()
    await message.answer('Piracy Is Crime')
    await message.message.edit('Succesfully Deleted All The Indexed Files.')



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

@Client.on_message(filters.command("deletefiles") & filters.user(ADMINS))
async def deletemultiplefiles(bot, message):
    chat_type = message.chat.type
    if chat_type != enums.ChatType.PRIVATE:
        return await message.reply_text(f"<b>Hᴇʏ {message.from_user.mention}, Tʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴡᴏɴ'ᴛ ᴡᴏʀᴋ ɪɴ ɢʀᴏᴜᴘs. Iᴛ ᴏɴʟʏ ᴡᴏʀᴋs ᴏɴ ᴍʏ PM!</b>")
    else:
        pass
    try:
        keyword = message.text.split(" ", 1)[1]
    except:
        return await message.reply_text(f"<b>Hᴇʏ {message.from_user.mention}, Gɪᴠᴇ ᴍᴇ ᴀ ᴋᴇʏᴡᴏʀᴅ ᴀʟᴏɴɢ ᴡɪᴛʜ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ᴅᴇʟᴇᴛᴇ ғɪʟᴇs.</b>")
    btn = [[
       InlineKeyboardButton("Yᴇs, Cᴏɴᴛɪɴᴜᴇ !", callback_data=f"killfilesdq#{keyword}")
       ],[
       InlineKeyboardButton("Nᴏ, Aʙᴏʀᴛ ᴏᴘᴇʀᴀᴛɪᴏɴ !", callback_data="close_data")
    ]]
    await message.reply_text(
        text="<b>Aʀᴇ ʏᴏᴜ sᴜʀᴇ? Dᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ?\n\nNᴏᴛᴇ:- Tʜɪs ᴄᴏᴜʟᴅ ʙᴇ ᴀ ᴅᴇsᴛʀᴜᴄᴛɪᴠᴇ ᴀᴄᴛɪᴏɴ!</b>",
        reply_markup=InlineKeyboardMarkup(btn),
        parse_mode=enums.ParseMode.HTML
    )
    
@Client.on_message(filters.command("deletesmallfiles") & filters.user(ADMINS))
async def process_command(client, message):
    chat_id = message.chat.id
    processing_message = await message.reply_text("<b>Processing: Deleting files...</b>")
    
    total_files_deleted = 0
    batch_size = 250

    while True:
        deleted_files = await delete_files_below_threshold(db, threshold_size_mb=50, batch_size=batch_size)
        
        if deleted_files == 0:
            break

        total_files_deleted += deleted_files

        # Update the message to show progress
        progress_message = f'<b>Processing: Deleted {total_files_deleted} files in {total_files_deleted // batch_size} batches.</b>'
        await processing_message.edit_text(progress_message)
        await asyncio.sleep(3)

    print(f'Total files deleted: {total_files_deleted}')
    await processing_message.edit_text(f'<b>Deletion complete: Deleted {total_files_deleted} files.</b>')

@Client.on_message(filters.command("delete_duplicate") & filters.user(ADMINS))
async def delete_duplicate_files(client, message):
    ok = await message.reply("prosessing...")
    deleted_count = 0
    batch_size = 0
    async def remove_duplicates(collection1, unique_files, ok, deleted_count, batch_size):                        
        async for duplicate_file in collection1.find():
            file_size = duplicate_file["file_size"]
            file_id = duplicate_file["file_id"]
            if file_size in unique_files and unique_files[file_size] != file_id:
                result_media1 = await collection1.find_one({'_id': file_id})                
                if result_media1:
                    await collection1.collection.delete_one({'_id': file_id})               
                    deleted_count += 1                
                    if deleted_count % 100 == 0:
                        batch_size += 1
                        await ok.edit(f'<b>Processing: Deleted {deleted_count} files in {batch_size} batches.</b>')
        return deleted_count, batch_size
    # Get all four collections
    media1_collection = Media
    media2_collection = Mediaa
    
    # Get all files from each collection
    all_files_media1 = await media1_collection.find({}, {"file_id": 1, "file_size": 1}).to_list(length=None)
    all_files_media2 = await media2_collection.find({}, {"file_id": 1, "file_size": 1}).to_list(length=None)
    
    # Combine files from all collections
    all_files = all_files_media1 + all_files_media2

    # Remove duplicate files while keeping one copy
    unique_files = {}
    for file_info in all_files:
        file_id = file_info["file_id"]
        file_size = file_info["file_size"]
        if file_size not in unique_files:
            unique_files[file_size] = file_id

    # Delete duplicate files from each collection
    deleted_count, batch_size = await remove_duplicates(media1_collection, unique_files, ok, deleted_count, batch_size)
    deleted_count = deleted_count
    batch_size = batch_size
    deleted_count, batch_size = await remove_duplicates(media2_collection, unique_files, ok, deleted_count, batch_size)
    deleted_count = deleted_count
    batch_size = batch_size
    
    # Send a final message indicating the total number of duplicates deleted
    await message.reply(f"Deleted {deleted_count} duplicate files. in {batch_size} batches")




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



@Client.on_message(filters.command("clearmissing") & filters.user(ADMINS))
async def clear_missing_requests(bot: Client, message: Message):
    await bot.send_chat_action(chat_id=message.chat.id, action=enums.ChatAction.TYPING)
    
    status_msg = await message.reply_text("<b>ക്ലിയറിംഗ് പ്രോസസ്സ് ആരംഭിക്കുന്നു... ⏳</b>")
    
    try:
        # ⚡ requests_db ഫയലിൽ നിന്നും യഥാർത്ഥ കളക്ഷൻ നേരിട്ട് ഇമ്പോർട്ട് ചെയ്യുന്നു
        from database.requests_db import collection as missing_collection
        
        # ആകെ എത്ര സിനിമകൾ ലിസ്റ്റിൽ ഉണ്ടെന്ന് നോക്കുന്നു
        total_docs = await missing_collection.count_documents({})
        
        if total_docs == 0:
            await status_msg.edit_text("<b>❌ മിസ്സിംഗ് ലിസ്റ്റിൽ നിലവിൽ സിനിമകൾ ഒന്നും തന്നെയില്ല!</b>")
            return
            
        # 🗑️ കളക്ഷനിലെ എല്ലാ ഡാറ്റയും ഡിലീറ്റ് ചെയ്യുന്നു (ഡാറ്റാബേസ് ഇൻഡക്സുകൾ നഷ്ടപ്പെടാതിരിക്കാൻ delete_many ഉപയോഗിക്കുന്നു)
        await missing_collection.delete_many({})
        
        await status_msg.edit_text(f"<b>✅ വിജയകരമായി ഡാറ്റാബേസ് ക്ലിയർ ചെയ്തു!\n\n🗑️ ആകെ ഇല്ലാതാക്കിയ റിക്വസ്റ്റുകൾ: <code>{total_docs}</code></b>")
        
    except Exception as e:
        logger.error(f"Error clearing missing movies database: {e}")
        await status_msg.edit_text(f"<b>❌ ഡാറ്റാബേസ് ക്ലിയർ ചെയ്യുന്നതിൽ പരാജയപ്പെട്ടു!\nError: <code>{e}</code></b>")
