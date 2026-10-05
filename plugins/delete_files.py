import re
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from info import DELETE_CHANNELS
from database.ia_filterdb import Media, unpack_new_file_id

logger = logging.getLogger(__name__)

# Configured filters: matches document, video, or audio files cleanly
media_filter = filters.document | filters.video | filters.audio

@Client.on_message(media_filter)
async def deletemultiplemedia(bot, message: Message):
    """Dynamic delete handler ensuring stability and accurate tracking."""
    
    # 1. Safe Channel Validation Guard
    # Evaluates variables at runtime to avoid startup filter execution exceptions
    if not DELETE_CHANNELS or message.chat.id not in DELETE_CHANNELS:
        return

    # Extract target media attribute structure securely
    for file_type in ("document", "video", "audio"):
        media = getattr(message, file_type, None)
        if media is not None:
            break
    else:
        return

    try:
        # Unpack the Pyrogram file identifier details
        file_id, file_ref = unpack_new_file_id(media.file_id)

        # 2. Direct Delete Execution via Unique ID hash parameters
        result = await Media.collection.delete_one({'_id': file_id})
        
        if result.deleted_count:
            logger.info(f"File [{media.file_name}] successfully deleted from database using direct ID.")
            return

        # 3. Corrected Fallback Match Mechanism
        # Instead of searching with a modified name query, we apply a safe regex search check
        cleaned_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
        regex_query = ".*".join(map(re.escape, cleaned_name.split()))
        
        result = await Media.collection.delete_many({
            'file_name': {'$regex': regex_query, '$options': 'i'},
            'file_size': media.file_size,
            'mime_type': media.mime_type
        })
        
        if result.deleted_count:
            logger.info(f"File [{media.file_name}] successfully deleted using regex backup match.")
            return

        # 4. Strict Exact Match Fallback Block
        result = await Media.collection.delete_many({
            'file_name': media.file_name,
            'file_size': media.file_size,
            'mime_type': media.mime_type
        })
        if result.deleted_count:
            logger.info(f"File [{media.file_name}] successfully deleted using exact string values.")
        else:
            logger.info(f"File [{media.file_name}] execution processed, but element not found in records.")
            
    except Exception as error:
        logger.error(f"Error handling multi-media database removal event: {error}")
