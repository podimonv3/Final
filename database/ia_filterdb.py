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


async def check_file(media):
    """Check if file is present in the database"""
    file_id, file_ref = unpack_new_file_id(media.file_id)
    existing_file = await Media.collection.find_one({"_id": file_id})
    
    if existing_file:
        return None
    else:
        return "okda"


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


async def get_search_results(query, file_type=None, max_results=10, offset=0, filter=False, total_results=None):
    query = query.replace("'", "")
    query = re.sub(r'[^\u0D00-\u0D7F\u0041-\u005A\u0061-\u007A\u0030-\u0039]', ' ', query)
    query = re.sub(r'\s+', ' ', query).strip()
    if not query:
        return [], '', 0

    if ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + re.escape(query) + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = re.escape(query).replace(r'\ ', r'.*[\s\.\+\-_()]')

    try:
        regex = re.compile(raw_pattern, re.IGNORECASE)
    except Exception:
        return [], '', 0

    filter_dict = {'$or': [{'file_name': regex}, {'caption': regex}]} if USE_CAPTION_FILTER else {'file_name': regex}
    if file_type:
        filter_dict['file_type'] = file_type

    if total_results is None:
        total_results = await Media.collection.count_documents(filter_dict)

    exact_regex = re.compile(r'^' + re.escape(query) + r'$', re.IGNORECASE)
    exact_filter = {'file_name': exact_regex}
    if file_type:
        exact_filter['file_type'] = file_type

    exact_cursor = Media.collection.find(exact_filter).limit(max_results)
    exact_raw = await exact_cursor.to_list(length=max_results)
    exact_files = [Media.build_from_mongo(doc) for doc in exact_raw] if exact_raw else []
    exact_ids = [doc['_id'] for doc in exact_raw]

    remaining = max_results - len(exact_files)
    normal_files = []

    if remaining > 0:
        normal_filter = dict(filter_dict)
        if exact_ids:
            if '$or' in normal_filter:
                normal_filter = {'$and': [normal_filter, {'_id': {'$nin': exact_ids}}]}
            else:
                normal_filter['_id'] = {'$nin': exact_ids}

        normal_offset = max(0, offset - len(exact_files))
        cursor = Media.collection.find(normal_filter).sort('file_name', 1).skip(normal_offset).limit(remaining)
        raw_files = await cursor.to_list(length=remaining)
        normal_files = [Media.build_from_mongo(doc) for doc in raw_files] if raw_files else []

    if offset == 0:
        files = exact_files + normal_files
    else:
        files = normal_files

    next_offset = offset + len(files)
    if next_offset >= total_results:
        next_offset = ''

    return files, next_offset, total_results


async def get_file_details(query):
    try:
        raw_files = await Media.collection.find({"_id": query}).limit(1).to_list(length=1)
        return [Media.build_from_mongo(doc) for doc in raw_files] if raw_files else []
    except Exception:
        return []


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
