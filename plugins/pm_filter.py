import asyncio
lock = asyncio.Lock()
import re
import ast
import math
import ast  # eval-ന് പകരം സുരക്ഷിതമായി സ്ട്രിങ് ലിസ്റ്റ് ആക്കാൻ
import emoji  # ഇമോജികൾ നീക്കം ചെയ്യാൻ
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid, QueryIdInvalid, MessageIdInvalid
from Script import script
import pyrogram
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, \
    make_inactive
from info import ADMINS, REQ_CHANNEL1, REQ_CHANNEL2, AUTH_USERS, CUSTOM_FILE_CAPTION, AUTH_GROUPS, P_TTI_SHOW_OFF, \
    SINGLE_BUTTON, SPELL_CHECK_REPLY, LOG_CHANNEL, SPELL_IMG
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, filters, enums
from utils import get_size, is_subscribed, temp, get_settings, save_group_settings, is_requested_one, is_requested_two, get_any_movie_poster, get_poster
from database.users_chats_db import db
from database.ia_filterdb import Media, Mediaa, get_bad_files, get_file_details, get_search_results, db as clientDB, db1 as clientDB2, db2 as clientDB3
from database.filters_mdb import (
    del_all,
    find_filter,
    get_filters,
)
from database.gfilters_mdb import find_gfilter, get_gfilters
import logging
from database.requests_db import save_missing_movie, get_all_missing_movies
import io
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


def _trim_dict(d: dict, max_size: int = 250):  # ഇവിടെ 1000 ആണ് DEFAULT വാല്യൂ
    """Remove oldest 20% of entries when dict exceeds max size."""
    if len(d) > max_size:
        keys_to_remove = list(d.keys())[:len(d) // 5]
        for k in keys_to_remove:
            d.pop(k, None)
            

BUTTONS = {}
SPELL_CHECK = {}


@Client.on_message(filters.private & (filters.text | filters.photo | filters.video | filters.sticker) & filters.incoming)
async def pm_text(bot: Client, message):
    user_id = message.from_user.id
    user = message.from_user.first_name or "User"

    if message.text and (message.text.startswith("/") or message.text.startswith("#")): return
    if user_id in ADMINS: return

    if message.text:
        text_to_check = message.text.strip()
        if not re.search(r'\b(19\d{2}|20[0-2]\d)\b$', text_to_check):
            await bot.send_chat_action(chat_id=message.chat.id, action=enums.ChatAction.TYPING)
            await asyncio.sleep(0.5)
            # തെറ്റായ ഫോർമാറ്റ് ആണെങ്കിൽ കാണിക്കുന്ന മെസ്സേജ് (ഇനി ഇത് തനിയെ ഡിലീറ്റ് ആകില്ല)
            await message.reply_text(
                text=f"<b>❌ Wrong Format / തെറ്റായ ഫോർമാറ്റ്!\n\nPlease send your request in this format:\n<code>Movie Name + Year</code>\n\nExample:\n<code>Kuruthi 2019</code>\n\n💡 സിനിമയുടെ പേരിനൊപ്പം വർഷം കൂടി ടൈപ്പ് ചെയ്ത് അയക്കുക.</b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚸 MUST READ 🚸", url="http://telegra.ph/Request-%E0%B4%85%E0%B4%AF%E0%B4%95%E0%B4%95-%E0%B4%AE%E0%B4%A8%E0%B4%A8-%E0%B4%B5%E0%B4%AF%E0%B4%95%E0%B4%95%E0%B4%A3%E0%B4%9D%E0%B4%A8%E0%B4%A4-08-19")]])
            )
            return

    content = message.text or message.caption or (f"Sent a Sticker [{message.sticker.emoji}]" if message.sticker else "Media File")
    files_found = False

    if message.text:
        search_query = message.text.strip()
        files, offset, total_results = await get_search_results(search_query.lower(), offset=0, filter=True)

        if files:
            files_found = True
            await bot.send_chat_action(chat_id=message.chat.id, action=enums.ChatAction.TYPING)
            settings = await get_settings(message.chat.id)
            pre = 'filep' if settings['file_secure'] else 'file'
            key = f"{message.chat.id}-{message.id}"
            BUTTONS[key] = search_query
            
            # get_filter_menu_buttons ഒഴിവാക്കി ലിസ്റ്റ് ബ്ലാങ്ക് (Empty) ആക്കി മാറ്റി
            btn = []

            if settings["button"]:
                for file in files[:10]: btn.append([InlineKeyboardButton(text=f"{get_size(file.file_size)}➪{file.file_name}", callback_data=f'{pre}#{file.file_id}')])
            else:
                for file in files[:10]: btn.append([InlineKeyboardButton(text=file.file_name, callback_data=f'{pre}#{file.file_id}'), InlineKeyboardButton(text=get_size(file.file_size), callback_data=f'{pre}#{file.file_id}')])

            if total_results > 10:
                btn.append([InlineKeyboardButton(text=f"   𝟷 / {math.ceil(int(total_results) / 10)}", callback_data="pages"), InlineKeyboardButton(text="ɴᴇxᴛ", callback_data=f"next_{user_id}_{key}_10")])

            cap = "<b><i><u>© can_Urvashi Theaters™️</u></i></b>"
            await message.reply_text(text=cap, reply_markup=InlineKeyboardMarkup(btn))

    if not files_found:
        await bot.send_chat_action(chat_id=message.chat.id, action=enums.ChatAction.TYPING)
        await asyncio.sleep(0.5)

        # സിനിമ കിട്ടിയില്ലെങ്കിൽ സബ്മിറ്റ് ആയി എന്ന് കാണിക്കുന്ന മെസ്സേജ് (ഇതും ഇനി തനിയെ ഡിലീറ്റ് ആകില്ല)
        await message.reply_text(
            text="<b>Your Request Has Been Submitted✅\n\nOTT Available Add Files With In 24Hrs.. Please Wait\n\nനിങ്ങളുടെ request അഡ്മിൻ അയച്ചിട്ടുണ്ട് ഫയൽസ് ഉണ്ടെങ്കിൽ 24മണിക്കൂറിനുള്ളിൽ ആഡ് ചെയ്യുന്നതാണ്</b>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚫 ANY ERROR REPORT 🚫 ", url="https://t.me/Adhityan_edavattom")],
                [InlineKeyboardButton("🚸 MUST READ 🚸", url="http://telegra.ph/Request-%E0%B4%85%E0%B4%AF%E0%B4%95%E0%B4%95-%E0%B4%AE%E0%B4%A8%E0%B4%A8-%E0%B4%B5%E0%B4%AF%E0%B4%95%E0%B4%95%E0%B4%A3%E0%B4%9D%E0%B4%A8%E0%B4%A4-08-19")]
            ])
        )

        log_reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("💬 MESSAGE USER (DIRECT)", url=f"tg://user?id={user_id}")]])
        log_text = f"<b>#PM_MSG\n\nNᴀᴍᴇ : <a href='tg://user?id={user_id}'>{user}</a>\n\nID : <code>{user_id}</code>\n\nMᴇssᴀɢᴇ :</b> <code>{content}</code>\n\n#id{user_id}"

        try:
            if message.photo:
                await bot.send_chat_action(chat_id=LOG_CHANNEL, action=enums.ChatAction.UPLOAD_PHOTO)
                await bot.send_photo(chat_id=LOG_CHANNEL, photo=message.photo.file_id, caption=log_text, reply_markup=log_reply_markup)
            elif message.video:
                await bot.send_chat_action(chat_id=LOG_CHANNEL, action=enums.ChatAction.UPLOAD_VIDEO)
                await bot.send_video(chat_id=LOG_CHANNEL, video=message.video.file_id, caption=log_text, reply_markup=log_reply_markup)
            elif message.sticker:
                await bot.send_message(chat_id=LOG_CHANNEL, text=log_text, reply_markup=log_reply_markup, disable_web_page_preview=True)
                await bot.send_sticker(chat_id=LOG_CHANNEL, sticker=message.sticker.file_id)
            else:
                await bot.send_chat_action(chat_id=LOG_CHANNEL, action=enums.ChatAction.TYPING)
                await bot.send_message(chat_id=LOG_CHANNEL, text=log_text, reply_markup=log_reply_markup, disable_web_page_preview=True)
        except Exception as e:
            logger.error(f"Error sending log to LOG_CHANNEL: {e}")



