import pymongo
from info import DATABASE_URI, DATABASE_NAME
from pyrogram import enums
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

myclient = pymongo.MongoClient(DATABASE_URI)
mydb = myclient[DATABASE_NAME]
# ഗ്ലോബൽ ഫിൽറ്ററുകൾക്കായുള്ള ഒറ്റ കളക്ഷൻ ഫോൾഡർ
mycol = mydb['gfilters'] 

# ഒരേ വാക്ക് വീണ്ടും വരാതിരിക്കാനും ഡാറ്റ വേഗത്തിൽ തിരയാനും ഇൻഡെക്സ് സെറ്റ് ചെയ്യുന്നു
mycol.create_index([("gfilters", 1), ("text", 1)], unique=True)

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
        mycol.update_one({'gfilters': str(gfilters), 'text': str(text)}, {"$set": data}, upsert=True)
    except:
        logger.exception('Some error occurred!', exc_info=True)





async def find_gfilter(gfilters, name):
    try:
        file = mycol.find_one({"gfilters": str(gfilters), "text": name})
        if file:
            return file['reply'], file['btn'], file.get('alert', None), file['file']
    except:
        pass
    return None, None, None, None

async def get_gfilters(gfilters):
    texts = []
    try:
        query = mycol.find({"gfilters": str(gfilters)})
        for file in query:
            texts.append(file['text'])
    except:
        pass
    return texts

async def delete_gfilter(message, text, gfilters):
    myquery = {'gfilters': str(gfilters), 'text': text}
    count = mycol.count_documents(myquery)
    if count > 0:
        mycol.delete_many(myquery)
        await message.reply_text(
            f"'`{text}`' deleted. I'll not respond to that gfilter anymore.",
            quote=True,
            parse_mode=enums.ParseMode.MARKDOWN
        )
    else:
        await message.reply_text("Couldn't find that gfilter!", quote=True)

async def del_allg(message, gfilters):
    myquery = {'gfilters': str(gfilters)}
    count = mycol.count_documents(myquery)
    if count == 0:
        await message.edit_text("Nothing to remove !")
        return
    try:
        mycol.delete_many(myquery)
        await message.edit_text("All gfilters have been removed !")
    except:
        await message.edit_text("Couldn't remove all gfilters !")

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
