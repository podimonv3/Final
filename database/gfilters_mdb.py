import pymongo
from info import DATABASE_URI, DATABASE_NAME
from pyrogram import enums
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

from motor.motor_asyncio import AsyncIOMotorClient

# Fixed: Configured the global filter repository to use the project's core async motor connection driver
myclient = AsyncIOMotorClient(DATABASE_URI)
mydb = myclient[DATABASE_NAME]
mycol = mydb['gfilters'] 

async def init_gfilters_db():
    """സിനിമ ഗ്ലോബൽ ഫിൽറ്ററുകൾ വേഗത്തിൽ തപ്പിയെടുക്കാൻ അസിങ്ക് ഇൻഡക്സ് സെറ്റ് ചെയ്യുന്നു 🚀"""
    try:
        await mycol.create_index([("gfilters", 1), ("text", 1)], unique=True)
    except Exception as e:
        logger.error(f"Error creating gfilters database index: {e}")

async def add_gfilter(gfilters, text, reply_text, btn, file, alert):
    data = {
        'gfilters': str(gfilters),
        'text': str(text),
        'reply': str(reply_text),
        'btn': str(btn),
        'file': str(file),
        'alert': str(alert)
    }
    try:
        # 🚀 '\$set' മാറ്റി പകരം കൃത്യമായ '$set' നൽകിValueError ഫിക്സ് ചെയ്തു ✨
        await mycol.update_one({'gfilters': str(gfilters), 'text': str(text)}, {"$set": data}, upsert=True)
    except:
        logger.exception('Some error occurred!', exc_info=True)





async def find_gfilter(gfilters, name):
    try:
        file = await mycol.find_one({"gfilters": str(gfilters), "text": name})
        if file:
            return file['reply'], file['btn'], file.get('alert', None), file['file']
    except:
        pass
    return None, None, None, None

async def get_gfilters(gfilters):
    texts = []
    try:
        # Fixed: Changed from sync cursor iteration to a smooth, modern async Motor stream loop
        cursor = mycol.find({"gfilters": str(gfilters)})
        async for file in cursor:
            texts.append(file['text'])
    except Exception:
        pass
    return texts

async def delete_gfilter(gfilters, text):
    """Removes a specific global filter keyword match row from the repository."""
    # Fixed: Standardized positional parameters to cleanly align with file 14's function call execution
    myquery = {'gfilters': str(gfilters), 'text': str(text).lower().strip()}
    count = await mycol.count_documents(myquery)
    if count > 0:
        await mycol.delete_one(myquery)
        return True
    return False

async def del_allg(gfilters):
    """Clears all global filter keywords mapped within the given room block."""
    myquery = {'gfilters': str(gfilters)}
    count = await mycol.count_documents(myquery)
    if count == 0:
        return False
    try:
        await mycol.delete_many(myquery)
        return True
    except Exception:
        return False


async def count_gfilters(gfilters):
    """ഒരു പ്രത്യേക കാറ്റഗറിയിലെ/ഗ്രൂപ്പിലെ ആകെ ഗ്ലോബൽ ഫിൽറ്ററുകളുടെ എണ്ണം എടുക്കുന്നു"""
    count = mycol.count_documents({'gfilters': str(gfilters)})
    return False if count == 0 else count

async def gfilter_stats():
    """ബോട്ടിലെ ആകെ ഗ്ലോബൽ ഫിൽറ്ററുകളുടെയും അവയുടെ ടോട്ടൽ കൗണ്ടും എടുക്കുന്നു"""
    try:
        # 'gfilters' എന്ന ഒരൊറ്റ കളക്ഷനിലെ ആകെ ഡോക്യുമെന്റുകളുടെ എണ്ണം എടുക്കുന്നു ⚡
        totalcount = mycol.count_documents({})
        
        # ആകെ എത്ര വ്യത്യസ്ത തരം ഗ്ലോബൽ ഫിൽറ്റർ ഐഡികൾ (ഗ്രൂപ്പുകൾ) ഉണ്ടെന്ന് കണ്ടെത്തുന്നു
        totalcollections = len(mycol.distinct("gfilters"))
        
        return totalcollections, totalcount
    except:
        return 0, 0