@Client.on_message(filters.chat(LOG_CHANNEL) & filters.reply)
async def admin_reply_to_user(bot: Client, message):
    parent_message = message.reply_to_message
    parent_text = parent_message.text or parent_message.caption
    if not parent_text: return

    match = re.search(r"#id(\d+)", parent_text)
    if match:
        user_id = int(match.group(1))
        reply_caption = f"<b>{message.caption}</b>" if message.caption else ""

        try:
            if message.photo:
                await bot.send_chat_action(chat_id=user_id, action=enums.ChatAction.UPLOAD_PHOTO)
                await bot.send_photo(chat_id=user_id, photo=message.photo.file_id, caption=reply_caption)
            elif message.video:
                await bot.send_chat_action(chat_id=user_id, action=enums.ChatAction.UPLOAD_VIDEO)
                await bot.send_video(chat_id=user_id, video=message.video.file_id, caption=reply_caption)
            elif message.sticker:
                await bot.send_sticker(chat_id=user_id, sticker=message.sticker.file_id)
            elif message.text:
                await bot.send_chat_action(chat_id=user_id, action=enums.ChatAction.TYPING)
                await bot.send_message(chat_id=user_id, text=f"<b>💬 Message From Admin:\n\n{message.text}</b>")
            else:
                return

            await message.reply_text("<b>✅ മറുപടി യൂസർക്ക് വിജയകരമായി അയച്ചു!</b>")

        except UserIsBlocked:
            await message.reply_text("<b>❌ മറുപടി അയക്കാൻ കഴിഞ്ഞില്ല! ഈ യൂസർ ബോട്ടിനെ ബ്ലോക്ക് ചെയ്തിരിക്കുകയാണ്.</b>")
        except PeerIdInvalid:
            await message.reply_text("<b>❌ ഈ യൂസറുമായി ബോട്ട് ഇതുവരെ ചാറ്റ് തുടങ്ങിയിട്ടില്ല (Peer ID Invalid).</b>")
        except Exception as e:
            logger.error(f"Admin reply forward error: {e}")
            await message.reply_text(f"<b>❌ മെസ്സേജ് അയക്കാൻ കഴിഞ്ഞില്ല!\nError: {e}</b>")



@Client.on_message(filters.text & filters.incoming)
async def give_filters(client, message):
    k = await global_filters(client, message)    
    if k == False:
        await auto_filter(client, message)


