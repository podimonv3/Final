import logging
from pyrogram.errors import InputUserDeactivated, UserNotParticipant, FloodWait, UserIsBlocked, PeerIdInvalid
from info import REQ_CHANNEL1, REQ_CHANNEL2, ADMINS
import asyncio
from pyrogram.types import Message, InlineKeyboardButton
from pyrogram import enums
from typing import Union
import re
import os
import time
from datetime import datetime
from typing import List
from database.users_chats_db import db
from info import TMDB_API_KEY, OMDB_API_KEY, DEFAULT_POSTER
import requests
import asyncio

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BTN_URL_REGEX = re.compile(
    r"(\[([^\[]+?)\]\((buttonurl|buttonalert):(?:/{0,2})(.+?)(:same)?\))"
)

BANNED = {}
SMART_OPEN = '“'
SMART_CLOSE = '”'
START_CHAR = ('\'', '"', SMART_OPEN)

# temp db for banned 
class temp(object):
    BANNED_USERS = []
    BANNED_CHATS = []
    ME = None
    CURRENT=int(os.environ.get("SKIP", 2))
    CANCEL = False
    MELCOW = {}
    U_NAME = None
    B_NAME = None
    SETTINGS = {}




import asyncio
import re
import urllib.parse

import aiohttp
from bs4 import BeautifulSoup
from imdb import Cinemagoer
import imdb

ia = imdb.Cinemagoer()


# 1. TMDB Async
async def get_tmdb_poster(movie_name, tmdb_api_key):
    try:
        url = (
            f"https://api.themoviedb.org/3/search/movie"
            f"?api_key={tmdb_api_key}"
            f"&query={urllib.parse.quote(movie_name)}"
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as response:
                data = await response.json()

                if data.get("results"):
                    movie = data["results"][0]

                    if movie.get("poster_path"):
                        return (
                            f"https://image.tmdb.org/t/p/w500"
                            f"{movie['poster_path']}"
                        )

    except Exception:
        pass

    return None



# 2. OMDb Async
async def get_omdb_poster(movie_name, omdb_api_key):
    try:
        url = (
            f"https://www.omdbapi.com/"
            f"?apikey={omdb_api_key}"
            f"&t={urllib.parse.quote(movie_name)}"
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as response:
                data = await response.json()

                if (
                    data.get("Response") == "True"
                    and data.get("Poster")
                    and data["Poster"] != "N/A"
                ):
                    return data["Poster"]

    except Exception:
        pass

    return None

# 3. Cinemagoer (ഇത് async അല്ല, അതിനാൽ ഇതിനെ ഒരു പ്രത്യേക ത്രെഡിൽ റൺ ചെയ്യിക്കണം)
def sync_cinemagoer(movie_name):
    try:
        movies = ia.search_movie(movie_name)

        if not movies:
            return None

        movie = movies[0]

        # Fetch main movie information
        ia.update(movie, ["main"])

        # Prefer full-size poster
        poster_url = movie.get("full-size cover url")

        if poster_url:
            return poster_url

        # Fallback to normal poster
        poster_url = movie.get("cover url")

        if poster_url:
            return poster_url

    except Exception as e:
        print(f"Cinemagoer error for '{movie_name}': {e}")

    return None

async def get_cinemagoer_poster(movie_name):
    return await asyncio.to_thread(
        sync_cinemagoer,
        movie_name
    )
    
# 4. Bing Scrapper Async
async def scrape_bing_poster(movie_name):
    try:
        search_query = f"{movie_name} movie poster"
        url = (
            f"https://www.bing.com/images/search"
            f"?q={urllib.parse.quote(search_query)}"
        )

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/154.0.0.0 Safari/537.36"
            )
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=headers,
                timeout=5
            ) as response:

                if response.status != 200:
                    return None

                html = await response.text()

        soup = BeautifulSoup(html, "html.parser")
        image_tag = soup.find("a", class_="iusc")

        if image_tag and image_tag.get("m"):
            match = re.search(
                r'"murl":"(.*?)"',
                image_tag["m"]
            )

            if match:
                return match.group(1)

    except Exception:
        pass

    return None


async def get_any_movie_poster(movie_name):
    # 1. TMDB
    if TMDB_API_KEY:
        poster = await get_tmdb_poster(movie_name, TMDB_API_KEY)
        if poster:
            return poster

    # 2. OMDb
    if OMDB_API_KEY:
        poster = await get_omdb_poster(movie_name, OMDB_API_KEY)
        if poster:
            return poster

    # 3. Cinemagoer
    poster = await get_cinemagoer_poster(movie_name)
    if poster:
        return poster

    # 4. Bing
    poster = await scrape_bing_poster(movie_name)
    if poster:
        return poster

    # 5. Default poster
    return DEFAULT_POSTER




