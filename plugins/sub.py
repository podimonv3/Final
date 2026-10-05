from pyrogram import Client, filters
from pyrogram.types import ChatJoinRequest
from info import REQ_CHANNEL1, REQ_CHANNEL2, ADMINS
from database.users_chats_db import db
from utils import temp
import logging

logger = logging.getLogger(__name__)

# Dynamically evaluates request channels safely to prevent startup filter crashes
@Client.on_chat_join_request()
async def join_reqs(b, join_req: ChatJoinRequest):
    user_id = join_req.from_user.id
    chat_id = join_req.chat.id
    
    # Ignore requests if the incoming event does not match our requirements channels
    if chat_id not in [int(REQ_CHANNEL1 or 0), int(REQ_CHANNEL2 or 0)]:
        return

    try:
        # Secure fallback validation checks utilizing our runtime global state cache
        bot_id = b.me.id if getattr(b, "me", None) else temp.ME
        
        # Safely verify if an invite link object exists before checking its creator attributes
        creator_id = join_req.invite_link.creator.id if (join_req.invite_link and join_req.invite_link.creator) else None

        if chat_id == int(REQ_CHANNEL1 or 0):
            if creator_id == bot_id:
                await db.add_req_one(user_id)
                
        elif chat_id == int(REQ_CHANNEL2 or 0):
            if creator_id == bot_id:
                await db.add_req_two(user_id)
                
    except Exception as e:
        logger.error(f"Error adding join request to tracking records: {e}")
