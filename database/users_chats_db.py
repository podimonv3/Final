import logging
# 🚀 motor പൂർണ്ണമായും അതുപോലെ AsyncIOMotorClient-ഉം ഒന്നിച്ച് ഇമ്പോർട്ട് ചെയ്യുന്നു ✨
import motor
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient
# info ഫയലിൽ നമ്മൾ നൽകിയ പുതിയ ഡാറ്റാബേസ് ലിങ്കും പേരും ഇമ്പോർട്ട് ചെയ്യുന്നു
# 🚀 ബട്ടൺ സെറ്റിങ്സ് എറർ ഒഴിവാക്കാൻ SINGLE_BUTTON കൂടി ഇമ്പോർട്ട് ചെയ്യുന്നു ✨
from info import DATABASE_URI, DATABASE_NAME, SINGLE_BUTTON, PROTECT_CONTENT, P_TTI_SHOW_OFF, MELCOW_NEW_USERS,SPELL_CHECK_REPLY

from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# 🚀 ഒരൊറ്റ പുതിയ DATABASE_URI ലിങ്ക് മാത്രം ഇവിടെയും സെറ്റ് ചെയ്യുന്നു ✨
client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]


class Database:
    
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users
        self.grp = self.db.group
        self.req_one = self.db.reqone
        self.req_two = self.db.reqtwo
        self.chat_col = self.db.chatcol
        self.chat_col2 = self.db.chatcol2


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
        default = {
            'button': SINGLE_BUTTON,
            'botpm': P_TTI_SHOW_OFF,
            'file_secure': PROTECT_CONTENT,            
            'spell_check': SPELL_CHECK_REPLY,
            'welcome': MELCOW_NEW_USERS            
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
            await self.req_one.insert_one({"user_id": int(user_id)})
            return
        except Exception as e:
            print(e)
            pass
        
    async def add_req_two(self, user_id):
        try:
            await self.req_two.insert_one({"id": int(user_id)})
            return
        except Exception as e:
            print(e)
            pass
            
    async def get_req_one(self, user_id):
        return await self.req_one.find_one({"user_id": int(user_id)})

    async def get_req_two(self, user_id):
        return await self.req_two.find_one({"id": int(user_id)})

    async def delete_all_one(self):
        await self.req_one.delete_many({})

    async def delete_all_two(self):
        await self.req_two.delete_many({})

    async def get_all_one_count(self): 
        count = 0
        async for req in self.req_one.find({}):
            count += 1
        return count

    async def get_all_two_count(self): 
        count = 0
        async for req in self.req_two.find({}):
            count += 1
        return count

    async def add_fsub_chat(self, chat_id):
        try:
            await self.chat_col.delete_many({})
            await self.req_one.delete_many({})
            await self.chat_col.insert_one({"chat_id": chat_id})
        except:
            pass

    async def get_fsub_chat(self):
        return await self.chat_col.find_one({})

    async def delete_fsub_chat(self, chat_id):
        await self.chat_col.delete_one({"chat_id": chat_id})
        await self.req_one.delete_many({})

    async def add_fsub_chat2(self, chat_id):
        try:
            await self.chat_col2.delete_many({})
            await self.req_two.delete_many({})
            await self.chat_col2.insert_one({"chat_id": chat_id})
        except:
            pass

    async def get_fsub_chat2(self):
        return await self.chat_col2.find_one({})

    async def delete_fsub_chat2(self, chat_id):
        await self.chat_col2.delete_one({"chat_id": chat_id})
        await self.req_two.delete_many({})
        
        
db = Database(DATABASE_URI, DATABASE_NAME)
