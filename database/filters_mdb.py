import logging
from motor.motor_asyncio import AsyncIOMotorClient
from info import DATABASE_URI, DATABASE_NAME

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# Fixed: Swapped out broken synchronous pymongo configurations for the clean core async driver
myclient = AsyncIOMotorClient(DATABASE_URI)
mydb = myclient[DATABASE_NAME]
mycol = mydb['filters'] 

async def init_filters_db():
    """ഗ്രൂപ്പ് ഫിൽറ്ററുകൾ വേഗത്തിൽ തപ്പിയെടുക്കാൻ അസിങ്ക് ഇൻഡക്സ് സെറ്റ് ചെയ്യുന്നു 🚀"""
    try:
        await mycol.create_index([("group_id", 1), ("text", 1)], unique=True)
    except Exception as e:
        logger.error(f"Error creating filters database index: {e}")

async def add_filter(grp_id, text, reply_text, btn, file, alert):
    """Safely updates or adds a unique text filter entry asynchronously."""
    data = {
        'group_id': str(grp_id),
        'text': str(text).lower().strip(),
        'reply': str(reply_text),
        'btn': str(btn),
        'file': str(file),
        'alert': str(alert)
    }
    try:
        # Fixed: Corrected "\$set" to standard MongoDB operator "$set" to prevent crashes
        await mycol.update_one(
            {'group_id': str(grp_id), 'text': str(text).lower().strip()}, 
            {"$set": data}, 
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f'Error occurred while adding filter to database: {e}')
        return False
             
async def find_filter(group_id, name):
    """Retrieves exact match configuration parameters for a specific group filter trigger."""
    try:
        file = await mycol.find_one({"group_id": str(group_id), "text": str(name).lower().strip()})
        if file:
            return file.get('reply'), file.get('btn'), file.get('alert', None), file.get('file')
    except Exception as e:
        logger.error(f"Error finding filter: {e}")
    return None, None, None, None

async def get_filters(group_id):
    """Fetches all custom filter text keywords saved within a specific chat group room."""
    texts = []
    try:
        # Fixed: Converted synchronous loops into full non-blocking asynchronous stream loops
        cursor = mycol.find({"group_id": str(group_id)})
        async for file in cursor:
            texts.append(file['text'])
    except Exception as e:
        logger.error(f"Error fetching filters list: {e}")
    return texts

async def delete_filter(group_id, text):
    """Removes a specific custom filter match rule row from the group collection block."""
    # Fixed: Moved UI messaging code out of the database driver to align cleanly with caller scripts
    myquery = {'group_id': str(group_id), 'text': str(text).lower().strip()}
    count = await mycol.count_documents(myquery)
    if count >= 1:
        await mycol.delete_one(myquery)
        return True
    return False

async def del_all(group_id):
    """Wipes all custom filter trigger keywords saved within a single chat room profile."""
    myquery = {'group_id': str(group_id)}
    count = await mycol.count_documents(myquery)
    if count == 0:
        return False
    try:
        await mycol.delete_many(myquery)
        return True
    except Exception as e:
        logger.error(f"Error clearing group filters: {e}")
        return False

async def count_filters(group_id):
    """Returns the total number of filters active inside a specific chat group."""
    count = await mycol.count_documents({'group_id': str(group_id)})
    return False if count == 0 else count

async def filter_stats():
    """Compiles statistics reflecting overall group-level filtering allocations bot-wide."""
    try:
        totalcount = await mycol.count_documents({})
        totalcollections = len(await mycol.distinct("group_id"))
        return totalcollections, totalcount
    except Exception as e:
        logger.error(f"Error building filter stats: {e}")
        return 0, 0
