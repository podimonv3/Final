import logging
from motor.motor_asyncio import AsyncIOMotorClient
from info import DATABASE_URI, DATABASE_NAME

logger = logging.getLogger(__name__)

# ബോട്ടിലെ മറ്റ് ഫയലുകളിലെ പോലെ ഒരൊറ്റ മെയിൻ അസിങ്ക് കണക്ഷൻ മാത്രം ഉപയോഗിക്കുന്നു
client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]
settings_collection = db['locks']


async def get_group_locks(chat_id: int):
    """ഗ്രൂപ്പിലെ നിലവിലെ എല്ലാ ലോക്ക് സെറ്റിങ്സും എടുക്കുന്നു"""
    config = await settings_collection.find_one({'_id': f'locks_{int(chat_id)}'})
    if config:
        return config.get('locks', {})
    
    # ഡിഫോൾട്ട് ആയി ആദ്യ തവണ എല്ലാ മീഡിയകളും അനുവദിച്ചിരിക്കുന്നു (Allow = False)
    return {
        "photos": False, "videos": False, "stickers": False, "voice": False, 
        "audio": False, "document": False, "animation": False, "poll": False,
        "video_note": False, "contact": False, "location": False, "inline": False,
        "story": False, "game": False, "channel": False,
        "new_members": False, "left_members": False, "title_changed": False,
        "photo_changed": False, "pinned": False, "video_chat": False,
        "fwd_channel": False, "usernames": False, "hashtags": False, 
        "commands": False, "emails": False, "links": False, 
        "text_styles": False, "edited": False
    }


async def set_group_lock(chat_id: int, media_type: str, status: bool):
    """ഒരു പ്രത്യേക മീഡിയ ലോക്ക്/അൺലോക്ക് ചെയ്യാൻ"""
    current_locks = await get_group_locks(chat_id)
    current_locks[media_type] = status
    await settings_collection.update_one(
        {'_id': f'locks_{int(chat_id)}'}, 
        {'$set': {'locks': current_locks}}, 
        upsert=True
    )