# 1. പ്രധാന സ്പെൽചെക്ക് ഫങ്ക്ഷൻ
@Client.on_callback_query(filters.regex(r"^spol"))
async def advantage_spoll_choker(bot, query):
    _, user, movie_idx = query.data.split('#')
    
    # 🔐 യൂസർ വെരിഫിക്കേഷൻ
    if int(user) and query.from_user.id != int(user):
        return await query.answer("This is not for you!", show_alert=True)
        
    # ❌ സ്പെൽചെക്ക് ക്ലോസ് ചെയ്യൽ
    if movie_idx == "close_spellcheck":
        return await query.message.delete()
        
    # ⏳ യൂസറുടെ ഒറിജിനൽ റിക്വസ്റ്റ് മെസ്സേജ് ട്രാക്ക് ചെയ്യുന്നു
    reply_to_msg = query.message.reply_to_message
    if not reply_to_msg:
        return await query.answer("Expired button.", show_alert=True)
        
    movies = SPELL_CHECK.get(reply_to_msg.id)
    if not movies:
        return await query.answer("Expired button.", show_alert=True)
        
    movie = movies[int(movie_idx)]
    await query.answer('Searching database...')
    
    try: await query.message.delete()
    except: pass

    # 🔍 ഫിൽറ്ററുകൾ പരിശോധിക്കുന്നു
    if await global_filters(bot, query.message, text=movie) == False:
        files, offset, total_results = await get_search_results(movie, offset=0, filter=True)
        if files:
            return await auto_filter(bot, query, (movie, files, offset, total_results))
            
        # 📌 സിനിമ ഡാറ്റാബേസിൽ ഇല്ലെങ്കിൽ മിസ്സിംഗ് ലിസ്റ്റിലേക്ക് സേവ് ചെയ്യുന്നു
        try: await save_missing_movie(movie)
        except: pass

        # 🔘 പുതിയ ബട്ടൺ ടെക്സ്റ്റുകൾ മുകളിലും ലിങ്ക് ബട്ടണുകൾ താഴെയും (2x2 Grid Layout)
        buttons = InlineKeyboardMarkup((
            (
                InlineKeyboardButton("📢 Coming Soon", callback_data="alert_channel"),
                InlineKeyboardButton("🫴 OTT വന്നിട്ടില്ല", callback_data="alert_google")
            ),
            (
                InlineKeyboardButton("📜 Rᴜʟᴇs", url="http://telegra.ph/Request-%E0%B4%85%E0%B4%AF%E0%B4%95%E0%B5%8D%E0%B4%95-%E0%B4%AE%E0%B4%A8%E0%B4%A8-%E0%B4%B5%E0%B4%AF%E0%B4%95%E0%B5%8D%E0%B4%95%E0%B1%81%E0%B4%A3%E0%B4%9F%E0%B4%A8%E0%B4%A4-08-19"),
                InlineKeyboardButton("📥 Rᴇqᴜᴇsᴛ", url="http://t.me/Promoviesearcher_bot")
            )
        ))
        
        # 🖼️ മൂവി പോസ്റ്റർ ഡൈനാമിക് ചെക്കിംഗ്
        try: photo_url = await get_any_movie_poster(movie)
        except: photo_url = None

        if not photo_url:
            photo_url = "https://files.catbox.moe/egu0ip.jpg"

        msg = None
        # 1. ആദ്യം ലഭ്യമായ ഫോട്ടോ യൂസറുടെ മെസ്സേജിന് റിപ്ലൈ ആയി അയക്കാൻ ശ്രമിക്കുന്നു
        try:
            msg = await query.message.reply_photo(
                photo=photo_url,
                caption=script.OTT_TEXT,                    
                reply_markup=buttons,
                parse_mode=enums.ParseMode.HTML,
                reply_to_message_id=reply_to_msg.id  # ↩️ ഇവിടെ ഒറിജിനൽ മെസ്സേജിന് റിപ്ലൈ നൽകുന്നു
            )
        except:
            # 2. ബാക്കപ്പ് ഫോട്ടോയും ഫെയിൽ ആയാൽ നോർമൽ ടെക്സ്റ്റ് മെസ്സേജ് റിപ്ലൈ ആയി അയക്കും
            try:
                msg = await query.message.reply_text(
                    text=script.OTT_TEXT, 
                    reply_markup=buttons,
                    parse_mode=enums.ParseMode.HTML,
                    reply_to_message_id=reply_to_msg.id  # ↩️ ഇവിടെ ഒറിജിനൽ മെസ്സേജിന് റിപ്ലൈ നൽകുന്നു
                )
            except: pass
        
        # 🕒 60 സെക്കന്റിന് ശേഷം അലേർട്ട് മെസ്സേജ് ഓട്ടോമാറ്റിക് ആയി ഡിലീറ്റ് ചെയ്യും
        if msg:
            await asyncio.sleep(60)
            try: await msg.delete()
            except: pass

# 2. "📢 Coming Soon" ബട്ടൺ ക്ലിക്ക് ചെയ്യുമ്പോൾ ഉള്ള അലേർട്ട്
@Client.on_callback_query(filters.regex("^alert_channel$"))
async def channel_alert_handler(bot, query):
    await query.answer("OTT FILE NOT AVAILABLE", show_alert=True)

# 3. "🫴 OTT വന്നിട്ടില്ല" ബട്ടൺ ക്ലിക്ക് ചെയ്യുമ്പോൾ ഉള്ള അലേർട്ട്
@Client.on_callback_query(filters.regex("^alert_google$"))
async def google_alert_handler(bot, query):
    await query.answer("OTT ഇറങ്ങുന്നേ വരെ ക്ഷമിക്ക് അളിയാ", show_alert=True)



