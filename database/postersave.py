import time
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from info import DATABASE_URI, DATABASE_NAME

logger = logging.getLogger(__name__)

# Main MongoDB Connection
client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]
poster_collection = db.poster

async def init_poster_db():
    """సినిమా పోస్టరുകൾ వేగത്തിൽ తപ്പിയെടുക്കാൻ అసిన్క్ ఇండెక్స్ సెట్ చేస్తుంది 🚀"""
    try:
        await poster_collection.create_index("movie_name", unique=True)
    except Exception as e:
        logger.error(f"Error creating poster database index: {e}")

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

async def get_db_stats():
    """ഡാറ്റാബേസിന്റെ സൈസ്, ആകെ ഫയലുകൾ എന്നിവ കണക്കാക്കുന്നു (Koyeb ലോഗ്സ് പൂർണ്ണമായി തടഞ്ഞു)"""
    try:
        total_posters = await poster_collection.count_documents({})
        
        data_size_mb = 0.0
        storage_size_mb = 0.0
        free_space_mb = 512.0 # Default free tier space
        
        try:
            stats = await db.command("dbStats")
            if stats:
                storage_size_bytes = stats.get("storageSize", 0)
                storage_size_mb = round(storage_size_bytes / (1024 * 1024), 2)
                free_space_mb = round(512.0 - storage_size_mb, 2)
                if free_space_mb < 0: 
                    free_space_mb = 0.0
        except Exception:
            pass
            
        return {
            "total": total_posters,
            "used": storage_size_mb,
            "free": free_space_mb
        }
    except Exception:
        return None

async def clear_entire_poster_db():
    """ഡാറ്റാബേസിലെ എല്ലാ പോസ്റ്റർ കാഷെയും പൂർണ്ണമായി ഡിലീറ്റ് ചെയ്യുന്നു (Koyeb ലോഗ്സ് ഉണ്ടാകില്ല)"""
    try:
        await poster_collection.delete_many({})
        return True
    except Exception:
        return False
