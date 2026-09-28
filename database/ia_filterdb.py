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
from info import DATABASE_URI, DATABASE_URI2, DATABASE_URI3, DATABASE_NAME, COLLECTION_NAME, USE_CAPTION_FILTER, TAGS

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]
instance = Instance.from_db(db)

client1 = AsyncIOMotorClient(DATABASE_URI2)
db1 = client1[DATABASE_NAME]
instance1 = Instance.from_db(db1)

client2 = AsyncIOMotorClient(DATABASE_URI3)
db2 = client2[DATABASE_NAME]
instance2 = Instance.from_db(db2)

@instance1.register
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

@instance2.register
class Mediaa(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)
    
    class Metaa:
        indexes = ('$file_name', )
        collection_name = COLLECTION_NAME

async def check_file(media):
    """Check if file is present in the database"""

    # TODO: Find better way to get same file_id for same media to avoid duplicates
    file_id, file_ref = unpack_new_file_id(media.file_id)
    
    existing_file = await Media.collection.find_one({"_id": file_id})
    existing_filea = await Mediaa.collection.find_one({"_id": file_id})
    
    if existing_file:
        pass
    elif existing_filea:
        pass
    else:
        okda = "okda"
        return okda
        


async def clean_file_name(raw_name: str) -> str:
    """ഫയൽ നെയിം ശുദ്ധീകരിക്കാനുള്ള ഹെൽപർ ഫങ്ഷൻ"""
    # 1. ഫയൽ എക്സ്റ്റൻഷൻ നീക്കം ചെയ്യുന്നു (.mp4, .mkv മുതലായവ)
    name_without_ext, _ = os.path.splitext(raw_name)
    
    # --- പുതിയ മാറ്റം: info.py-ലെ TAGS ലിസ്റ്റിലുള്ളവ തുടക്കത്തിൽ വന്നാൽ മാത്രം ഒഴിവാക്കുന്നു ---
    if TAGS and isinstance(TAGS, list):
        # ലിസ്റ്റിലെ ടാഗുകൾ പൈത്തൺ റീജക്സിന് മനസ്സിലാകുന്ന രീതിയിലേക്ക് മാറ്റുന്നു
        escaped_tags = "|".join(re.escape(tag) for tag in TAGS)
        
        # ഫയലിന്റെ തുടക്കത്തിൽ (^) ഈ ടാഗുകൾ വന്നാൽ അത് നീക്കം ചെയ്യുന്നു
        name_without_ext = re.sub(r'^(' + escaped_tags + r')[\s._-]*', '', name_without_ext, flags=re.IGNORECASE)    
        
    # 2. അപ്പോസ്ട്രോഫികൾ (') പൂർണ്ണമായി ഒഴിവാക്കുന്നു (i'm -> im)
    name_no_apostrophe = name_without_ext.replace("'", "")
    
    # 3 & 4. മലയാളം, ഇംഗ്ലീഷ് (A-Z, a-z), അക്കങ്ങൾ (0-9) എന്നിവ മാത്രം നിലനിർത്തുന്നു.
    # മറ്റെല്ലാ പ്രത്യേക ചിഹ്നങ്ങൾക്ക് പകരവും സ്പേസ് നൽകുന്നു.
    # [^\u0D00-\u0D7F\u0041-\u005A\u0061-\u007A\u0030-\u0039] എന്നത് മലയാളം, ഇംഗ്ലീഷ്, അക്കങ്ങൾ അല്ലാത്തവയെ സൂചിപ്പിക്കുന്നു.
    cleaned_chars = re.sub(r'[^\u0D00-\u0D7F\u0041-\u005A\u0061-\u007A\u0030-\u0039]', ' ', name_no_apostrophe)
    
    # 5. അനാവശ്യമായ ഒന്നിലധികം സ്പേസുകൾ ഒഴിവാക്കി ഒരൊറ്റ സ്പേസ് ആക്കുന്നു, ഇരുവശത്തെയും സ്പേസ് കളയുന്നു.
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