async def check_loop_sub(client, message):
    count = 0
    while count < 15:
        check = await is_requested_one(client, message)
        check2 = await is_requested_two(client, message)
        count += 1
        if check and check2:
            return True
        await asyncio.sleep(1.5)
    return False

async def check_loop_sub1(client, message):
    count = 0
    while count < 15:
        if await is_requested_one(client, message):
            return True
        count += 1
        await asyncio.sleep(1)
    return False

async def check_loop_sub2(client, message):
    count = 0
    while count < 15:
        if await is_requested_two(client, message):
            return True
        count += 1
        await asyncio.sleep(1)
    return False

async def is_requested_one(self , message):
    user = await db.get_req_one(int(message.from_user.id))
    if user:
        return True
    if message.from_user.id in ADMINS:
        return True
    try:
        user = await self.get_chat_member(int(REQ_CHANNEL1), message.from_user.id)
    except UserNotParticipant:
        pass
    except Exception as e:
        logger.exception(e)
        pass
    else:
        if not (user.status == enums.ChatMemberStatus.BANNED):
            return True
        else:
            pass
    return False
    
async def is_requested_two(self, message):
    user = await db.get_req_two(int(message.from_user.id))
    if user:
        return True
    if message.from_user.id in ADMINS:
        return True
    try:
        user = await self.get_chat_member(int(REQ_CHANNEL2), message.from_user.id)
    except UserNotParticipant:
        pass
    except Exception as e:
        logger.exception(e)
        pass
    else:
        if not (user.status == enums.ChatMemberStatus.BANNED):
            return True
        else:
            pass
    return False
    
async def is_subscribed(bot, query):
    try:
        user = await bot.get_chat_member(AUTH_CHANNEL, query.from_user.id)
    except UserNotParticipant:
        pass
    except Exception as e:
        logger.exception(e)
    else:
        if user.status != 'kicked':
            return True

    return False
 

async def broadcast_messages(user_id, message):
    try:
        await message.copy(chat_id=user_id)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await broadcast_messages(user_id, message)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id}-Removed from Database, since deleted account.")
        return False, "Deleted"
    except UserIsBlocked:
        logging.info(f"{user_id} -Blocked the bot.")
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id} - PeerIdInvalid")
        return False, "Error"
    except Exception as e:
        return False, "Error"

async def get_settings(group_id):
    settings = temp.SETTINGS.get(group_id)
    if not settings:
        settings = await db.get_settings(group_id)
        temp.SETTINGS[group_id] = settings
    return settings
    
async def save_group_settings(group_id, key, value):
    current = await get_settings(group_id)
    current[key] = value
    temp.SETTINGS[group_id] = current
    await db.update_settings(group_id, current)
    
