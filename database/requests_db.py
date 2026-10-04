from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from info import DATABASE_URI, DATABASE_NAME

client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]
collection = db["moviereq"]

async def init_db():
    """സിനിമയുടെ പേര് ഡ്യൂപ്ലിക്കേറ്റ് വരാതിരിക്കാനുള്ള ഇൻഡക്സ് മാത്രം സെറ്റ് ചെയ്യുന്നു (24hr ഡിലീറ്റ് ഒഴിവാക്കി)"""
    await collection.create_index("movie_name", unique=True)

async def save_missing_movie(movie_name):
    """സിനിമ പുതിയതാണെങ്കിൽ സേവ് ചെയ്യും, ഉള്ളതാണെങ്കിൽ കൗണ്ട് 1 വർദ്ധിപ്പിക്കും"""
    movie_clean = movie_name.strip().lower()
    
    await collection.update_one(
        {"movie_name": movie_clean},
        {
            "$inc": {"search_count": 1},
            "$set": {"lastSearchedAt": datetime.utcnow()}
        },
        upsert=True
    )
    return True

async def get_all_missing_movies():
    """ഡാറ്റാബേസിലുള്ള എല്ലാ സിനിമകളും alphabetical order-ൽ എടുക്കുന്നു"""
    cursor = collection.find({}).sort("movie_name", 1)
    results = await cursor.to_list(length=None)
    
    return [{"name": doc["movie_name"].title(), "count": doc.get("search_count", 1)} for doc in results]

async def clear_all_missing_movies():
    """ഡാറ്റാബേസിലെ മുഴുവൻ റിക്വസ്റ്റുകളും ഒന്നിച്ച് ഡിലീറ്റ് ചെയ്യാനുള്ള പുതിയ ഫങ്ഷൻ ✨"""
    try:
        await collection.delete_many({})
        return True
    except Exception:
        return False