@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer("Search for Yourself", show_alert=True)

    try:
        offset = int(offset)
    except ValueError:
        offset = 0

    search = BUTTONS.get(key)
    if not search:
        await query.answer("You are using one of my old messages, please send the request again.", show_alert=True)
        return

    db_search = search
    if " [" in search:
        base = search.split(" [")[0]
        tags = search.split(" [")[1].replace("]", "").split(" + ")
        db_search = f"{base} {' '.join(tags)}"

    files, n_offset, total = await get_search_results(db_search.lower(), offset=offset, filter=True)
    if not files:
        await query.answer("no files", show_alert=True)
        return

    settings = await get_settings(query.message.chat.id)
    btn = []
    pre = 'filep' if settings['file_secure'] else 'file'

    for file in files:
        btn.append([InlineKeyboardButton(text=f"{get_size(file.file_size)}➪{file.file_name}", callback_data=f'{pre}#{file.file_id}')])

    if 0 < offset < 10:
        off_set = 0
    elif offset == 0:
        off_set = None
    else:
        off_set = offset - 10

    if n_offset == '':
        btn.append([
            InlineKeyboardButton("Back", callback_data=f"next_{req}_{key}_{off_set}"),
            InlineKeyboardButton(f"{math.ceil(offset / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages")
        ])
    elif off_set is None:
        btn.append([
            InlineKeyboardButton(f"{math.ceil(offset / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
            InlineKeyboardButton("Next", callback_data=f"next_{req}_{key}_{n_offset}")
        ])
    else:
        btn.append([
            InlineKeyboardButton("Back", callback_data=f"next_{req}_{key}_{off_set}"),
            InlineKeyboardButton(f"{math.ceil(offset / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
            InlineKeyboardButton("Next", callback_data=f"next_{req}_{key}_{n_offset}")
        ])

    try:
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))
        await query.answer()
    except MessageNotModified:
        await query.answer()
    except MessageIdInvalid:
        await query.answer("ഈ സെർച്ച് മെനു കാലാവധി കഴിഞ്ഞതോ ഡിലീറ്റ് ചെയ്യപ്പെട്ടതോ ആണ്. ദയവായി വീണ്ടും സെർച്ച് ചെയ്യുക!", show_alert=True)
    except FloodWait as e:
        await query.answer(f"വളരെ വേഗത്തിലാണ്! ദയവായി {e.value} സെക്കൻഡ് കാത്തിരിക്കൂ.", show_alert=True)


