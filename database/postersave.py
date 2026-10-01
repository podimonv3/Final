import time
from motor.motor_asyncio import AsyncIOMotorClient
from info import POSTER_DB

# MongoDB കണക്ഷൻ സെറ്റ് ചെയ്യുന്നു
client = AsyncIOMotorClient(POSTER_DB)
db = client.MoviePostersDB
poster_collection = db.cached_posters

async def get_cached_poster(movie_name):
    """ഡാറ്റാബേസിൽ നിന്ന് വളരെ വേഗത്തിൽ പോസ്റ്റർ ലിങ്ക് എടുക്കുന്നു"""
    try:
        data = await poster_collection.find_one({'movie_name': movie_name.lower()})
        if data:
            return data.get('poster_url')
    except Exception:
        pass
    return None

async def save_poster_to_cache(movie_name, poster_url):
    """പുതിയ പോസ്റ്റർ ലിങ്ക് ഭാവിയിലെ ഉപയോഗത്തിനായി ഡാറ്റാബേസിലേക്ക് സേവ് ചെയ്യുന്നു"""
    try:
        await poster_collection.update_one(
            {'movie_name': movie_name.lower()},
            {'$set': {'poster_url': poster_url, 'time': time.time()}},
            upsert=True
        )
    except Exception:
        pass
