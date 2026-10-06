from pyrogram import Client, filters
from pyrogram.types import Message
from info import CHANNELS
from database.ia_filterdb import save_file, check_file
import logging

logger = logging.getLogger(__name__)

# Configured filters: explicitly matches document or video structures
media_filter = filters.document | filters.video

@Client.on_message(media_filter)
async def media_handler(bot, message: Message):
    """Dynamically parses and saves incoming media assets into the database."""
    
    # 1. Safe Channel Validation Guard
    # Avoids startup filter exceptions by validating target channel array inputs at runtime
    if not CHANNELS or message.chat.id not in CHANNELS:
        return

    # 2. Extract Target File Attributes safely
    file_type = None
    media_obj = None
    
    for current_type in ("document", "video"):
        media_obj = getattr(message, current_type, None)
        if media_obj is not None:
            file_type = current_type
            break
            
    if not media_obj:
        return

    # Bind operational helper tags safely to the model layer
    media_obj.file_type = file_type
    media_obj.caption = message.caption
    
    try:
        # Fixed: Routed lookup straight through the collection model by unique ID hash parameters
        from database.ia_filterdb import Media, unpack_new_file_id, save_file
        
        file_id, file_ref = unpack_new_file_id(media_obj.file_id)
        exists = await Media.collection.find_one({'_id': file_id})
        
        if not exists:
            await save_file(media_obj)
            logger.info(f"🎥 Auto-Indexed File: {getattr(media_obj, 'file_name', 'Unknown')}")
    except Exception as db_error:
        logger.error(f"Failed to auto-index incoming channel file element: {db_error}")
