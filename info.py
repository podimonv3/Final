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
OMDB_API_KEY = os.environ.get("OMDB_API_KEY", "65f7219f")
DEFAULT_POSTER = os.environ.get("DEFAULT_POSTER", "https://files.catbox.moe/oryxah.jpg")
SPELL_IMG = os.environ.get("SPELL_IMG", "https://files.catbox.moe/yt159d.jpg")
FANART_API_KEY = os.environ.get("FANART_API_KEY", "d56b45eb243c31ca1229bd37813e66d8")




# TMDB API Keys (കോമ ഇട്ട് എത്ര കീകൾ വേണമെങ്കിലും നൽകാം)
TMDB_API_KEYS = os.environ.get("TMDB_API_KEYS", "7a11f792bc13f275b6831932eb85bfa4,5f28978232d6d780d64dd0d0e0bbe2f2,a992c5a043c61edf1ce9d3e74d7a0aca")

# OMDb API Keys (ഇതുപോലെ കോമ ഇട്ട് നൽകുക)
OMDB_API_KEYS = os.environ.get("OMDB_API_KEYS", "4b4d1a5f,5d94dd20,4c6f039d")


# Bot information
SESSION = environ.get('SESSION', 'autodelete')
API_ID = int(environ.get("API_ID", "19071424"))
API_HASH = environ.get("API_HASH", "c4b3e298cc50fd4cc563ae75ee882948")
BOT_TOKEN = environ.get("BOT_TOKEN", "7466979295:AAG6UlB81Q7COPbHprOSvGmJ4DxILjW-VW4")

# Bot settings
CACHE_TIME = int(environ.get('CACHE_TIME', 60))
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


# Koyeb Config Vars-ൽ നിന്ന് ലിങ്ക് എടുക്കുന്നു, ഇല്ലെങ്കിൽ ബാക്കപ്പ് ആയി രണ്ടാമത്തെ ലിങ്ക് ഉപയോഗിക്കും
POSTER_DB = os.environ.get("POSTER_DB", "mongodb+srv://sreejithskumar9387_db_user:vi93eYFWbLSIedyV@cluster0.hxzaxzb.mongodb.net/?appName=Cluster0")

# Auto approve
CHAT_ID = [int(app_chat_id) if id_pattern.match(app_chat_id) else app_chat_id for app_chat_id in environ.get('CHAT_ID', '-1002303772763').split()]
TEXT = environ.get("APPROVED_WELCOME_TEXT", "Hello {mention}\nWelcome To {title}\n\nYour request has been approved")
APPROVED = environ.get("APPROVED_WELCOME", "off").lower()

# peer id fix 
pyroutils.MIN_CHAT_ID = -999999999999
pyroutils.MIN_CHANNEL_ID = -100999999999999

# info.py ഫയലിൽ ഈ രീതിയിൽ നൽകാം
# ================= NEW TAGS FROM SECOND LIST =================

