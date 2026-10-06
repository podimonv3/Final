import logging
from struct import pack
import os
import re
import base64
from pyrogram.file_id import FileId
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from marshmallow.exceptions import ValidationError
from info import DATABASE_URI, DATABASE_NAME, COLLECTION_NAME, USE_CAPTION_FILTER, TAGS

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 🚀 രണ്ട് കണക്ഷനുകൾ മാറ്റി ഒരൊറ്റ മെയിൻ ഡാറ്റാബേസ് കണക്ഷൻ മാത്രമാക്കുന്നു ✨
client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]
instance = Instance.from_db(db)



@instance.register
class Media(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)
    
    class Meta:
        indexes = ('$file_name', )
        collection_name = COLLECTION_NAME


async def clean_file_name(raw_name: str) -> str:
    """ഫയൽ നെയിം ശുദ്ധീകരിക്കാനുള്ള ഹെൽപർ ഫങ്ഷൻ"""
    name_without_ext, _ = os.path.splitext(raw_name)
    name_without_ext = re.sub(r'^\[[^\]]+\][\s._-]*', '', name_without_ext, flags=re.IGNORECASE)
    
    if TAGS and isinstance(TAGS, list):
        escaped_tags = "|".join(re.escape(tag) for tag in TAGS)
        name_without_ext = re.sub(r'^(' + escaped_tags + r')[\s._-]*', '', name_without_ext, flags=re.IGNORECASE)    
        
    name_no_apostrophe = name_without_ext.replace("'", "")
    cleaned_chars = re.sub(r'[^\u0D00-\u0D7F\u0041-\u005A\u0061-\u007A\u0030-\u0039]', ' ', name_no_apostrophe)
    final_name = re.sub(r'\s+', ' ', cleaned_chars).strip()
    return final_name


async def check_file(media):
    """Check if file is present in the database"""
    file_id, file_ref = unpack_new_file_id(media.file_id)
    existing_file = await Media.collection.find_one({"_id": file_id})
    
    if existing_file:
        return None
    else:
        return "okda"


async def save_file(media):
    """Save file in database"""
    file_id, file_ref = unpack_new_file_id(media.file_id)
    file_name = await clean_file_name(str(media.file_name))
    
    try:
        file = Media(
            file_id=file_id,
            file_ref=file_ref,
            file_name=file_name,
            file_size=media.file_size,
            file_type=media.file_type,
            mime_type=media.mime_type,
            caption=media.caption.html if media.caption else None,
         )
    except ValidationError:
        logger.exception('Error occurred while saving file in database')
        return False, 2
    else:
        try:
            await file.commit()
            return True, 1
        except DuplicateKeyError:      
            return False, 0


async def delete_files_below_threshold(threshold_size_mb=50, batch_size=20, chat_id=None, message_id=None):
    # Fixed: Uses Media.collection.find to accurately step through data items without throwing exceptions
    cursor = Media.collection.find({"file_size": {"$lt": threshold_size_mb * 1024 * 1024}}).limit(batch_size)
    deleted_count = 0
    async for document in cursor:
        try:
            await Media.collection.delete_one({"_id": document["_id"]})
            deleted_count += 1
        except Exception:
            pass
    return deleted_count




async def get_bad_files(query, file_type=None, filter=False):
    query = query.strip()
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_]')

    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except:
        return []

    filter_data = {'file_name': regex}
    if file_type:
        filter_data['file_type'] = file_type

    # Fixed: Adjusted counting parameters to query from collection directly
    total_results = await Media.collection.count_documents(filter_data)
    cursor_media = Media.collection.find(filter_data).sort('$natural', -1)
    raw_files = await cursor_media.to_list(length=total_results)
    files_media = [Media.build_from_mongo(doc) for doc in raw_files] if raw_files else []
    return files_media, total_results


async def get_search_results(query, file_type=None, max_results=12, offset=0, filter=False):
    query_no_apostrophe = query.replace("'", "")
    cleaned_query_chars = re.sub(r'[^\u0D00-\u0D7F\u0041-\u005A\u0061-\u007A\u0030-\u0039]', ' ', query_no_apostrophe)
    query = re.sub(r'\s+', ' ', cleaned_query_chars).strip()

    if not query:
        return [], '', 0

    if ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_()]')

    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except:
        return [], '', 0

    if USE_CAPTION_FILTER:
        filter_dict = {'$or': [{'file_name': regex}, {'caption': regex}]}
    else:
        filter_dict = {'file_name': regex}

    if file_type:
        filter_dict['file_type'] = file_type

    # Fixed: Routed directly through the collection driver handle to avoid umongo's missing attribute crash
    cursor_media = Media.collection.find(filter_dict).sort('file_name', 1).allow_disk_use(True)

    # Convert the returned raw dictionary documents into proper umongo object mappings for downstream processing compatibility
    raw_files = await cursor_media.to_list(length=125)
    files_media = [Media.build_from_mongo(doc) for doc in raw_files] if raw_files else []


    if files_media:
        query_lower = query.lower().strip()
        
        def sort_by_exact_match(file_obj):
            file_name_lower = file_obj.file_name.lower().strip()
            file_name_lower = re.sub(r'[\u200b\u200c\u200d\ufeff\u200e\u200f]', '', file_name_lower)
            file_name_lower = re.sub(r'[\s\u00a0\u2000-\u200a\u202f\u205f\u3000]+', ' ', file_name_lower)
            
            custom_key = []
            is_series = bool(re.search(r'\b(s\d+|e\d+)\b', file_name_lower))
            
            for text in re.split(r'(\d+)', file_name_lower):
                if text.isdigit():
                    num = int(text)
                    if len(text) == 4 and not is_series:
                        custom_key.append(-num)
                    else:
                        custom_key.append(num)
                else:
                    custom_key.append(text)

            exact_year_pattern = r'^' + re.escape(query_lower) + r'\s*(\d{4})\b'
            if re.search(exact_year_pattern, file_name_lower): return (0, custom_key)

            match_season_pattern = r'^' + re.escape(query_lower) + r'\b.*?(s\d+|e\d+)'
            if re.search(match_season_pattern, file_name_lower): return (1, custom_key)

            match_year_pattern = r'^' + re.escape(query_lower) + r'\b.*?(\d{4})'
            if re.search(match_year_pattern, file_name_lower): return (2, custom_key)
                
            if file_name_lower.startswith(query_lower): return (3, custom_key)
            return (4, custom_key)

        files_media.sort(key=sort_by_exact_match)

    seen_ids = set()
    final_sorted_files = []
    for file in files_media:
        if file.file_id not in seen_ids:
            final_sorted_files.append(file)
            seen_ids.add(file.file_id)

    total_results = len(final_sorted_files)
    if offset < 0: offset = 0

    files = final_sorted_files[offset:offset + max_results]
    next_offset = offset + len(files)

    if next_offset < total_results:
        return files, next_offset, total_results
    else:
        return files, '', total_results


async def get_file_details(query):
    cursor_media = Media.collection.find({'file_id': query})
    return await cursor_media.to_list(length=1)

def encode_file_id(s: bytes) -> str:
    r = b""
    n = 0
    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0
            r += bytes([i])
    return base64.urlsafe_b64encode(r).decode().rstrip("=")


def encode_file_ref(file_ref: bytes) -> str:
    return base64.urlsafe_b64encode(file_ref).decode().rstrip("=")


def unpack_new_file_id(new_file_id):
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(
        pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash
        )
    )
    file_ref = encode_file_ref(decoded.file_reference)
    return file_id, file_ref
