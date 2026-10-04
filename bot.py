import logging
import logging.config
import gc  # മെമ്മറി ക്ലീൻ ചെയ്യാനായി ചേർത്തത്
import asyncio  # ഓട്ടോമാറ്റിക് ടാസ്ക് റൺ ചെയ്യാനായി ചേർത്തത്

# Get logging configurations
logging.config.fileConfig('logging.conf')

logging.getLogger("pyrogram").setLevel(logging.ERROR)
# asyncio വാർണിങ്ങുകൾ പൂർണ്ണമായി ഒഴിവാക്കാൻ താഴെ പറയുന്ന വരി ചേർക്കുക
logging.getLogger("asyncio").setLevel(logging.ERROR)

# imdbio ലോഗുകൾ പൂർണ്ണമായി ഒഴിവാക്കാൻ CRITICAL ലെവൽ നൽകുക
logging.getLogger("imdbio").setLevel(logging.CRITICAL)
logging.getLogger("imdbio.services").setLevel(logging.CRITICAL)
logging.getLogger("imdbio.parsers").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)



from pyrogram import Client, __version__
from pyrogram.raw.all import layer
# Mediaa ഒഴിവാക്കി മെയിൻ കളക്ഷൻ മാത്രം നിലനിർത്തുന്നു
from database.ia_filterdb import Media

# 🚀 മൂവി റിക്വസ്റ്റ് ഡാറ്റാബേസ് ഇൻഡെക്സിങ് ഫങ്ഷൻ ഇമ്പോർട്ട് ചെയ്യുന്നു ✨
from database.requests_db import init_db

from database.users_chats_db import db
from info import *
from utils import temp
from typing import Union, Optional, AsyncGenerator
from pyrogram import types
from plugins.commands import restarti
import os 
import sys
from dotenv import load_dotenv
from aiohttp import web
from plugins import web_server
PORT = environ.get("PORT", "8050")

load_dotenv("./dynamic.env", override=True, encoding="utf-8")

async def auto_clean_memory():
    while True:
        await asyncio.sleep(900)  # 15 മിനിറ്റ്
        try:
            gc.collect()  # റാം ക്ലീൻ ചെയ്യുന്നു
        except Exception as e:
            logging.error(f"RAM cleaning failed: {e}")  # എറർ ഉണ്ടായാൽ മാത്രം Koyeb-ൽ കാണിക്കും


async def restart_bot(bot):
    progress_document = restarti.find_one({"_id": "frestart"})
    if progress_document:
        last_restart = progress_document.get("restart")
        if last_restart == "on":
            restarti.update_one(
                {"_id": "frestart"},
                {"\$set": {"restart": "off"}},
                upsert=True
            )
            os.execl(sys.executable, sys.executable, "bot.py")
        else:
            return 
class Bot(Client):

    def __init__(self):
        super().__init__(
            name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=200,
            plugins={"root": "plugins"},
            sleep_threshold=5,
        )

    async def start(self):
        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats
        await super().start()        
        # ഒരൊറ്റ ഡാറ്റാബേസ് ഇൻഡെക്സ് മാത്രം വെരിഫൈ ചെയ്യുന്നു
        await Media.ensure_indexes()        
        
        # 🚀 24 മണിക്കൂർ ഡിലീറ്റ് ഒഴിവാക്കിയുള്ള പുതിയ റിക്വസ്റ്റ് ഇൻഡെക്സ് ഇവിടെ റൺ ചെയ്യുന്നു ✨
        await init_db()
        
        me = await self.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        self.username = '@' + me.username
        logging.info(f"{me.first_name} with for Pyrogram v{__version__} (Layer {layer}) started on {me.username}.")
        logging.info(LOG_STR)
        if REQ_CHANNEL1 == None:
            with open("./dynamic.env", "wt+") as f:
                req = await db.get_fsub_chat()                
                if req is None:
                    req = False
                else:
                    req = req['chat_id']                   
                f.write(f"REQ_CHANNEL1={req}\n")
                
            logging.info("Loading REQ_CHANNEL from database...") 
            os.execl(sys.executable, sys.executable, "bot.py")
            return 
        if REQ_CHANNEL2 == None:
            with open("./dynamic.env", "wt+") as f:
                req2 = await db.get_fsub_chat2()
                if req2 is None:
                    req2 = False
                else:
                    req2 = req2['chat_id']
                f.write(f"REQ_CHANNEL2={req2}\n")
            logging.info("Loading REQ_CHANNEL...") 
            os.execl(sys.executable, sys.executable, "bot.py")
            return 
        await self.send_message(chat_id=LOG_CHANNEL, text="restarted ❤️‍🩹")
        
        app = web.AppRunner(await web_server(), access_log=None)
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()       

        if REQ_CHANNEL1 != False:           
            try:
                _link = await self.create_chat_invite_link(chat_id=int(REQ_CHANNEL1), creates_join_request=True)
                self.req_link1 = _link.invite_link
            except Exception as e:
                logging.info(f"Make Sure REQ_CHANNEL 1 ID is correct or {e}")
        if REQ_CHANNEL2 != False:
            try:
                _link = await self.create_chat_invite_link(chat_id=int(REQ_CHANNEL2), creates_join_request=True)
                self.req_link2 = _link.invite_link
            except Exception as e:
                logging.info(f"Make Sure REQ_CHANNEL 2 ID is correct or {e}")

        # ബോട്ട് റൺ ആകുമ്പോൾ ബാക്ക്ഗ്രൗണ്ടിൽ മെമ്മറി ക്ലീനിങ് ടാസ്ക് സ്റ്റാർട്ട് ചെയ്യും
        asyncio.create_task(auto_clean_memory())
        await restart_bot(self)
        
    async def stop(self, *args):
        await super().stop()
        logging.info("Bot stopped. Bye.")
    
    async def iter_messages(
        self,
        chat_id: Union[int, str],
        limit: int,
        offset: int = 0,
    ) -> Optional[AsyncGenerator["types.Message", None]]:
        current = offset
        while True:
            new_diff = min(200, limit - current)
            if new_diff <= 0:
                return
            messages = await self.get_messages(chat_id, list(range(current, current+new_diff+1)))
            for message in messages:
                yield message
                current += 1


app = Bot()
app.run()
