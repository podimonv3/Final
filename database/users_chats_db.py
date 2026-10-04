import logging
# 🚀 motor പൂർണ്ണമായും അതുപോലെ AsyncIOMotorClient-ഉം ഒന്നിച്ച് ഇമ്പോർട്ട് ചെയ്യുന്നു ✨
import motor
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
# info ഫയലിൽ നമ്മൾ നൽകിയ പുതിയ ഡാറ്റാബേസ് ലിങ്കും പേരും ഇമ്പോർട്ട് ചെയ്യുന്നു
# 🚀 ബട്ടൺ സെറ്റിങ്സ് എറർ ഒഴിവാക്കാൻ SINGLE_BUTTON കൂടി ഇമ്പോർട്ട് ചെയ്യുന്നു ✨
from info import DATABASE_URI, DATABASE_NAME, SINGLE_BUTTON, PROTECT_CONTENT, P_TTI_SHOW_OFF, MELCOW_NEW_USERS, SPELL_CHECK_REPLY

from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


class Database:
    
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        
        # 🚀 സ്റ്റാറ്റ്സ് പാനലുമായി 100% ഒത്തുപോകാൻ കളക്ഷൻ പേരുകൾ കൃത്യമായി സെറ്റ് ചെയ്യുന്നു ✨
        self.col = self.db.users
        self.grp = self.db.group
        self.req_one = self.db.connections  # connections_mdb-ന് പകരമുള്ള മെയിൻ ലിങ്ക്
        self.reqone = self.db.reqone        # fsub 1 റിക്വസ്റ്റുകൾ
        self.reqtwo = self.db.reqtwo        # fsub 2 റിക്വസ്റ്റുകൾ
        self.chatcol = self.db.chatcol      # fsub chat 1
        self.chatcol2 = self.db.chatcol2    # fsub chat 2

    def new_user(self, id, name):
        return dict(
            id = id,
            name = name,
            ban_status=dict(
                is_banned=False,
                ban_reason="",
            ),
        )

    def new_group(self, id, title):
        return dict(
            id = id,
            title = title,
            chat_status=dict(
                is_disabled=False,
                reason="",
            ),
        )
    
    async def add_user(self, id, name):
        user = self.new_user(id, name)
        await self.col.insert_one(user)
    
    async def is_user_exist(self, id):
        user = await self.col.find_one({'id':int(id)})
        return bool(user)
    
    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count
    
    async def remove_ban(self, id):
        ban_status = dict(
            is_banned=False,
            ban_reason=''
        )
        await self.col.update_one({'id': id}, {'$set': {'ban_status': ban_status}})
    
    async def ban_user(self, user_id, ban_reason="No Reason"):
        ban_status = dict(
            is_banned=True,
            ban_reason=ban_reason
        )
        await self.col.update_one({'id': user_id}, {'$set': {'ban_status': ban_status}})

    async def get_ban_status(self, id):
        default = dict(
            is_banned=False,
            ban_reason=''
        )
        user = await self.col.find_one({'id':int(id)})
        if not user:
            return default
        return user.get('ban_status', default)

    async def get_all_users(self):
        return self.col.find({})
    
    async def delete_user(self, user_id):
        await self.col.delete_many({'id': int(user_id)})

    async def get_banned(self):
        users = self.col.find({'ban_status.is_banned': True})
        chats = self.grp.find({'chat_status.is_disabled': True})
        b_chats = [chat['id'] async for chat in chats]
        b_users = [user['id'] async for user in users]
        return b_users, b_chats
    
    async def add_chat(self, chat, title):
        chat = self.new_group(chat, title)
        await self.grp.insert_one(chat)
    
    async def get_chat(self, chat):
        chat = await self.grp.find_one({'id':int(chat)})
        return False if not chat else chat.get('chat_status')
    
    async def re_enable_chat(self, id):
        chat_status=dict(
            is_disabled=False,
            reason="",
            )
        await self.grp.update_one({'id': int(id)}, {'$set': {'chat_status': chat_status}})
        
    async def update_settings(self, id, settings):
        await self.grp.update_one({'id': int(id)}, {'$set': {'settings': settings}})
        
    async def get_settings(self, id):
        # 🚀 SINGLE_BUTTON എറർ എന്നെന്നേക്കുമായി ഒഴിവാക്കാൻ ഡിഫോൾട്ട് സെറ്റിങ്സ് ഫിക്സ് ചെയ്യുന്നു ✨
        default = {
            'button': True,                  # SINGLE_BUTTON-ന് പകരം നേരിട്ട് True നൽകുന്നു
            'botpm': True,                  # P_TTI_SHOW_OFF-ന് പകരം നേരിട്ട് True നൽകുന്നു
            'file_secure': False,            # PROTECT_CONTENT-ന് പകരം നേരിട്ട് False നൽകുന്നു         
            'spell_check': True,             # SPELL_CHECK_REPLY-ന് പകരം നേരിട്ട് True നൽകുന്നു
            'welcome': True                  # MELCOW_NEW_USERS-ന് പകരം നേരിട്ട് True നൽകുന്നു           
        }
        chat = await self.grp.find_one({'id':int(id)})
        if chat:
            return chat.get('settings', default)
        return default

    
    async def disable_chat(self, chat, reason="No Reason"):
        chat_status=dict(
            is_disabled=True,
            reason=reason,
            )
        await self.grp.update_one({'id': int(chat)}, {'$set': {'chat_status': chat_status}})
    
    async def total_chat_count(self):
        count = await self.grp.count_documents({})
        return count
    
    async def get_all_chats(self):
        return self.grp.find({})

    async def get_db_size(self):
        return (await self.db.command("dbstats"))['dataSize']

    async def add_req_one(self, user_id):
        try:
            await self.reqone.insert_one({"user_id": int(user_id)})
            return
        except Exception as e:
            print(e)
            pass
        
    async def add_req_two(self, user_id):
        try:
            await self.reqtwo.insert_one({"id": int(user_id)})
            return
        except Exception as e:
            print(e)
            pass
            
    async def get_req_one(self, user_id):
        return await self.reqone.find_one({"user_id": int(user_id)})

    async def get_req_two(self, user_id):
        return await self.reqtwo.find_one({"id": int(user_id)})

    async def delete_all_one(self):
        await self.reqone.delete_many({})

    async def delete_all_two(self):
        await self.reqtwo.delete_many({})

    async def get_all_one_count(self): 
        count = 0
        async for req in self.reqone.find({}):
            count += 1
        return count

    async def get_all_two_count(self): 
        count = 0
        async for req in self.reqtwo.find({}):
            count += 1
        return count

    async def add_fsub_chat(self, chat_id):
        try:
            await self.chatcol.delete_many({})
            await self.reqone.delete_many({})
            await self.chatcol.insert_one({"chat_id": chat_id})
        except:
            pass

    async def get_fsub_chat(self):
        return await self.chatcol.find_one({})

    async def delete_fsub_chat(self, chat_id):
        await self.chatcol.delete_one({"chat_id": chat_id})
        await self.reqone.delete_many({})

    async def add_fsub_chat2(self, chat_id):
        try:
            await self.chatcol2.delete_many({})
            await self.reqtwo.delete_many({})
            await self.chatcol2.insert_one({"chat_id": chat_id})
        except:
            pass

    async def get_fsub_chat2(self):
        return await self.chatcol2.find_one({})

    async def delete_fsub_chat2(self, chat_id):
        await self.chatcol2.delete_one({"chat_id": chat_id})
        await self.reqtwo.delete_many({})
        
        
db = Database(DATABASE_URI, DATABASE_NAME)

