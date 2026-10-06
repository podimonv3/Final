from pyrogram import Client, filters, enums
from pyrogram.types import ChatJoinRequest, Message
from info import REQ_CHANNEL1, REQ_CHANNEL2, ADMINS
from database.users_chats_db import db

@Client.on_chat_join_request(filters.chat(REQ_CHANNEL1) | filters.chat(REQ_CHANNEL2))
async def join_reqs(b, join_req: ChatJoinRequest):
    user_id = join_req.from_user.id
    try:
        if join_req.chat.id == REQ_CHANNEL1:
            if join_req.invite_link.creator.id == b.me.id:
                await db.add_req_one(user_id)
        if join_req.chat.id == REQ_CHANNEL2:
            if join_req.invite_link.creator.id == b.me.id:
                await db.add_req_two(user_id)
    except Exception as e:
        print(f"Error adding join request: {e}")
