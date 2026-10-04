import pymongo
from pyrogram import enums
from info import DATABASE_URI, DATABASE_NAME
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

myclient = pymongo.MongoClient(DATABASE_URI)
mydb = myclient[DATABASE_NAME]
# എല്ലാ ഗ്രൂപ്പ് ഫിൽറ്ററുകളും ഇനി മുതൽ 'filters' എന്ന ഒരൊറ്റ കളക്ഷനിലേക്ക് സേവ് ചെയ്യും
mycol = mydb['filters'] 

# ഒരു ഗ്രൂപ്പിൽ ഒരേ പേരിൽ രണ്ട് ഫിൽറ്റർ വരാതിരിക്കാനും തിരച്ചിൽ റോക്കറ്റ് വേഗതയിലാക്കാനും ഇൻഡെക്സ് സെറ്റ് ചെയ്യുന്നു
mycol.create_index([("group_id", 1), ("text", 1)], unique=True)

async def add_filter(grp_id, text, reply_text, btn, file, alert):
    data = {
        'group_id': str(grp_id),
        'text': str(text),
        'reply': str(reply_text),
        'btn': str(btn),
        'file': str(file),
        'alert': str(alert)
    }
    try:
        mycol.update_one({'group_id': str(grp_id), 'text': str(text)}, {"\$set": data}, upsert=True)
    except:
        logger.exception('Some error occurred!', exc_info=True)
             
async def find_filter(group_id, name):
    try:
        file = mycol.find_one({"group_id": str(group_id), "text": name})
        if file:
            return file['reply'], file['btn'], file.get('alert', None), file['file']
    except:
        pass
    return None, None, None, None

async def get_filters(group_id):
    texts = []
    try:
        query = mycol.find({"group_id": str(group_id)})
        for file in query:
            texts.append(file['text'])
    except:
        pass
    return texts

async def delete_filter(message, text, group_id):
    myquery = {'group_id': str(group_id), 'text': text}
    query = mycol.count_documents(myquery)
    if query >= 1:
        mycol.delete_one(myquery)
        await message.reply_text(
            f"'`{text}`' deleted. I'll not respond to that filter anymore.",
            quote=True,
            parse_mode=enums.ParseMode.MARKDOWN
        )
    else:
        await message.reply_text("Couldn't find that filter!", quote=True)

async def del_all(message, group_id, title):
    myquery = {'group_id': str(group_id)}
    count = mycol.count_documents(myquery)
    if count == 0:
        await message.edit_text(f"Nothing to remove in {title}!")
        return
    try:
        mycol.delete_many(myquery)
        await message.edit_text(f"All filters from {title} has been removed")
    except:
        await message.edit_text("Couldn't remove all filters from group!")

async def count_filters(group_id):
    count = mycol.count_documents({'group_id': str(group_id)})
    return False if count == 0 else count

async def filter_stats():
    try:
        totalcount = mycol.count_documents({})
        # ആകെ എത്ര തരം ഗ്രൂപ്പുകൾ ബോട്ടിൽ ഫിൽറ്റർ സെറ്റ് ചെയ്തിട്ടുണ്ടെന്ന് കണ്ടെത്തുന്നു
        totalcollections = len(mycol.distinct("group_id"))
        return totalcollections, totalcount
    except:
        return 0, 0
