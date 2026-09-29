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
from info import TMDB_API_KEY, OMDB_API_KEY, DEFAULT_POSTER, LONG_IMDB_DESCRIPTION, MAX_LIST_ELM
import requests
import asyncio
from bs4 import BeautifulSoup
import aiohttp
import httpx

try:
    import imdbio as _imdbio
    from imdbio.exceptions import ImdbioError as _ImdbioError
    IMDBIO_AVAILABLE = True
except ImportError:
    IMDBIO_AVAILABLE = False


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


# 1. TMDB Async
async def get_tmdb_poster(movie_name, tmdb_api_key):
    try:
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={tmdb_api_key}&query={urllib.parse.quote(movie_name)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, timeout=5) as response:
                if response.status != 200:
                    return None
                data = await response.json()

            if not data.get("results"):
                return None

            movie = data["results"][0]
            movie_id = movie.get("id")

            if movie_id:
                images_url = f"https://api.themoviedb.org/3/movie/{movie_id}/images?api_key={tmdb_api_key}"
                async with session.get(images_url, timeout=5) as response:
                    if response.status == 200:
                        images = await response.json()

                        backdrops = images.get("backdrops", [])
                        if backdrops:
                            backdrops.sort(key=lambda x: x.get("vote_average", 0), reverse=True)
                            path = backdrops[0].get("file_path")
                            if path:
                                return f"https://image.tmdb.org/t/p/w1280{path}"

            poster_path = movie.get("poster_path")
            if poster_path:
                return f"https://image.tmdb.org/t/p/w500{poster_path}"

    except Exception as e:
        logger.warning(f"TMDB poster error for '{movie_name}': {e}")

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



async def get_any_movie_poster(movie_name):
    # 2. TMDB - Landscape Backdrop
    if TMDB_API_KEY:
        poster = await get_tmdb_poster(
            movie_name,
            TMDB_API_KEY
        )
        if poster:
            return poster

   
    # 4. OMDb - Portrait Poster (last fallback)
    if OMDB_API_KEY:
        poster = await get_omdb_poster(
            movie_name,
            OMDB_API_KEY
        )
        if poster:
            return poster

    # 5. Nothing found
    return None



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
 


class _OmdbFakeMovie:
    """Wraps an OMDb search-result dict to match Cinemagoer's object interface."""
    def __init__(self, m):
        self._m = m
        self.movieID = f"omdb_{m.get('imdbID')}"
    def get(self, k, default=None):
        _map = {'title': 'Title', 'year': 'Year', 'kind': 'Type'}
        return self._m.get(_map.get(k, k), default)


class _ImdbioFakeMovie:
    """Wraps an imdbio MovieBriefInfo search result to match Cinemagoer's object interface."""
    def __init__(self, m):
        self._m = m
        self.movieID = f"imdbio_{m.imdb_id}"
    def get(self, k, default=None):
        if k == 'title':
            return self._m.title or default
        if k == 'year':
            return self._m.year or default
        if k == 'kind':
            return self._m.kind or default
        return default


def _names(people):
    """Turn a list of imdbio Person/CastMember objects into a joined name string."""
    try:
        names = [p.name for p in people if getattr(p, "name", None)]
    except (TypeError, AttributeError):
        return "N/A"
    return list_to_str(names) if names else "N/A"


def _cat(m, key):
    """Safely pull a named category (writer, producer, ...) off an imdbio MovieDetail."""
    try:
        return _names(m.categories.get(key, []))
    except (AttributeError, TypeError):
        return "N/A"

async def _imdbio_search(title, year=None, bulk=False):
    """Search movies/shows via imdbio (no API key required)."""
    if not IMDBIO_AVAILABLE:
        return None
    try:
        result = await asyncio.to_thread(_imdbio.search_title, title, year=year)
    except _ImdbioError:        
        return None
    except TypeError:
        # upstream bug ലോഗ് ചെയ്യുന്നത് ഒഴിവാക്കി
        return None
    except Exception:
        # മറ്റെല്ലാ അപ്രതീക്ഷിത എറർ ലോഗുകളും ഒഴിവാക്കി
        return None

    if not result or not result.titles:
        return None
    if bulk:
        return [_ImdbioFakeMovie(t) for t in result.titles[:10]]
    return await _imdbio_get_details(result.titles[0].imdb_id)


