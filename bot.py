import logging
import logging.config

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
# asyncio വാർണിങ്ങുകൾ പൂർണ്ണമായി ഒഴിവാക്കാൻ താഴെ പറയുന്ന വരി ചേർക്കുക
logging.getLogger("asyncio").setLevel(logging.ERROR)


# imdbio ലോഗുകൾ മാത്രം ഒഴിവാക്കാൻ
logging.getLogger("imdbio.services").setLevel(logging.WARNING)
logging.getLogger("imdbio.parsers").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from database.ia_filterdb import Media
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

async def restart_bot(bot):
    progress_document = restarti.find_one({"_id": "frestart"})
    if progress_document:
        last_restart = progress_document.get("restart")
        if last_restart == "on":
            restarti.update_one(
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
        await Media.ensure_indexes()
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
        """Iterate through a chat sequentially.
        This convenience method does the same as repeatedly calling :meth:`~pyrogram.Client.get_messages` in a loop, thus saving
        you from the hassle of setting up boilerplate code. It is useful for getting the whole chat messages with a
        single call.
        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).
                
            limit (``int``):
                Identifier of the last message to be returned.
                
            offset (``int``, *optional*):
                Identifier of the first message to be returned.
                Defaults to 0.
        Returns:
            ``Generator``: A generator yielding :obj:`~pyrogram.types.Message` objects.
        Example:
            .. code-block:: python
                for message in app.iter_messages("pyrogram", 1, 15000):
                    print(message.text)
        """
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