@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()                
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            grpid = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    await query.message.edit_text("Make sure I'm present in your group!!", quote=True)
                    return await query.answer('Piracy Is Crime')
            else:
                await query.message.edit_text(
                    "I'm not connected to any groups!\nCheck /connections or connect to any groups",
                    quote=True
                )
                return await query.answer('Piracy Is Crime')

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            title = query.message.chat.title

        else:
            return await query.answer('Piracy Is Crime')

        st = await client.get_chat_member(grp_id, userid)
        if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
            await del_all(query.message, grp_id, title)
        else:
            await query.answer("You need to be Group Owner or an Auth User to do that!", show_alert=True)
    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer("That's not for you!!", show_alert=True)
    elif "groupcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        act = query.data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        if act == "":
            stat = "CONNECT"
            cb = "connectcb"
        else:
            stat = "DISCONNECT"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
             InlineKeyboardButton("DELETE", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("BACK", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"Group Name : **{title}**\nGroup ID : `{group_id}`",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return await query.answer('Piracy Is Crime')
    elif "connectcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title

        user_id = query.from_user.id

        mkact = await make_active(str(user_id), str(group_id))

        if mkact:
            await query.message.edit_text(
                f"Connected to **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text('Some error occurred!!', parse_mode=enums.ParseMode.MARKDOWN)
        return await query.answer('Piracy Is Crime')
    elif "disconnect" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title
        user_id = query.from_user.id

        mkinact = await make_inactive(str(user_id))

        if mkinact:
            await query.message.edit_text(
                f"Disconnected from **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer('Piracy Is Crime')
    elif "deletecb" in query.data:
        await query.answer()

        user_id = query.from_user.id
        group_id = query.data.split(":")[1]

        delcon = await delete_connection(str(user_id), str(group_id))

        if delcon:
            await query.message.edit_text(
                "Successfully deleted connection"
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer('Piracy Is Crime')
    elif query.data == "backcb":
        await query.answer()

        userid = query.from_user.id

        groupids = await all_connections(str(userid))
        if groupids is None:
            await query.message.edit_text(
                "There are no active connections!! Connect to some groups first.",
            )
            return await query.answer('Piracy Is Crime')
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ACTIVE" if active else ""
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}"
                        )
                    ]
                )
            except:
                pass
        if buttons:
            await query.message.edit_text(
                "Your connected group details ;\n\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True) 
            
    if query.data.startswith("file"):
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.file_name
        
        # ⬇️ എറർ വരാതിരിക്കാൻ ഈ 2 വരികൾ പകരം ചേർക്കുക ⬇️
        chat_id = query.message.chat.id if (query.message and query.message.chat) else query.from_user.id
        settings = await get_settings(chat_id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption, mention=query.from_user.mention)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{title}"
            
        # ബട്ടണുകൾ ഉണ്ടായിരുന്ന ഭാഗം ഒഴിവാക്കി നേരിട്ട് PM-ലേക്ക് റീഡയറക്ട് ചെയ്യുന്നു
        try:
            if settings['botpm']:
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                return
            else:
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                return
        except QueryIdInvalid:
            await query.answer("This query is no longer valid.", show_alert=True)
        except UserIsBlocked:
            await query.answer('Unblock the bot mahn !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
        except Exception as e:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
            
    

    elif query.data.startswith("killfilesdq"):
        ident, keyword = query.data.split("#")
        await query.message.edit_text(f"<b>Fᴇᴛᴄʜɪɴɢ Fɪʟᴇs ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {keyword} ᴏɴ DB... Pʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>")
        files_media1, files_media2, total_media = await get_bad_files(keyword)        
        await query.message.edit_text(f"<b>Fᴏᴜɴᴅ {total_media} Fɪʟᴇs ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {keyword} !\n\nFɪʟᴇ ᴅᴇʟᴇᴛɪᴏɴ ᴘʀᴏᴄᴇss ᴡɪʟʟ sᴛᴀʀᴛ ɪɴ 5 sᴇᴄᴏɴᴅs!</b>")
        await asyncio.sleep(5)
        deleted = 0
        async with lock:
            try:
                # Delete files from Media collection
                for file in files_media1:
                    file_ids = file.file_id
                    file_name = file.file_name
                    result = await Media.collection.delete_one({
                        '_id': file_ids,
                    })
                    if result.deleted_count:
                        logger.info(f'Fɪʟᴇ Fᴏᴜɴᴅ ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {keyword}! Sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {file_name} ғʀᴏᴍ ᴅᴀᴛᴀʙᴀsᴇ.')
                    deleted += 1
                    if deleted % 100 == 0:
                        await query.message.edit_text(f"<b>Pʀᴏᴄᴇss sᴛᴀʀᴛᴇᴅ ғᴏʀ ᴅᴇʟᴇᴛɪɴɢ ғɪʟᴇs ғʀᴏᴍ DB. Sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {str(deleted)} ғɪʟᴇs ғʀᴏᴍ DB ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {keyword} !\n\nPʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>")
                # Delete files from Mediaa collection
                for file in files_media2:
                    file_ids = file.file_id
                    file_name = file.file_name
                    result = await Mediaa.collection.delete_one({
                        '_id': file_ids,
                    })
                    if result.deleted_count:
                        logger.info(f'Fɪʟᴇ Fᴏᴜɴᴅ ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {keyword}! Sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {file_name} ғʀᴏᴍ ᴅᴀᴛᴀʙᴀsᴇ.')
                    deleted += 1
                    if deleted % 100 == 0:
                        await query.message.edit_text(f"<b>Pʀᴏᴄᴇss sᴛᴀʀᴛᴇᴅ ғᴏʀ ᴅᴇʟᴇᴛɪɴɢ ғɪʟᴇs ғʀᴏᴍ DB. Sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {str(deleted)} ғɪʟᴇs ғʀᴏᴍ DB ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {keyword} !\n\nPʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>")
            except Exception as e:
                logger.exception
                await query.message.edit_text(f'Eʀʀᴏʀ: {e}')
            else:
                await query.message.edit_text(f"<b>Pʀᴏᴄᴇss Cᴏᴍᴘʟᴇᴛᴇᴅ ғᴏʀ ғɪʟᴇ ᴅᴇʟᴇᴛɪᴏɴ !\n\nSᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {str(deleted)} ғɪʟᴇs ғʀᴏᴍ DB ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {keyword}.</b>")
            
    elif query.data == "pages":
        await query.answer()
    
    elif query.data == "start":
        buttons = [
            [
                InlineKeyboardButton('👥 Jᴏɪɴ Oᴜʀ Gʀᴏᴜᴘ 👥', url='https://t.me/+eb__Eg3RS2IyZWQ1')
            ],
            [
                InlineKeyboardButton('📊 Sᴛᴀᴛs 📊', callback_data='stats'),
                InlineKeyboardButton('✖️ Cʟᴏsᴇ ✖️', callback_data='close_data')
            ]
        ]       
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    
    elif query.data == "stats":
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='start')           
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)        
        
        tot = await Media.count_documents()
        tota = await Mediaa.count_documents()
        total = tot + tota
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        
        stats = await clientDB.command('dbStats')
        used_dbSize = (stats['dataSize']/(1024*1024))+(stats['indexSize']/(1024*1024))        
        free_dbSize = 512-used_dbSize
        
        stats2 = await clientDB2.command('dbStats')
        used_dbSize2 = (stats2['dataSize']/(1024*1024))+(stats2['indexSize']/(1024*1024))
        free_dbSize2 = 512-used_dbSize2
        
        stats3 = await clientDB3.command('dbStats')
        used_dbSize3 = (stats3['dataSize']/(1024*1024))+(stats3['indexSize']/(1024*1024))
        free_dbSize3 = 512-used_dbSize3        

        # 🖥️ Koyeb CPU, RAM & Disk കണക്കുകൾ എടുക്കുന്നു
        import psutil
        import shutil
        
        cpu_usage = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        ram_usage = ram.percent
        ram_used_mb = round(ram.used / (1024 * 1024), 2)
        ram_total_mb = round(ram.total / (1024 * 1024), 2)
        
        total_d, used_d, free_d = shutil.disk_usage("/")
        disk_usage = round((used_d / total_d) * 100, 2)
        
        stats_text = (
            "📊 <b>Bot Statistics</b>\n\n"
            f"▪️ Total Files: {total}\n"
            f"▪️ Main DB Files (Media): {tot}\n"
            f"▪️ DB 2 Files (Mediaa): {tota}\n\n"
            f"▪️ Total Users: {users}\n"
            f"▪️ Total Chats: {chats}\n\n"
            f"🗄 Database 1 Size: {round(used_dbSize, 2)} MB / Free: {round(free_dbSize, 2)} MB\n"
            f"🗄 Database 2 Size: {round(used_dbSize2, 2)} MB / Free: {round(free_dbSize2, 2)} MB\n"
            f"🗄 Database 3 Size: {round(used_dbSize3, 2)} MB / Free: {round(free_dbSize3, 2)} MB\n\n"
            f"🖥 <b>Koyeb Server Status:</b>\n"
            f"⚙️ CPU Usage: {cpu_usage}%\n"
            f"🧠 RAM Usage: {ram_usage}% ({ram_used_mb} MB / {ram_total_mb} MB)\n"
            f"💽 Disk Space: {disk_usage}%\n"
        )
        
        # 🛠️ എറർ ഒഴിവാക്കാനായി വരുത്തിയ മാറ്റം:
        try:
            # മീഡിയ മെസ്സേജ് ആണെങ്കിൽ അതിന്റെ ക്യാപ്ഷൻ എഡിറ്റ് ചെയ്യുന്നു
            await query.message.edit_caption(
                caption=stats_text,
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            )
        except Exception:
            # അതല്ലെങ്കിൽ സാധാരണ പോലെ ടെക്സ്റ്റ് എഡിറ്റ് ചെയ്യുന്നു
            await query.message.edit_text(
                text=stats_text,
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            )



async def auto_filter(client, msg, spoll=False):
    if not spoll:
        message = msg
        settings = await get_settings(message.chat.id)
        if message.text.startswith("/"): return
        if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text): return

        if 0 < len(message.text) < 100:
            search = message.text
            search = re.sub(r'[\u200b\u200c\u200d\ufeff\u200e\u200f]', '', search)
            search = re.sub(r'[\s\u00a0\u2000-\u200a\u202f\u205f\u3000]+', ' ', search)
            search = re.sub(r"['‘’]", "", search)
            search = re.sub(r"[-–—_,#&?/( )\[\]\\\":\.¡%“”]", " ", search)
            search = re.sub(r"\b(hd|full|print|file)\b", "", search, flags=re.IGNORECASE)

            find = search.lower().split(" ")
            removes = {"pls","plz","plzz","please","send","snd","snt","gib","veno","venam","venum","undo","ayakkumo","ayakkamo","und","move","multi","dubb","dub","bro","bruh","broh","dubbed","link","lnk","iruka","pannunga","pannungga","anuppunga","anupunga","anuppungga","anupungga","subtile","kitti","kitty","tharu","kittumo","kittum","da","mwonse","bhai","share","malayalm","malylm","subtitle"}
            search = " ".join(w for w in find if w not in removes)
            search = re.sub(r"\s+", " ", search).strip()
            if not search: return

            files, offset, total_results = await get_search_results(search.lower(), offset=0, filter=True)

            if not files:
                keywords = await get_gfilters('gfilters')
                if any(re.match(r"^" + re.escape(k.strip().lower()) + r"$", search.lower()) for k in keywords): return
                
                # 🔄 ഫയലുകൾ ഇല്ലെങ്കിൽ പുതിയ ടെക്സ്റ്റ് ലിസ്റ്റ് സ്പെൽചെക്കിലേക്ക് പോകുന്നു
                try:
                    await advantage_spell_chok(client, msg)
                    return
                except Exception:
                    return
        else:
            settings = await get_settings(msg.message.chat.id)
            return
    else:
        message = msg.message.reply_to_message
        search, files, offset, total_results = spoll
        settings = await get_settings(message.chat.id)

    key = f"{message.chat.id}-{message.id}"
    BUTTONS[key] = search

    # ⚡ ഇന്റർനെറ്റ് ഇല്ലാതെ വർഷം വേർതിരിച്ചെടുക്കുന്നു
    year_match = re.findall(r'\b(19\d{2}|20[0-2]\d)\b', search)
    if not year_match and files:
        year_match = re.findall(r'\b(19\d{2}|20[0-2]\d)\b', files[0].file_name)
    
    movie_year = f" ({year_match[0]})" if year_match else ""
    clean_title = re.sub(r'\b(19\d{2}|20[0-2]\d)\b', '', search).strip().upper()

    # 📝 ഗ്രൂപ്പിൽ കാണിക്കേണ്ട blockquote ലേഔട്ട്
    cap = (
        f"<blockquote><b><i>{clean_title}{movie_year}</i></b></blockquote>\n\n"
        f"<b><i><u>For better result:</u></i></b>\n<i>↪bhramam      ❌\n↪bhramam 2021 ✅</i>"
    )

    # 📥 ബോട്ടിന്റെ PM-ലേക്ക് റീഡയറക്ട് ചെയ്യാനുള്ള ബട്ടൺ നിർമ്മിക്കുന്നു
    # ഇവിടെ സെർച്ച് ക്വറി ബേസ്64 ലോ മറ്റോ മാറ്റാതെ സുരക്ഷിതമായി സ്റ്റാർട്ട് ലിങ്ക് ആക്കുന്നു
    query_encoded = quote_plus(search)
    pm_btn = InlineKeyboardMarkup([[
        InlineKeyboardButton("📥 Dᴏᴡɴʟᴏᴀᴅ Mᴏᴠɪᴇ", url=f"https://t.me{temp.U_NAME}?start=search_{query_encoded}")
    ]])

    poster = await get_any_movie_poster(search)

    fmsg = None
    if poster:
        try:
            fmsg = await message.reply_photo(photo=poster, caption=cap, reply_markup=pm_btn, parse_mode=enums.ParseMode.HTML)
        except Exception as photo_error:
            logger.warning(f"Photo അയക്കാൻ കഴിഞ്ഞില്ല, ടെക്സ്റ്റിലേക്ക് മാറുന്നു: {photo_error}")

    if not fmsg:
        try:
            await message.reply_text(text=cap, reply_markup=pm_btn, disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML)
        except Exception as text_error:
            logger.error(f"Text മെസ്സേജ് അയക്കുന്നതിലും എറർ വന്നിരിക്കുന്നു: {text_error}")



