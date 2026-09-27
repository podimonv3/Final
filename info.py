import re
from os import environ
from Script import script
from pyrogram import utils as pyroutils

# ടെലിഗ്രാം ഐഡികൾ കൃത്യമായി തിരിച്ചറിയാൻ ഈ പാറ്റേൺ ഉപയോഗിക്കുക (Fixed)
id_pattern = re.compile(r'^-?\d+$')

def is_enabled(value, default):
    if value.lower() in ["true", "yes", "1", "enable", "y"]:
        return True
    elif value.lower() in ["false", "no", "0", "disable", "n"]:
        return False
    else:
        return default


import os

# നിലവിലുള്ള മറ്റ് വേരിയബിളുകൾക്ക് താഴെ ഇത് ചേർക്കുക:
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "5f28978232d6d780d64dd0d0e0bbe2f2")
OMDB_API_KEY = os.environ.get("OMDB_API_KEY", "3feaa2f6")
DEFAULT_POSTER = os.environ.get("DEFAULT_POSTER", "https://files.catbox.moe/oryxah.jpg")


# Bot information
SESSION = environ.get('SESSION', 'autodelete')
API_ID = int(environ.get("API_ID", "19071424"))
API_HASH = environ.get("API_HASH", "c4b3e298cc50fd4cc563ae75ee882948")
BOT_TOKEN = environ.get("BOT_TOKEN", "7466979295:AAG6UlB81Q7COPbHprOSvGmJ4DxILjW-VW4")

# Bot settings
CACHE_TIME = int(environ.get('CACHE_TIME', 300))
USE_CAPTION_FILTER = bool(environ.get('USE_CAPTION_FILTER', False))
PICS = (environ.get('PICS', 'https://telegra.ph https://telegra.ph https://telegra.ph https://telegra.ph https://telegra.ph https://telegra.ph https://telegra.ph https://telegra.ph https://telegra.ph https://telegra.ph https://telegra.ph https://telegra.ph https://telegra.ph https://telegra.ph https://telegra.ph https://telegra.ph')).split()

# Admins, Channels & Users
ADMINS = [int(admin) if id_pattern.match(admin) else admin for admin in environ.get('ADMINS', '7425490417 5032034594').split()]
CHANNELS = [int(ch) if id_pattern.match(ch) else ch for ch in environ.get('CHANNELS', '-1002252582164 -1002397004421').split()]
auth_users = [int(user) if id_pattern.match(user) else user for user in environ.get('AUTH_USERS', '').split()]
AUTH_USERS = (auth_users + ADMINS) if auth_users else []
auth_grp = environ.get('AUTH_GROUP')
AUTH_GROUPS = [int(ch) for ch in auth_grp.split()] if auth_grp else None

# REQ_CHANNEL കോഡ് ലളിതമാക്കിയത് (Fixed & Cleaned)
req_ch1 = environ.get("REQ_CHANNEL1")
REQ_CHANNEL1 = int(req_ch1) if (req_ch1 and id_pattern.match(req_ch1)) else False

req_ch2 = environ.get("REQ_CHANNEL2")
REQ_CHANNEL2 = int(req_ch2) if (req_ch2 and id_pattern.match(req_ch2)) else False