async def _imdbio_get_details(imdb_id):
    """Fetch full details via imdbio by IMDb ID."""
    if not IMDBIO_AVAILABLE:
        return None
    if isinstance(imdb_id, str) and imdb_id.startswith("imdbio_"):
        imdb_id = imdb_id[len("imdbio_"):]
    try:
        m = await asyncio.to_thread(_imdbio.get_movie, imdb_id)
    except _ImdbioError as e:
        logger.warning(f"imdbio details error: {e}")
        return None
    except Exception as e:
        logger.exception(f"imdbio details unexpected error: {e}")
        return None
    if not m:
        return None

    plot = m.plot or "N/A"
    if not LONG_IMDB_DESCRIPTION and plot and plot != "N/A" and len(plot) > 800:
        plot = plot[:800] + "..."

    try:
        seasons = len(m.info_series.display_seasons) if getattr(m, "info_series", None) else None
    except (AttributeError, TypeError):
        seasons = None

    try:
        cast = _names(m.categories.get("cast", []))
        if cast == "N/A":
            cast = _names(m.stars)
    except (AttributeError, TypeError):
        cast = _names(m.stars) if getattr(m, "stars", None) else "N/A"

    try:
        box_office = (m.box_office or {}).get("cumulativeWorldwideGross") \
            or (m.box_office or {}).get("grossWorldwide") \
            or m.worldwide_gross or "N/A"
    except (AttributeError, TypeError):
        box_office = "N/A"

    return {
        'title': m.title or "N/A",
        'votes': str(m.votes) if m.votes else "N/A",
        "aka": list_to_str(m.title_akas) if getattr(m, "title_akas", None) else "N/A",
        "seasons": seasons,
        "box_office": box_office,
        'localized_title': m.title_localized or m.title or "N/A",
        'kind': "tv series" if m.is_series() else ("episode" if m.is_episode() else "movie"),
        "imdb_id": m.imdb_id or "N/A",
        "cast": cast,
        "runtime": f"{m.duration} min" if getattr(m, "duration", None) else "N/A",
        "countries": list_to_str(m.countries) if getattr(m, "countries", None) else "N/A",
        "certificates": m.mpaa or m.certificate or "N/A",
        "languages": list_to_str(m.languages_text or m.languages) if (getattr(m, "languages_text", None) or getattr(m, "languages", None)) else "N/A",
        "director": _names(m.directors) if getattr(m, "directors", None) else "N/A",
        "writer": _cat(m, "writer"),
        "producer": _cat(m, "producer"),
        "composer": _cat(m, "composer"),
        "cinematographer": _cat(m, "cinematographer"),
        "music_team": "N/A",
        "distributors": "N/A",
        'release_date': m.release_date or "N/A",
        'year': str(m.year) if m.year else "N/A",
        'genres': list_to_str(m.genres) if getattr(m, "genres", None) else "N/A",
        'poster': _hq_poster(m.cover_url),
        'plot': plot,
        'rating': str(m.rating) if m.rating else "N/A",
        'url': m.url or (f"https://www.imdb.com/title/{m.imdb_id}/" if m.imdb_id else "N/A"),
        'trailers': list(m.trailers) if getattr(m, "trailers", None) else [],
        '_source': 'imdbio',
    }

def _hq_poster(url):
    """OMDb poster URLs point at Amazon's image CDN with a size-limiting suffix
    like '._V1_SX300.jpg'. Stripping that suffix returns the original, full-res image."""
    if not url or url == "N/A":
        return None
    return re.sub(r'\._[A-Z0-9,]+_(?=\.\w+$)', '', url)


