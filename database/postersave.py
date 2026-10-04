import time
from motor.motor_asyncio import AsyncIOMotorClient
from info import POSTER_DB

# MongoDB കണക്ഷൻ സെറ്റ് ചെയ്യുന്നു
client = AsyncIOMotorClient(POSTER_DB)
db = client.MoviePostersDB
# ഡാറ്റകൾ ഇനി മുതൽ 'poster' എന്ന ഒരൊറ്റ കളക്ഷൻ ഫോൾഡറിലേക്ക് സേവ് ചെയ്യും
poster_collection = db.poster

# പോസ്റ്റർ വേഗത്തിൽ തപ്പിയെടുക്കാൻ ഇൻഡെക്സ് സെറ്റ് ചെയ്യുന്നു
poster_collection.create_index("movie_name", unique=True)

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
        # ആകെ സേവ് ചെയ്തിട്ടുള്ള പോസ്റ്ററുകളുടെ എണ്ണം എടുക്കുന്നു
        total_posters = await poster_collection.count_documents({})
        
        data_size_mb = 0.0
        storage_size_mb = 0.0
        free_space_mb = 512.0 # Default free tier space
        
        try:
            # ഡാറ്റാബേസ് സ്റ്റാറ്റ്സ് കമാൻഡ് റൺ ചെയ്യുന്നു
            stats = await db.command("dbStats")
            if stats:
                storage_size_bytes = stats.get("storageSize", 0)
                storage_size_mb = round(storage_size_bytes / (1024 * 1024), 2)
                free_space_mb = round(512.0 - storage_size_mb, 2)
                if free_space_mb < 0: 
                    free_space_mb = 0.0
        except Exception:
            # ചില മംഗോഡിബി ക്ലസ്റ്ററുകളിൽ dbStats കമാൻഡ് അഡ്മിൻ പെർമിഷൻ കാരണം ബ്ലോക്ക് ആയാൽ
            # Koyeb ലോഗ്സ് വരാതിരിക്കാൻ എറർ പ്രിന്റ് ചെയ്യാതെ തനിയെ സ്കിപ്പ് (Skip) ചെയ്യുന്നു.
            pass
            
        return {
            "total": total_posters,
            "used": storage_size_mb,
            "free": free_space_mb
        }
    except Exception:
        # ആകെ എണ്ണം എടുക്കുന്നതിൽ പോലും വല്ല എററും വന്നാൽ പൂർണ്ണമായി സ്കിപ്പ് ചെയ്ത് None നൽകും
        return None


async def clear_entire_poster_db():
    """ഡാറ്റാബേസിലെ എല്ലാ പോസ്റ്റർ കാഷെയും പൂർണ്ണമായി ഡിലീറ്റ് ചെയ്യുന്നു (Koyeb ലോഗ്സ് ഉണ്ടാകില്ല)"""
    try:
        # കളക്ഷനിലുള്ള എല്ലാ ഡോക്യുമെന്റുകളും ഡിലീറ്റ് ചെയ്യുന്നു
        await poster_collection.delete_many({})
        return True
    except Exception:
        # ഡാറ്റാബേസ് എറർ വന്നാൽ ലോഗ് ചെയ്യാതെ സൈലന്റ് ആയി സ്കിപ്പ് ചെയ്യും
        return False