# MongoDB information
DATABASE_URI = environ.get('DATABASE_URI', "mongodb+srv://gimilat757:0wiQwyG8cIRJOmXs@cluster0.f2qk2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DATABASE_URI2 = environ.get('DATABASE_URI2', "mongodb+srv://sushankm16:4i1WAfPYKWyqPIDD@cluster0.sngp9pz.mongodb.net/?retryWrites=true&w=majority")
DATABASE_URI3 = environ.get('DATABASE_URI3', "mongodb+srv://sushankm16:4i1WAfPYKWyqPIDD@cluster0.sngp9pz.mongodb.net/?retryWrites=true&w=majority")
DATABASE_NAME = environ.get('DATABASE_NAME', "MammoottyV1")
COLLECTION_NAME = environ.get('COLLECTION_NAME', 'mcu_files')

# Auto approve
CHAT_ID = [int(app_chat_id) if id_pattern.match(app_chat_id) else app_chat_id for app_chat_id in environ.get('CHAT_ID', '-1002303772763').split()]
TEXT = environ.get("APPROVED_WELCOME_TEXT", "Hello {mention}\nWelcome To {title}\n\nYour request has been approved")
APPROVED = environ.get("APPROVED_WELCOME", "off").lower()

# peer id fix 
pyroutils.MIN_CHAT_ID = -999999999999
pyroutils.MIN_CHANNEL_ID = -100999999999999

# info.py ഫയലിൽ ഈ രീതിയിൽ നൽകാം
TAGS = [
    "@FBM_New", "@FBM_HW", "@FBM", "@FBM_Tamil", "@FBM_x265", "[KMH]", "@FBM_ALL",
    "@mobile_mm", "@Mallu_Hub", "[HN]", "PDisk", "@VR", "@CC_New", "@CC_Links",
    "@CC_ALL", "@tollywoodz", "[KML]", "RWD", "[@WORD_MOVIS]", "@360", "@cinema_company",
    "@Cinematic_world", "@CC", "@CK_HEVC", "@koreanjournal", "@CK_Moviez", "[TC]", "@cinema library",
    "[F&T]", "HDMVCOUNTER", "@C_V", "@KL_ROCKERZ", "@MM_New", "MM_New", "@MM_ALL",
    "@MM_X265", "[MM-New]", "@MM_Linkz", "@MM", "[MM]", "MLM", "@E4E",
    "@RickyChannel", "ғαιвεяsgαтє", "Tamil_LinkZz", "@MPC", "://tamilrockers.com", "www_1TamilMV_art", "[CF]",
    "[CC]", "@PM", "[TIF]", "@desimovies", "@telugu_moviez", "[A2MOVIES]", "@CCM",
    "@malayalam movies", "@CE_Links", "@WMR", "@ᒪᕈT", "@TeamHDT", "@MoviesTop10", "@colorkannadi_movies",
    "@DVDWOALL", "DVDWORLD", "Malayalam_Full_Movie", "DVDWO", "@KR", "@Sharathrockers", "@HindiHDmovies",
    "@I_M_D_B", "@moviesclub1234", "@mclubb_subtitles", "@mclubb", "@CVM",
    "@filmreview", "【CP】", "[ᎡTemporary]", "TIF_HW", "@Ma_Cartoonzz", "@Mj_Linkz", "@AM", "@HEVC_MoviesZ",
    "@CV", "Dvdworld", "@movieworldkdY", "@Adult_MovieX", "@Rarefilms", "@CK",
    "[WMJ]", "@SY_MS", "@Mallu_Movies", "@BM_Links", "@CC_Telugu",
    "[Hotstar_Tamil]", "[DnO]", "(@desimovies Telegram)", "[DFBC]", "[US]", "@Cinema_Villa",
    "@CMVLA", "@TamilAnimationToday", "[ML]", "[USA]", "[HEVC]", "@HMF", "[FC]", "@MJ_HEVC",
    "@MM_OLD", "@FBM_Dubbed", "NewHDMovies", "[MC_Moviecentral]",
    "Malayalam_Comedy_Movie", "@CiNEWOD", "@MalluRockerZz", "(@UCMOVIE)", "MAPTAP_TEAM", "[CT™]", "@MoviezzClub",
    "@butterfly_media", "@Mp4Mania", "[MSM]", "[CT™️]", "@SUBTLESUBS", "@TR", "E4E", "@FC_HEVC",
    "Full Movie", "@Moviezwen", "[TG @FILMFEVE]", "@Mx Links",
    "@EE", "@CPR", "[MASHOBUC]", "[YDF]", "CG", "@McParadiso", "@FilmBuzzMedia",
    "@CL", "@MT", "ML", "NewRelease",
    "സിനിമാ_കലവറ", "🎞", "www_1tamilmv_lease",
    "@CineMallu_Linkz",
    "TamilYogi.vip",
    "[Movie Bazar]", "Movie Bazar", "[MF]", "@MoViezOnlYheRe", "[GC]", "GC",
    "@HEVCHubX", "@HPC_Telegram", "@LinkZz_MBBS", "[D&O]", "[PF]", "@DramaOST", "Tg @MoviesHunt",
    "@HDMovies", "[MJ]", "@IM", "@PVRCinemas", "@M©", "[DD]", "[@ML_Linkz]",
    "@sherlibrary", "@M3", "@MCSouth", "@Movie_Blasters1", "@MCArchives", "[TM]",
    "www_1tamilmv_", "HDTCPREDVDFILES"
]

# Others
LONG_IMDB_DESCRIPTION = is_enabled(environ.get("LONG_IMDB_DESCRIPTION", "False"), False)

LOG_CHANNEL = int(environ.get('LOG_CHANNEL', "-1002332361885"))
DELETE_CHANNELS = [int(dch) if id_pattern.match(dch) else dch for dch in environ.get('DELETE_CHANNELS', '-1002354592029').split()]
SUPPORT_CHAT = environ.get('SUPPORT_CHAT', 'mcumovies')
P_TTI_SHOW_OFF = is_enabled((environ.get('P_TTI_SHOW_OFF', "False")), False)
SINGLE_BUTTON = is_enabled((environ.get('SINGLE_BUTTON', "True")), True)
CUSTOM_FILE_CAPTION = environ.get("CUSTOM_FILE_CAPTION", f"{script.CUSTOM_FILE_CAPTION}")
BATCH_FILE_CAPTION = environ.get("BATCH_FILE_CAPTION", CUSTOM_FILE_CAPTION)
SPELL_CHECK_REPLY = is_enabled(environ.get("SPELL_CHECK_REPLY", "True"), True)
INDEX_REQ_CHANNEL = int(environ.get('INDEX_REQ_CHANNEL', LOG_CHANNEL))
FILE_STORE_CHANNEL = [int(ch) for ch in (environ.get('FILE_STORE_CHANNEL', '-1003737995666')).split()]
MELCOW_NEW_USERS = is_enabled((environ.get('MELCOW_NEW_USERS', "False")), False)
PROTECT_CONTENT = is_enabled((environ.get('PROTECT_CONTENT', "False")), False)
PUBLIC_FILE_STORE = is_enabled((environ.get('PUBLIC_FILE_STORE', "False")), False)

LOG_STR = ""