async def save_filea(media):
    """Save file in database"""
    file_id, file_ref = unpack_new_file_id(media.file_id)
    file_name = await clean_file_name(str(media.file_name))
    
    try:
        file = Mediaa(
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

            

async def delete_files_below_threshold(db, threshold_size_mb: int = 50, batch_size: int = 20, chat_id: int = None, message_id: int = None):
    cursor_media = Media.find({"file_size": {"$lt": threshold_size_mb * 1024 * 1024}}).limit(batch_size // 2)
    cursor_mediaa = Mediaa.find({"file_size": {"$lt": threshold_size_mb * 1024 * 1024}}).limit(batch_size // 2)
    deleted_count_media = 0
    deleted_count_mediaa = 0
    
    async for document in cursor_media:
        try:
            await Media.collection.delete_one({"_id": document["file_id"]})
            deleted_count_media += 1
            print(f'Deleted file from Media: {document["file_name"]}')
        except Exception as e:
            print(f'Error deleting file from Media: {document["file_name"]}, {e}')

    async for document in cursor_mediaa:
        try:
            await Mediaa.collection.delete_one({"_id": document["file_id"]})
            deleted_count_mediaa += 1
            print(f'Deleted file from Mediaa: {document["file_name"]}')
        except Exception as e:
            print(f'Error deleting file from Mediaa: {document["file_name"]}, {e}')
            
    deleted_count = deleted_count_media + deleted_count_mediaa
    return deleted_count

async def get_bad_files(query, file_type=None, filter=False):
    """For given query return (results, next_offset)"""
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

    if USE_CAPTION_FILTER:
        filter = {'file_name': regex}
    else:
        filter = {'file_name': regex}

    if file_type:
        filter['file_type'] = file_type

    total_results_media1 = await Media.count_documents(filter)
    total_results_media2 = await Mediaa.count_documents(filter)
    total_results = total_results_media1 + total_results_media2

    cursor_media1 = Media.find(filter)
    cursor_media1.sort('$natural', -1)
    files_media1 = await cursor_media1.to_list(length=total_results_media1)

    cursor_media2 = Mediaa.find(filter)
    cursor_media2.sort('$natural', -1)
    files_media2 = await cursor_media2.to_list(length=total_results_media2)

    return files_media1, files_media2, total_results


async def get_search_results(query, file_type=None, max_results=8, offset=0, filter=False):
    """Koyeb ഫ്രീ സെർവറിനായി ഡാറ്റാബേസ് ലെവലിൽ ഒപ്റ്റിമൈസ് ചെയ്ത സ്മാർട്ട് സെർച്ച് (Fixed)"""

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

    # --- തിരുത്തിയ ഭാഗം: എറർ ഒഴിവാക്കാൻ $natural മാറ്റി file_name മാത്രം ഉപയോഗിച്ച് സോർട്ട് ചെയ്യുന്നു ---
    cursor_media = Media.find(filter_dict).sort([('file_name', 1)])
    cursor_mediaa = Mediaa.find(filter_dict).sort([('file_name', 1)])

    # Koyeb സെർവർ റാം ക്രാഷ് ആകാതിരിക്കാൻ ലിമിറ്റ് 120 ആയി നിലനിർത്തുന്നു
    files_media = await cursor_media.to_list(length=200)
    files_mediaa = await cursor_mediaa.to_list(length=200)

    interleaved_files = []
    index_media1 = index_media2 = 0
    while index_media1 < len(files_media) or index_media2 < len(files_mediaa):
        if index_media1 < len(files_media):
            interleaved_files.append(files_media[index_media1])
            index_media1 += 1
        if index_media2 < len(files_mediaa):
            interleaved_files.append(files_mediaa[index_media2])
            index_media2 += 1

    if interleaved_files:
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

        interleaved_files.sort(key=sort_by_exact_match)

    seen_ids = set()
    final_sorted_files = []
    for file in interleaved_files:
        if file.file_id not in seen_ids:
            final_sorted_files.append(file)
            seen_ids.add(file.file_id)

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
    if filedetails_media:
        return filedetails_media
    # Query details from Mediaa collection
    cursor_mediaa = Mediaa.find(filter)
    filedetails_mediaa = await cursor_mediaa.to_list(length=1)
    if filedetails_mediaa:
        return filedetails_mediaa

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
    """Return file_id, file_ref"""
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