async def fetch_poster_bytes(url):
    """Download a poster image ourselves and return raw bytes, or None on failure.
    Telegram's own reply_photo(photo=<url>) sometimes fails (CDN blocks Telegram's
    fetcher, size/dimension limits) even when the URL is perfectly loadable from a
    normal browser/HTTP client — downloading it ourselves and uploading the bytes
    sidesteps that."""
    if not url:
        return None
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
    try:
        async with httpx.AsyncClient(timeout=15, headers=headers, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.content
    except Exception as e:
        logger.warning(f"poster download failed: {e}")
        return None


async def _omdb_search(title, year=None, bulk=False):
    """Search movies/shows via OMDb."""
    if not OMDB_API_KEY:
        logger.warning("OMDB_API_KEY not set, cannot search OMDb")
        return None
    try:
        params = {"apikey": OMDB_API_KEY, "s": title}
        if year:
            params["y"] = year
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("https://www.omdbapi.com/", params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.exception(f"omdb search error: {e}")
        return None

    if data.get("Response") != "True":
        return None
    results = data.get("Search", [])
    if not results:
        return None
    if bulk:
        return [_OmdbFakeMovie(r) for r in results[:10]]
    return await _omdb_get_details(results[0]["imdbID"])

async def _omdb_get_details(imdb_id):
    """Fetch full details via OMDb by IMDb ID."""
    if not OMDB_API_KEY:
        return None
    if isinstance(imdb_id, str) and imdb_id.startswith("omdb_"):
        imdb_id = imdb_id[len("omdb_"):]
    try:
        params = {"apikey": OMDB_API_KEY, "i": imdb_id, "plot": "full" if LONG_IMDB_DESCRIPTION else "short"}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("https://www.omdbapi.com/", params=params)
            resp.raise_for_status()
            m = resp.json()
    except Exception as e:
        logger.exception(f"omdb details error: {e}")
        return None
    if not m or m.get("Response") != "True":
        return None

    plot = m.get("Plot") or "N/A"
    if not LONG_IMDB_DESCRIPTION and plot and len(plot) > 800:
        plot = plot[:800] + "..."

    def _split(field):
        v = m.get(field)
        if not v or v == "N/A":
            return "N/A"
        return list_to_str([p.strip() for p in v.split(",")])

    return {
        'title': m.get("Title", "N/A"),
        'votes': m.get("imdbVotes", "N/A"),
        "aka": "N/A",
        "seasons": m.get("totalSeasons"),
        "box_office": m.get("BoxOffice", "N/A"),
        'localized_title': m.get("Title", "N/A"),
        'kind': "tv series" if m.get("Type") == "series" else "movie",
        "imdb_id": m.get("imdbID", "N/A"),
        "cast": _split("Actors"),
        "runtime": m.get("Runtime", "N/A"),
        "countries": _split("Country"),
        "certificates": m.get("Rated", "N/A"),
        "languages": _split("Language"),
        "director": _split("Director"),
        "writer": _split("Writer"),
        "producer": "N/A",
        "composer": "N/A",
        "cinematographer": "N/A",
        "music_team": "N/A",
        "distributors": "N/A",
        'release_date': m.get("Released", "N/A"),
        'year': m.get("Year", "N/A"),
        'genres': _split("Genre"),
        'poster': _hq_poster(m.get("Poster")),
        'plot': plot,
        'rating': m.get("imdbRating", "N/A"),
        'url': f"https://www.imdb.com/title/{m.get('imdbID')}/" if m.get("imdbID") else "N/A",
        'trailers': [],  # OMDb has no trailer data
        '_source': 'omdb',
    }
    
async def get_poster(query, bulk=False, id=False, file=None):
    # ── Direct ID lookups ────────────────────────────────────────────────────
    if id:
        result = await _imdbio_get_details(query)
        if result:
            return result
        return await _omdb_get_details(query)

    # ── Parse title + year ───────────────────────────────────────────────────
    query = (query.strip()).lower()
    title = query
    year = re.findall(r'[1-2]\d{3}$', query, re.IGNORECASE)
    if year:
        year = list_to_str(year[:1])
        title = (query.replace(year, "")).strip()
    elif file is not None:
        year = re.findall(r'[1-2]\d{3}', file, re.IGNORECASE)
        if year:
            year = list_to_str(year[:1])
    else:
        year = None

    result = await _imdbio_search(title, year=year, bulk=bulk)
    if result:
        return result
    return await _omdb_search(title, year=year, bulk=bulk)


def list_to_str(k, max_elm=5):  # ഇവിടെ 5 ആണ് DEFAULT വാല്യൂ
    if not k:
        return "N/A"
    
    # ലിസ്റ്റിന്റെ നീളം ഡിഫോൾട്ട് വാല്യൂവിനേക്കാൾ കൂടുതലാണെങ്കിൽ മാത്രം മുറിക്കുക
    if len(k) > max_elm:
        k = k[:max_elm]
        
    # എലമെന്റുകൾക്കിടയിൽ കൃത്യമായി കോമ വരാൻ ', '.join() ഉപയോഗിക്കാം
    return ', '.join(str(elem) for elem in k)


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