async def advantage_spell_chok(client, msg):
    mv_id = msg.id
    mv_rqst = msg.text
    reqstr1 = msg.from_user.id if msg.from_user else 0
    cleaned_query = re.sub(
        r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|"
        r"br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|file|that|find|und(o)*|"
        r"kit(t(i|y)?)?o(w)?|thar(u)?(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|"
        r"any(one)|with\ssubtitle(s)?)",
        "", msg.text, flags=re.IGNORECASE
    )
    cleaned_query = cleaned_query.strip()

    # 🔍 ഗൂഗിൾ സെർച്ചിനായുള്ള ലിങ്കും മറ്റ് ബട്ടണുകളും ഫോർമാറ്റ് ചെയ്യുന്നു
    reqst_gle = quote_plus(mv_rqst)
    google_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔎 𝗖𝗼𝗿𝗿𝗲𝗰𝘁 𝗦𝗽𝗲𝗹𝗹𝗶𝗻𝗴 (𝖦𝗈𝗈𝗀𝗅𝖾) 🔍", url=f"https://www.google.com/search?q={reqst_gle}")],
        [
            InlineKeyboardButton("📜 Rᴜʟᴇs", url="http://telegra.ph/Request-%E0%B4%85%E0%B4%AF%E0%B4%95%E0%B5%8D%E0%B4%95-%E0%B4%AE%E0%B4%A8%E0%B4%A8-%E0%B4%B5%E0%B4%AF%E0%B4%95%E0%B5%8D%E0%B4%95%E0%B5%81%E0%B4%A3%E0%B4%9F%E0%B4%A8%E0%B4%A8%E0%B4%A4-08-19"),
            InlineKeyboardButton("📥 Rᴇqᴜᴇsᴛ", url="http://t.me/Promoviesearcher_bot")
        ]
    ])

    try:
        # സിനിമയുടെ പേരുകൾ കണ്ടെത്താൻ നിങ്ങളുടെ പഴയ ഫങ്ക്ഷൻ തന്നെ ഉപയോഗിക്കുന്നു
        movies = await get_poster(cleaned_query, bulk=True)
    except Exception as e:
        logger.exception(e)
        try:
            k = await msg.reply_photo(
                photo="https://catbox.moe",
                caption=script.SPELL_TEXT.format(msg.from_user.mention),
                reply_markup=google_button,
                reply_to_message_id=msg.id,
                parse_mode=enums.ParseMode.HTML
            )
        except Exception:
            k = await msg.reply_text(
                text=script.SPELL_TEXT.format(msg.from_user.mention), 
                reply_markup=google_button,
                reply_to_message_id=msg.id,
                parse_mode=enums.ParseMode.HTML
            )
            
        await asyncio.sleep(30)
        await k.delete()
        return

    if not movies:
        try:
            k = await msg.reply_photo(
                photo="https://catbox.moe",
                caption=script.SPELL_TEXT.format(msg.from_user.mention),
                reply_markup=google_button,
                reply_to_message_id=msg.id,
                parse_mode=enums.ParseMode.HTML
            )
        except Exception:
            k = await msg.reply_text(
                text=script.SPELL_TEXT.format(msg.from_user.mention), 
                reply_markup=google_button,
                reply_to_message_id=msg.id,
                parse_mode=enums.ParseMode.HTML
            )
            
        await asyncio.sleep(40)
        await k.delete()
        return

    # 1. ടൈറ്റിലും വർഷവും ഒരുമിച്ച് ലിസ്റ്റാക്കുന്നു (വർഷം ഇല്ലെങ്കിൽ 'N/A' എന്ന് കാണിക്കും)
    # 1. API ക്ലാസുകളിൽ നിന്ന് ടൈറ്റിലും വർഷവും കൃത്യമായി വേർതിരിച്ച് ലിസ്റ്റാക്കുന്നു
    movielist = []
    for movie in movies:
        title = movie.get('title')
        year = movie.get('year')
        
        if title:
            # വർഷം ഉണ്ടെങ്കിൽ അതിൽ നിന്നും 4 അക്കങ്ങൾ മാത്രം (Year) വേർതിരിച്ചെടുക്കുന്നു
            if year and str(year) != "N/A":
                year_str = re.findall(r'\b(19\d{2}|20\d{2})\b', str(year))
                year_val = f" {year_str[0]}" if year_str else ""
            else:
                year_val = ""
                
            movielist.append(f"{title.strip()}{year_val}")

    if not movielist:
        return

    SPELL_CHECK[mv_id] = movielist
    _trim_dict(SPELL_CHECK)

    # 📝 Heading ചേർക്കുന്നു
    spell_list_text = script.NO_TXT + "\n\n"
    spell_list_text += "<u><b>SUGGESTIONS 👇</b></u>\n"
    
    # 2. ആദ്യത്തെ 6 എണ്ണം പർപ്പസ്ലി പാസേമോഡ് HTML-ൽ ബോൾഡ് ആയി ലിസ്റ്റ് ചെയ്യുന്നു
    for index, movie_name in enumerate(movielist[:6], start=1):
        spell_list_text += f"<b>{index}. {movie_name}</b>\n"


    
    # 🖼️ ഫോട്ടോ എടുക്കാൻ മാത്രം get_any_movie_poster ഉപയോഗിക്കുന്നു (ആദ്യത്തെ സിനിമയുടെ പേര് വച്ച്)
    try: 
        photo_url = await get_any_movie_poster(cleaned_query)
    except Exception: 
        photo_url = None

    if not photo_url:
        photo_url = "https://files.catbox.moe/egu0ip.jpg"

    try:
        # ഇവിടെ close_btn-ന് പകരം google_button നേരിട്ട് നൽകിയിരിക്കുന്നു
        spell_check_del = await msg.reply_photo(
            photo=photo_url,
            caption=spell_list_text,
            reply_markup=google_button,
            reply_to_message_id=msg.id,
            parse_mode=enums.ParseMode.HTML
        )
    except Exception:
        spell_check_del = await msg.reply_text(
            text=spell_list_text,
            reply_markup=google_button,
            reply_to_message_id=msg.id,
            parse_mode=enums.ParseMode.HTML
        )
        
    await asyncio.sleep(50)
    try:
        await spell_check_del.delete()
    except Exception:
        pass

            
        