def get_size(size):
    """Get size in readable integer format with full superscript styling"""
    units = ["Bytes", "ᴷᴮ", "ᴹᴮ", "ᴳᴮ", "ᵀᴮ", "ᴾᴮ", "ᴱᴮ"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
        
    raw_size_str = str(int(size))
    
    # Mapping table to convert normal numbers to superscript numbers
    superscript_map = {
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
        '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'
    }
    
    su_size_str = "".join(superscript_map.get(char, char) for char in raw_size_str)
    
    return f"{su_size_str}{units[i]}"

def get_file_id(msg: Message):
    if msg.media:
        for message_type in (
            "photo",
            "animation",
            "audio",
            "document",
            "video",
            "video_note",
            "voice",
            "sticker"
        ):
            obj = getattr(msg, message_type)
            if obj:
                setattr(obj, "message_type", message_type)
                return obj

def extract_user(message: Message) -> Union[int, str]:
    """extracts the user from a message"""
    # https://github.com/SpEcHiDe/PyroGramBot/blob/f30e2cca12002121bad1982f68cd0ff9814ce027/pyrobot/helper_functions/extract_user.py#L7
    user_id = None
    user_first_name = None
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        user_first_name = message.reply_to_message.from_user.first_name

    elif len(message.command) > 1:
        if (
            len(message.entities) > 1 and
            message.entities[1].type == enums.MessageEntityType.TEXT_MENTION
        ):
           
            required_entity = message.entities[1]
            user_id = required_entity.user.id
            user_first_name = required_entity.user.first_name
        else:
            user_id = message.command[1]
            # don't want to make a request -_-
            user_first_name = user_id
        try:
            user_id = int(user_id)
        except ValueError:
            pass
    else:
        user_id = message.from_user.id
        user_first_name = message.from_user.first_name
    return (user_id, user_first_name)

def list_to_str(k):
    if not k:
        return "N/A"
    elif len(k) == 1:
        return str(k[0])
    elif MAX_LIST_ELM:
        k = k[:int(MAX_LIST_ELM)]
        return ' '.join(f'{elem}, ' for elem in k)
    else:
        return ' '.join(f'{elem}, ' for elem in k)

def last_online(from_user):
    time = ""
    if from_user.is_bot:
        time += "🤖 Bot :("
    elif from_user.status == enums.UserStatus.RECENTLY:
        time += "Recently"
    elif from_user.status == enums.UserStatus.LAST_WEEK:
        time += "Within the last week"
    elif from_user.status == enums.UserStatus.LAST_MONTH:
        time += "Within the last month"
    elif from_user.status == enums.UserStatus.LONG_AGO:
        time += "A long time ago :("
    elif from_user.status == enums.UserStatus.ONLINE:
        time += "Currently Online"
    elif from_user.status == enums.UserStatus.OFFLINE:
        time += from_user.last_online_date.strftime("%a, %d %b %Y, %H:%M:%S")
    return time


def split_quotes(text: str) -> List:
    if not any(text.startswith(char) for char in START_CHAR):
        return text.split(None, 1)
    counter = 1  # ignore first char -> is some kind of quote
    while counter < len(text):
        if text[counter] == "\\":
            counter += 1
        elif text[counter] == text[0] or (text[0] == SMART_OPEN and text[counter] == SMART_CLOSE):
            break
        counter += 1
    else:
        return text.split(None, 1)

    # 1 to avoid starting quote, and counter is exclusive so avoids ending
    key = remove_escapes(text[1:counter].strip())
    # index will be in range, or `else` would have been executed and returned
    rest = text[counter + 1:].strip()
    if not key:
        key = text[0] + text[0]
    return list(filter(None, [key, rest]))



def gfilterparser(text, keyword):
    if "buttonalert" in text:
        text = (text.replace("\n", "\\n").replace("\t", "\\t"))
    buttons = []
    note_data = ""
    prev = 0
    i = 0
    alerts = []
    for match in BTN_URL_REGEX.finditer(text):
        # Check if btnurl is escaped
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and text[to_check] == "\\":
            n_escapes += 1
            to_check -= 1

        # if even, not escaped -> create button
        if n_escapes % 2 == 0:
            note_data += text[prev:match.start(1)]
            prev = match.end(1)
            if match.group(3) == "buttonalert":
                # create a thruple with button label, url, and newline status
                if bool(match.group(5)) and buttons:
                    buttons[-1].append(InlineKeyboardButton(
                        text=match.group(2),
                        callback_data=f"gfilteralert:{i}:{keyword}"
                    ))
                else:
                    buttons.append([InlineKeyboardButton(
                        text=match.group(2),
                        callback_data=f"gfilteralert:{i}:{keyword}"
                    )])
                i += 1
                alerts.append(match.group(4))
            elif bool(match.group(5)) and buttons:
                buttons[-1].append(InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(4).replace(" ", "")
                ))
            else:
                buttons.append([InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(4).replace(" ", "")
                )])

        else:
            note_data += text[prev:to_check]
            prev = match.start(1) - 1
    else:
        note_data += text[prev:]

    try:
        return note_data, buttons, alerts
    except:
        return note_data, buttons, None





def parser(text, keyword):
    if "buttonalert" in text:
        text = (text.replace("\n", "\\n").replace("\t", "\\t"))
    buttons = []
    note_data = ""
    prev = 0
    i = 0
    alerts = []
    for match in BTN_URL_REGEX.finditer(text):
        # Check if btnurl is escaped
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and text[to_check] == "\\":
            n_escapes += 1
            to_check -= 1

        # if even, not escaped -> create button
        if n_escapes % 2 == 0:
            note_data += text[prev:match.start(1)]
            prev = match.end(1)
            if match.group(3) == "buttonalert":
                # create a thruple with button label, url, and newline status
                if bool(match.group(5)) and buttons:
                    buttons[-1].append(InlineKeyboardButton(
                        text=match.group(2),
                        callback_data=f"alertmessage:{i}:{keyword}"
                    ))
                else:
                    buttons.append([InlineKeyboardButton(
                        text=match.group(2),
                        callback_data=f"alertmessage:{i}:{keyword}"
                    )])
                i += 1
                alerts.append(match.group(4))
            elif bool(match.group(5)) and buttons:
                buttons[-1].append(InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(4).replace(" ", "")
                ))
            else:
                buttons.append([InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(4).replace(" ", "")
                )])

        else:
            note_data += text[prev:to_check]
            prev = match.start(1) - 1
    else:
        note_data += text[prev:]

    try:
        return note_data, buttons, alerts
    except:
        return note_data, buttons, None