TAGS = [
    "dvdwap.com", "Dvdworld", "DVDWORLD", "DVDWO", "KC", "KC_", "MF", "MLM", "MZone", "MoviezzClub", "HDMVCOUNTER",
    "A2MOVIES", "HDTCPREDVDFILES",

    "@ADrama_Lovers", "@AVA", "@BM_Links", "@CC", "@CC_All", "@CC_ALL_MOVIES2", "@CC_NEW", "@CC_X265",
    "@CCineClub", "@CCM", "@CE_Links", "@CMEHD", "@CR_Rockers", "@cinecom88", " @Cinematic_world", "@Cinema Company", " @cinema_company", "@Cinema_Company", "@CINEMA_BUDDIES", "@Country_Fellows",
    "@Cinema_Kottaka", "@cinema library", "@CKMovies", "@CK_HEVC", "@CK_Moviez", "CT™️", "@CelluloidCineClub", " @colorkannadi_movies", "@C_V", "@CVM", "@DailyMovieZhunt", "@desimovies", "@DK_Drama", "@DM_LinkZzzz",
    "@DMovies", "@DramaOST", "@Dubbedmovies", " @DVDWOALL", "@DvdWap", "@E4E", "@E4E_Rockers", "@FBM_x265", "@FBM_HW", "@FBM_New", "@FILIMHOUSE",
    "@FilmCage", "@Film_Kottaka", "@FrediesChannel", "@HEVC_Cinemaz", "@IM",
    "@HEVC_Moviesz", "@HOREK_ROKOM", "@Hk", "@IndianMoviez", "@KBO", "@KD_Deck", "@KGRockers",
    "@KW", "@KR", "@KannadaWarriors", "@KeralaBoxOffice", "@KL_ROCKERZ", "@Links2U", "@Linkz_MM", "@ᒪᕈT",
    "@M_Zone", "@mobile_mm", "Malayalam_Full_Movie", "@Mallu_Movies", "@malayalam movies", "@MAASFILE", "@MC", "@MC_4U", "@MinaKaze", "@MJ_Linkz", "@MJ_Moviez", "@MM", "@MM_Movies", "@MM_Linkz",
    "@MM_NEW", "@MM_ALL", "@MM_TvSeries", "@MOVIEHUNT", "@MOVIEZMOB", "@MPC", "@MalluRockers",
    "@Mallu_Rockers", "@Mc_South", "@MovieWorld2000", "@Movie_Hub", " @MM_Linkz", "@bheeshmat",
    "@desimovies Telegram", "@favio", "@film_down_load", "@iMediaShare",
    "@infotainmentmedia", "@kickass_torrents", "@msp", "@moviescollection17",
    "@moviesdeveloper", "@MoviesTop10", "@MoviesWar", "@myflixx", "@nanacinemas", "@OB", "PDisk", "@PIT", "@PM",
    "@PM_Old", "@Qualitymovies", "@R_A_R_B_G", "@RickyChannel", "@RatedRMovies", "@Sky_MoviesHD", " @sherlibrary", "@SY_MS", "@telugu_moviez", "@TG UPDATES1",
    "@TN60_LinkzZ", "@TEAMxKL", "@TV 30NAMA1", "@TamilDubbs", "@TamilMV", "@TGmovie9", "@TamilMV_Live", "@TamilRockers",
    "@Tamil_HD_Movies_Requests", "@Tamil_Linkz", "Tamil_LinkZz", "@Tamil_LinkzZ", "@Tamil_Seriesz", "@TeamHDT", "@Team_HDT",
    "@Team_Hevc", "@Theprofffesorr", "@TR_Moviez", "@TR_Updates", "@Tv2Us",
    "@TvSeriesBay", "@UCDump", "@VR", "www_Movcr_cc", "@WMR", "@WorldCinemaToday", "@X265 E4E", "@YTSLT",
    "@cinemaheist", "@trolldcompany", "@yamandanmovies", "@Zee_Keralam_HD", "F&T",

    "www.",
    "www_DVDWap_Com_",
    "www_TamilMV_pw",
    "www_1TamilMV",
    "www_1TamilMV_fun",
    "www_1TamilMV_rodeo",
    "www_1TamilMV_fans",
    "www_1TamilMV_nl",
    "www_1TamilMV_art",
    "www_1TamilMV_org",
    "www_1TamilMV_eu",
    "www_1TamilMV_men",
    "www_1TamilMV_wtf",
    "www_1TamilMV_city",
    "www_1TamilMV_cafe",
    "www_1TamilMV_help",
    "www_1TamilMV_im",
    "www_1TamilMV_phd",
    "www_1TamilMV_one",
    "www_1TamilMV_guru",
    "www_1TamilMV_us",
    "www_1TamilMV_live",
    "www_1TamilMV_pw",
    "www_1TamilMV_life",
    "www_1TamilMV_me",
    "www_1TamilMV_vin",
    "www_1TamilMV_sbs",
    "www_1TamilMV_mx",
    "www_1TamilMV_team",
    "www_1TamilMV_cyou",
    "www_1TamilMV_pics",
    "www_1TamilMV_click",
    "www_1TamilMV_pro",
    "www_1TamilMV_lease",
    "www_1TamilMV_rocks",
    "www_1TamilMV_meme",
    "www_1TamilMV_ing",
    "www_1TamilMV_pizza",
    "www_1TamilMV_li",
    "www_1TamilMV_top",
    "www_1TamilMV_promo",
    "www_1TamilMV_gs",
    "www_1TamilMV_bio",
    "www_1TamilMV_xyz",

    "www.1TamilBlasters.dad",
    "www.1TamilMV.ac",
    "www.1TamilMV.cafe",
    "www.1TamilMV.eu",
    "www.1TamilMV.fans",
    "www.1TamilMV.fun",
    "www.1TamilMV.gold",
    "www.1TamilMV.gs",
    "www.1TamilMV.help",
    "www.1TamilMV.im",
    "www.1TamilMV.ing",
    "www.1TamilMV.lease",
    "www.1TamilMV.li",
    "www.1TamilMV.life",
    "www.1TamilMV.me",
    "www.1TamilMV.men",
    "www.1TamilMV.meme",
    "www.1TamilMV.mx",
    "www.1TamilMV.nl",
    "www.1TamilMV.one",
    "www.1TamilMV.org",
    "www.1TamilMV.phd",
    "www.1TamilMV.pics",
    "www.1TamilMV.pizza",
    "www.1TamilMV.pro",
    "www.1TamilMV.prof",
    "www.1TamilMV.promo",
    "www.1TamilMV.pw",
    "www.1TamilMV.rodeo",
    "www.1TamilMV.rocks",
    "www.1TamilMV.sbs",
    "www.1TamilMV.team",
    "www.1TamilMV.top",
    "www.1TamilMV.us",
    "www.1TamilMV.vin",
    "www.1TamilMV.wf",
    "www.1TamilMV.wtf",
    "www.1TamilMV.xyz",
    "www.1TamilMV.bio",

    "@mfmixsouth",
]
# Others
LONG_IMDB_DESCRIPTION = is_enabled(environ.get("LONG_IMDB_DESCRIPTION", "False"), False)
MAX_LIST_ELM = int(environ.get("MAX_LIST_ELM", 5))
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
