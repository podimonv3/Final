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
from info import DATABASE_URI, DATABASE_URI2, DATABASE_NAME, COLLECTION_NAME, USE_CAPTION_FILTER, TAGS

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# മെയിൻ യൂസർ ഡാറ്റാബേസ് കണക്ഷൻ (For commands/stats)
client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]

# സിനിമ ഫയലുകൾ സൂക്ഷിക്കുന്ന പുതിയ ഡാറ്റാബേസ് കണക്ഷൻ
client1 = AsyncIOMotorClient(DATABASE_URI2)
db1 = client1[DATABASE_NAME] # 👈 ഇതാണ് commands.py-ലേക്ക് ഇമ്പോർട്ട് ചെയ്യുന്നത്
instance = Instance.from_db(db1)

@instance.register
class Media(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)
    
    # 💡 uMongo എറർ ഒഴിവാക്കാൻ ഈ ഒരു വരി കൂടി ഏറ്റവും താഴെയായി ചേർക്കുക
    score = fields.FloatField(load_only=True, dump_only=True)
    
    class Meta:
        indexes = (
            {'key': [('file_name', 'text')]},
        )
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

# save_filea ഒഴിവാക്കിയതിനാൽ പഴയ ഇൻഡെക്സിങ് ഫയലുകളിൽ എറർ വരാതിരിക്കാൻ ബാക്കപ്പ് നൽകുന്നു
async def save_filea(media):
    return await save_file(media)


async def delete_files_below_threshold(db, threshold_size_mb: int = 50, batch_size: int = 20, chat_id: int = None, message_id: int = None):
    cursor_media = Media.find({"file_size": {"$lt": threshold_size_mb * 1024 * 1024}}).limit(batch_size)
    deleted_count = 0
    
    async for document in cursor_media:
        try:
            await Media.collection.delete_one({"_id": document["file_id"]})
            deleted_count += 1
            print(f'Deleted file from Media: {document["file_name"]}')
        except Exception as e:
            print(f'Error deleting file from Media: {document["file_name"]}, {e}')

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
        return [], [], 0

    filter_dict = {'file_name': regex}
    if file_type:
        filter_dict['file_type'] = file_type

    total_results = await Media.count_documents(filter_dict)
    cursor_media = Media.find(filter_dict).sort([('$natural', -1)])
    files_media = await cursor_media.to_list(length=total_results)

    return files_media, [], total_results





async def get_search_results(query, file_type=None, max_results=12, offset=0, filter=False):
    """Text Index ഇല്ലാത്ത പ്രശ്നം പൂർണ്ണമായി പരിഹരിച്ച സെർച്ച് ഫങ്ഷൻ"""
    query_no_apostrophe = query.replace("'", "")
    cleaned_query_chars = re.sub(r'[^\u0D00-\u0D7F\u0041-\u005A\u0061-\u007A\u0030-\u0039]', ' ', query_no_apostrophe)
    query = re.sub(r'\s+', ' ', cleaned_query_chars).strip()

    if not query:
        return [], '', 0

    # 💡 മാറ്റം വരുത്തിയത് ഇവിടെയാണ്:
    # ഡാറ്റാബേസിൽ ടെക്സ്റ്റ് ഇൻഡെക്സ് ഇല്ലെങ്കിൽ അത് നിർബന്ധമായി ഇവിടെ ക്രിയേറ്റ് ചെയ്യിക്കുന്നു
    try:
        await Media.collection.create_index([('file_name', 'text')])
    except Exception as e:
        logger.info(f"Index check/creation: {e}")

    # മോംഗോഡിബി ടെക്സ്റ്റ് സെർച്ചിനായുള്ള ഫിൽട്ടർ
    filter_dict = {"$text": {"$search": query}}

    if file_type:
        filter_dict['file_type'] = file_type

    try:
        # സ്കോർ അടിസ്ഥാനമാക്കി സോർട്ട് ചെയ്ത് 200 എണ്ണം മാത്രം എടുക്കുന്നു
        cursor_media = Media.find(filter_dict, projection={'score': {'$meta': 'textScore'}}).sort([('score', {'$meta': 'textScore'})])
        final_sorted_files = await cursor_media.to_list(length=200)
    except Exception as e:
        logger.error(f"Search Error: {e}")
        return [], '', 0

    # ഫയലുകൾ എടുത്ത ശേഷമുള്ള പൈത്തൺ കസ്റ്റം സോർട്ടിങ്
    if final_sorted_files:
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
            if re.search(exact_year_pattern, file_name_lower):
                return (0, custom_key)

            match_season_pattern = r'^' + re.escape(query_lower) + r'\b.*?(s\d+|e\d+)'
            if re.search(match_season_pattern, file_name_lower):
                return (1, custom_key)

            match_year_pattern = r'^' + re.escape(query_lower) + r'\b.*?(\d{4})'
            if re.search(match_year_pattern, file_name_lower):
                return (2, custom_key)
                
            if file_name_lower.startswith(query_lower):
                return (3, custom_key)
                
            return (4, custom_key)

        final_sorted_files.sort(key=sort_by_exact_match)

    total_results = len(final_sorted_files)

    if offset < 0:
        offset = 0

    files = final_sorted_files[offset:offset + max_results]
    next_offset = offset + len(files)

    if next_offset < total_results:
        return files, next_offset, total_results
    else:
        return files, '', total_results



       
async def get_file_details(query):
    filter = {'file_id': query}
    cursor_media = Media.find(filter)
    filedetails_media = await cursor_media.to_list(length=1)
    return filedetails_media


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