def remove_escapes(text: str) -> str:
    res = ""
    is_escaped = False
    for counter in range(len(text)):
        if is_escaped:
            res += text[counter]
            is_escaped = False
        elif text[counter] == "\\":
            is_escaped = True
        else:
            res += text[counter]
    return res


def humanbytes(size):
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'



def get_progress_bar(completed, total, length=10):
    progress = completed / total
    block = int(round(length * progress))
    # 🟩 ചിഹ്നവും ⬜ ചിഹ്നവും ഉപയോഗിച്ച് ബാർ ഉണ്ടാക്കുന്നു
    text = "🟩" * block + "⬜" * (length - block)
    percentage = round(progress * 100, 1)
    return f"[{text}] {percentage}%"

async def broadcast_messages(user_id, message):
    try:
        await message.copy(chat_id=user_id)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await broadcast_messages(user_id, message)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        return False, "Deleted"
    except UserIsBlocked:
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        return False, "Error"
    except Exception:
        return False, "Error"

async def run_broadcast_in_background(client, message, status_msg):
    start_time = time.time()
    success = 0
    blocked = 0
    deleted = 0
    failed = 0

    all_users_cursor = await db.get_all_users()
    total_users = await db.total_users_count() # ആകെ യൂസർമാരുടെ എണ്ണം
    
    if total_users == 0:
        await status_msg.edit("❌ ഡാറ്റാബേസിൽ യൂസർമാർ ആരും തന്നെയില്ല!")
        return

    processed = 0
    async for user in all_users_cursor:
        user_id = user.get('id')
        if not user_id:
            continue
            
        is_sent, result = await broadcast_messages(int(user_id), message)
        
        if is_sent:
            success += 1
        elif result == "Blocked":
            blocked += 1
        elif result == "Deleted":
            deleted += 1
        else:
            failed += 1
            
        processed += 1
        
        # ഓരോ 10 യൂസർമാർ കഴിയുമ്പോഴും ടെലിഗ്രാമിലെ മെസ്സേജ് ലൈവ് ആയി പ്രോഗ്രസ് ബാർ സഹിതം അപ്‌ഡേറ്റ് ചെയ്യും
        if processed % 10 == 0 or processed == total_users:
            bar = get_progress_bar(processed, total_users)
            progress_text = (
                f"📢 **ബ്രോഡ്കാസ്റ്റിംഗ് പുരോഗമിക്കുന്നു...**\n\n"
                f"📊 Progress: {bar}\n"
                f"⏳ അയച്ചത്: {processed} / {total_users}\n\n"
                f"👍 വിജയിച്ചത്: {success}\n"
                f"🚫 ബ്ലോക്ക് ചെയ്തവർ: {blocked}\n"
                f"💀 ഡിലീറ്റ് ആയവർ: {deleted}"
            )
            try:
                await status_msg.edit(progress_text)
            except Exception:
                pass
                
        await asyncio.sleep(0.5)

    # ബ്രോഡ്കാസ്റ്റ് പൂർണ്ണമായി കഴിഞ്ഞാൽ വരാനുള്ള FINAL TEXT
    end_time = time.time()
    time_taken = round(end_time - start_time, 2)

    final_text = (
        f"✅ **ബ്രോഡ്കാസ്റ്റ് വിജയകരമായി പൂർത്തിയായി!**\n\n"
        f"⏱️ എടുത്ത സമയം: {time_taken} സെക്കന്റ്\n"
        f"👥 ആകെ യൂസർമാർ: {total_users}\n\n"
        f"👍 വിജയിച്ചത്: {success}\n"
        f"🚫 ബ്ലോക്ക് ചെയ്തവർ: {blocked}\n"
        f"💀 അക്കൗണ്ട് ഡിലീറ്റ് ആയവർ: {deleted}\n"
        f"❌ പരാജയപ്പെട്ടത്: {failed}"
    )
    try:
        await status_msg.edit(final_text)
    except Exception:
        pass
