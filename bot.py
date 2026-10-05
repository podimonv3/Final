import logging
import logging.config
import gc  
import asyncio  
import os 
import sys
from os import environ  # Fixed: Imported environ cleanly to avoid NameError crashes
from dotenv import load_dotenv
# Fixed: Imports directly from the plugins folder package root (__init__.py)
from plugins import init_web_application


from database.postersave import init_poster_db

# Run environment updates FIRST before any project parameters are initialized
load_dotenv("./dynamic.env", override=True, encoding="utf-8")

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("imdbio").setLevel(logging.CRITICAL)
logging.getLogger("imdbio.services").setLevel(logging.CRITICAL)
logging.getLogger("imdbio.parsers").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)

from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from database.ia_filterdb import Media
from database.requests_db import init_db
from database.users_chats_db import db
from info import *  # This will now safely read variables initialized by load_dotenv!
from utils import temp
from typing import Union, Optional, AsyncGenerator
from pyrogram import types
from plugins.commands import restarti
from aiohttp import web
from plugins import web_server

PORT = environ.get("PORT", "8050")

async def auto_clean_memory():
    while True:
        await asyncio.sleep(1800)  # 30 മിനിറ്റ്
        try:
            gc.collect()  # റാം ക്ലീൻ ചെയ്യുന്നു
        except Exception as e:
            logging.error(f"RAM cleaning failed: {e}")  # എറർ ഉണ്ടായാൽ മാത്രം Koyeb-ൽ കാണിക്കും


async def restart_bot(bot):
    # 🚀 Motor അസിങ്ക് ഡ്രൈവർ ആയതുകൊണ്ട് ഇവിടെ await നിർബന്ധമായും ചേർക്കുന്നു ✨
    progress_document = await restarti.find_one({"_id": "frestart"})
    if progress_document:
        last_restart = progress_document.get("restart")
        if last_restart == "on":
            await restarti.update_one(
                {"_id": "frestart"},
                {"$set": {"restart": "off"}},
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
        
        # Initialize the missing movie request index blocks
        await init_db()
        await init_poster_db()
    # Inject this line to safely stand up the movie poster cache collection index:      
        me = await self.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        self.username = '@' + me.username
        logging.info(f"{me.first_name} with for Pyrogram v{__version__} (Layer {layer}) started on {me.username}.")
        logging.info(LOG_STR)
        # 🚀 Fsub ചാനൽ 1-ന്റെ ഐഡി ഡാറ്റാബേസിൽ നിന്ന് അസിങ്ക് ആയി ലോഡ് ചെയ്യുന്നു ✨
        if REQ_CHANNEL1 is None:
            with open("./dynamic.env", "wt+") as f:
                req = await db.get_fsub_chat()             
                if req is None:
                    req = "False"
                else:
                    req = str(req['chat_id'])                   
                f.write(f"REQ_CHANNEL1={req}\n")
                
            logging.info("Loading REQ_CHANNEL 1 from database and rebooting...") 
            # Force environmental runtime parameter updates before restarting execution
            os.environ["REQ_CHANNEL1"] = req
            os.execl(sys.executable, sys.executable, "bot.py")
            return 
            
        # 🚀 Fsub ചാനൽ 2-ന്റെ ഐഡി ഡാറ്റാബേസിൽ നിന്ന് അസിങ്ക് ആയി ലോഡ് ചെയ്യുന്നു ✨
        if REQ_CHANNEL2 is None:
            with open("./dynamic.env", "wt+") as f:
                req2 = await db.get_fsub_chat2()  
                if req2 is None:
                    req2 = "False"
                else:
                    req2 = str(req2['chat_id'])
                f.write(f"REQ_CHANNEL2={req2}\n")
            logging.info("Loading REQ_CHANNEL 2 from database and rebooting...") 
            # Force environmental runtime parameter updates before restarting execution
            os.environ["REQ_CHANNEL2"] = req2
            os.execl(sys.executable, sys.executable, "bot.py")
            return 
 

        await self.send_message(chat_id=LOG_CHANNEL, text="restarted ❤️‍🩹")
        
        app = web.AppRunner(await init_web_application(), access_log=None)
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