async def global_filters(client, message, text=False):
    group_id = message.chat.id
    raw_name = text or message.text
    
    # 🌟 ഇവിടെ raw_name-നെ സുരക്ഷിതമായി സ്ട്രിംഗ് (str) ആക്കി മാറ്റുന്നു
    # ഇത് Pyrogram-ന്റെ 'utf-16-le' ഡീകോഡിങ് എറർ പൂർണ്ണമായി ഇല്ലാതാക്കും
    safe_name = str(raw_name) if raw_name else ""

    try:
        # ഇമോജികൾ നീക്കം ചെയ്യുന്നു
        search = emoji.replace_emoji(safe_name, replace='')
    except Exception:
        # ഏതെങ്കിലും സാഹചര്യത്തിൽ വീണ്ടും തകരാർ വന്നാൽ എറർ അടിക്കാതെ മുന്നോട്ട് പോകാൻ
        search = safe_name

    search = re.sub(r'[\u200b\u200c\u200d\ufeff\u200e\u200f]', '', search)
    search = re.sub(r'[\s\u00a0\u2000-\u200a\u202f\u205f\u3000]+', ' ', search)
    search = re.sub(r"['‘’]", "", search)
    search = re.sub(r"[-–—_,#&?/( )\[\]\\\":\.¡%“”]", " ", search)
    search = re.sub(r"\b(hd|full|print|file)\b", "", search, flags=re.IGNORECASE)
    find = search.lower().split(" ")
    removes = {"pls","plz","plzz","please","send","snd","snt","gib","veno","venam","venum","undo","ayakkumo","ayakkamo","und","move","multi","dubb","dub","bro","bruh","broh","dubbed","link","lnk","iruka","pannunga","pannungga","anuppunga","anupunga","anuppungga","anupungga","subtile","kitti","kitty","tharu","kittumo","kittum","da","mwonse","bhai","share","malayalm","malylm","subtitle"}
    search = " ".join(w for w in find if w not in removes)
    clean_name = re.sub(r"\s+", " ", search).strip()

    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_gfilters('gfilters')

    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"^" + re.escape(keyword.strip().lower()) + r"$"
        if re.match(pattern, clean_name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_gfilter('gfilters', keyword)
            if reply_text: reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if btn != "[]":
                        try: button = json.loads(btn)
                        except Exception: button = eval(btn)
                    else: button = []

                    g_msg = None
                    if fileid == "None":
                        while True:
                            try:
                                if btn == "[]":
                                    g_msg = await client.send_message(group_id, reply_text, disable_web_page_preview=True, reply_to_message_id=reply_id)
                                else:
                                    g_msg = await client.send_message(group_id, reply_text, disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(button), reply_to_message_id=reply_id)
                                break
                            except FloodWait as e:
                                logger.warning(f"FloodWait triggered! Sleeping for {e.value} seconds.")
                                await asyncio.sleep(e.value)
                    elif btn == "[]":
                        while True:
                            try:
                                g_msg = await client.send_cached_media(group_id, fileid, caption=reply_text or "", reply_to_message_id=reply_id)
                                break
                            except FloodWait as e:
                                logger.warning(f"FloodWait triggered! Sleeping for {e.value} seconds.")
                                await asyncio.sleep(e.value)
                    else:
                        while True:
                            try:
                                g_msg = await client.send_cached_media(group_id, fileid, caption=reply_text or "", reply_markup=InlineKeyboardMarkup(button), reply_to_message_id=reply_id)
                                break
                            except FloodWait as e:
                                logger.warning(f"FloodWait triggered! Sleeping for {e.value} seconds.")
                                await asyncio.sleep(e.value)

                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False
