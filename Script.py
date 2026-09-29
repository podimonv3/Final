class script(object):
    START_TXT = """<blockquote><b>Welcome {},</b></blockquote>

<i>This is an automated movie delivery system built exclusively for our official community.</i>
<i>If Any Bug Please Contact Admins 👇
<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>
<a href="https://t.me/Adhityan_edavattom">Admin™ I</a></i>
<a href="https://t.me/SreejithSKumar">Admin™ II</a></i>
<a href="https://t.me/Akhilkrishnan121">Admin™ III</a></i>
<a href="https://t.me/Promoviesearcher_bot">Admin™ IV</a></i>
<a href="https://t.me/Roopak_raj">Admin™ V</a></i>
<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>
<b>Powered by:</b>
<u><b><i><a href="https://t.me/UrvashiTheaters_Main">𝐓𝐞𝐚𝐦 𝐔𝐫𝐯𝐚𝐬𝐡𝐢 𝐓𝐡𝐞𝐚𝐭𝐞𝐫𝐬™️</a></u></b></i>"""

    SPELL_TEXT = """<b><i><u>🚸നിർദ്ദേശങ്ങൾ🚸</u></b></i>
<b><i>🌿 ᴄʜᴇᴄᴋ ᴛʜᴇ ꜱᴘᴇʟʟɪɴɢ—ʙᴜᴛ ᴏɴʟʏ ɪꜰ ᴛʜᴀᴛ ᴍᴏᴠɪᴇ ʜᴀꜱ ʜᴀᴅ ᴀɴ ᴏᴛᴛ ʀᴇʟᴇᴀꜱᴇ.</b></i></blockquote>"""

    OTT_TEXT = """<b><i><u>🚸നിർദ്ദേശങ്ങൾ🚸</u></b></i>
<b><i> 🌿 OTT റിലീസ് ആവാത്ത മൂവീസ് ചോദിച്ചു സമയം കളയണ്ട കിട്ടില്ല 👀
🍃 OTT NOT Available 
 🌿 request ചെയ്തോളൂ.. request ചെയ്യും മുൻപ് rules വായിക്കുന്നത് നല്ലതായിരിക്കും</b></i></blockquote>"""


    JOIN_TXT = """⚠️ <b>Access Restricted / പ്രവേശന അനുമതി നിഷേധിക്കപ്പെട്ടിരിക്കുന്നു</b>

<blockquote>To successfully receive your requested movie, you must join both of our official channels listed below.

നിങ്ങൾ തിരഞ്ഞ സിനിമ ലഭിക്കുന്നതിനായി താഴെ നൽകിയിരിക്കുന്ന രണ്ട് ഔദ്യോഗിക ചാനലുകളിലും നിർബന്ധമായും ജോയിൻ ചെയ്യേണ്ടതുണ്ട്.</blockquote>

📌 <b>Important Instructions / പ്രധാന നിർദ്ദേശം:</b>
1. Click and join the <b>First Channel</b>.
2. Wait for <b>2 seconds</b>.
3. Then click and join the <b>Second Channel</b>.

<i>👉 ആദ്യം ഒന്നാമത്തെ ചാനലിൽ ജോയിൻ ചെയ്ത ശേഷം 2 സെക്കൻഡ് കാത്തിരിക്കുക, അതിനുശേഷം മാത്രം രണ്ടാമത്തെ ചാനലിൽ ജോയിൻ ചെയ്യുക.</i>

<b>⚡ Powered by:</b>
👉 <i><a href="https://t.me/UrvashiTheaters_Main">© Team Urvashi Theaters™</a></i>"""


    CUSTOM_FILE_CAPTION = """<code>{file_name}</code>"""


    CUSTOM_TAGS = [
    "dvdwap.com", "@360", "A2MOVIES", "Dvdworld", "HDMVCOUNTER", "KC", "KC_", "MF",
    "MLM", "MZone", "MoviezzClub", "NewRelease", "PDisk", "Tamil_LinkZz", "[@HK]", "[@MOVIES HUNT]",
    "[@TVseriesLand]", "[@WORD_MOVIS]", "[A2MOVIES]", "[AML]", "[Anylink Movies]", "[BO]", "[CC]", "[CF] ",
    "[CF]", "[CKM]", "[CKMSERIES]", "[CK]", "[CT™️]", "[CT™]", "[DFBC]", "[Dn0]",
    "[DnO]", "[EC]", "[F&T]", "[FFH]", "[GKL]", "[HK] Join @ғanѕzz", "[HN]", "[KBO]",
    "[KC]", "[KMH]", "[KML]", "[M-Zone]", "[MABLG]", "[MC_Moviecentral]", "[MC]", "[MFA]",
    "[MF]", "[MM-New]", "[MM]", "[MS]", "[Movie Bazar]", "[MoviesNowTamil]", "[PFM]", "[PM]",
    "[PS]", "[SeriesLand4U]", "[TC]", "[TIF]", "[TR]", "[TS]", "[WC]", "[YDF HD]",
    "[YDF]", "[YM]", "[ᎡᴛᏴᴛ]", "@ADrama_Lovers", "@AM", "@AVA", "@CC", "@CC_",
    "@CC_ALL", "@CC_All", "@CC_NEW", "@CC_New", "@CC_X265", "@CCM", "@CCineClub", "@CE_Links",
    "@CK_HEVC", "@CK_Moviez", "@CL", "@CMEHD", "@CR_Rockers", "@C_V", "@CVM", "@Cinema Company",
    "@Cinema_Company", "@Cinema_Kottaka", "@Cinematic_world", "@CKMovies", "@CelluloidCineClub", "@DailyMovieZhunt", "@DMovies", "@DramaOST",
    "@Dubbedmovies", "@DvdWap", "@E4E", "@E4E_Rockers", "@FBM", "@FBM_ALL", "@FBM_Dubbed", "@FBM_HW",
    "@FBM_New", "@FBM_Tamil", "@FBM_x265", "@FILIMHOUSE", "@FilmCage", "@Film_Kottaka", "@FrediesChannel", "@HEVCHubX",
    "@HEVC_Cinemaz", "@HEVC_Moviesz", "@Hk", "@I_M_D_B", "@IM", "@IndianMoviez", "@KBO", "@KD_Deck",
    "@KGRockers", "@KL_ROCKERZ", "@KR", "@KW", "@KannadaWarriors", "@KeralaBoxOffice", "@Links2U", "@Linkz_MM",
    "@M_Zone", "@MAASFILE", "@MC", "@MC_4U", "@MCArchives", "@MJ_Moviez", "@MM", "@MM_Linkz",
    "@MM_Movies", "@MM_NEW", "@MM_New", "@MM_OLD", "@MM_TvSeries", "@MOVIEHUNT", "@MOVIEZMOB", "@MalluRockers",
    "@Mallu_Movies", "@Mallu_Rockers", "@Mc_South", "@MovieWorld2000", "@Movie_Hub", "@MoviesTop10", "@MoviezzClub", "@VR",
    "@bheeshmat", "@cinema library", "@colorkannadi_movies", "@desimovies", "@desimovies Telegram", "@favio", "@film_down_load", "@iMediaShare",
    "@infotainmentmedia", "@kickass_torrents", "@koreanjournal", "@lubokvideo", "@mobile_mm", "@msp", "@malayalam movies", "@moviescollection17",
    "@moviesdeveloper", "@MoviesWar", "@myflixx", "@nanacinemas", "@OB", "@PIT", "@PM_Old", "@Qualitymovies",
    "@Rarefilms", "@RatedRMovies", "@RickyChannel", "@SY_MS", "@Sky_MoviesHD", "@TG UPDATES1", "@TN60_LinkzZ", "@TV 30NAMA1",
    "@TamilMV", "@TamilMV_Live", "@TamilRockers", "@Tamil_HD_Movies_Requests", "@Tamil_Linkz", "@Tamil_LinkzZ", "@Team_HDT", "@Theprofffesorr",
    "@TR_Moviez", "@TR_Updates", "@Tv2Us", "@TvSeriesBay", "@UCDump", "@WMR", "@WorldCinemaToday", "@X265 E4E",
    "@YTSLT", "@cinemaheist", "@trolldcompany", "@yamandanmovies", "@ᒪᕈT", "www.", "www.1TamilMV", "www.1TamilMV.fun",
    "www.1TamilMV.me", "www.1TamilMV.org", "www_1TamilMV", "www_1TamilMV_art", "www_1TamilMV_fun", "www_DVDWap_Com_", "ғαιвεяsgαтє"
    ]


    
     
    
    




