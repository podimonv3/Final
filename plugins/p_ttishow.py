from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors.exceptions.bad_request_400 import MessageTooLong, PeerIdInvalid
from info import ADMINS, LOG_CHANNEL, SUPPORT_CHAT, MELCOW_NEW_USERS, REQ_CHANNEL1, REQ_CHANNEL2
from utils import get_size, temp, get_settings, run_broadcast_in_background
from Script import script
from pyrogram.errors import ChatAdminRequired
import os
import asyncio
# 🚀 ia_filterdb-ൽ നിന്ന് db1 (clientDB2) ഒഴിവാക്കി മെയിൻ db (clientDB) മാത്രം ഇമ്പോർട്ട് ചെയ്യുന്നു ✨
from database.ia_filterdb import Media, db as clientDB
from database.users_chats_db import db

# ====================================================================
# 🚀 ALL-IN-ONE BOT & DATABASE FULL STATS COMMAND ✨
# ====================================================================

@Client.on_message(filters.command("bot_stats") & filters.user(ADMINS))
async def get_combined_bot_and_db_stats_cmd(client: Client, message: Message):
    """ബോട്ട് വിവരങ്ങളും ഡാറ്റാബേസ് കളക്ഷനുകളും ഒരൊറ്റ കമാൻഡിൽ കാണിക്കുന്നു 📊"""
    msg = await message.reply_text("⏳ ഡാറ്റാബേസ് വിവരങ്ങൾ പൂർണ്ണമായി ശേഖരിച്ചുകൊണ്ടിരിക്കുന്നു...")
    
    try:
        # 1. ഒരൊറ്റ മെയിൻ ഡാറ്റാബേസിൽ നിന്ന് മാത്രം വിവരങ്ങൾ വേഗത്തിൽ എടുക്കുന്നു
        total_connections = await clientDB['connections'].count_documents({})
        total_filters = await clientDB['filters'].count_documents({})
        total_gfilters = await clientDB['gfilters'].count_documents({})
        total_locks = await clientDB['locks'].count_documents({})
        total_poster = await clientDB['poster'].count_documents({})
        total_moviereq = await clientDB['moviereq'].count_documents({})
        total_media = await clientDB['Media'].count_documents({}) 
        total_users = await db.total_users_count()
        total_group = await db.total_chat_count()
        
        # 2. മംഗോഡിബിയിൽ നിലവിലുള്ള മുഴുവൻ കളക്ഷൻ ഫോൾഡറുകളുടെ പേരുകൾ എടുക്കുന്നു
        collections = await clientDB.list_collection_names()
        
        # 3. ആകെ വിവരങ്ങൾ കൂട്ടിയെടുക്കുന്നു
        total_all_docs = (
            total_connections + total_filters + total_gfilters + total_locks + 
            total_poster + total_moviereq + total_media + total_users + total_group
        )
        
        # 4. റിസൾട്ട് ഒരൊറ്റ മെസ്സേജിൽ ഫോർമാറ്റ് ചെയ്യുന്നു
        status_text = f"📊 <b>★ BOT & DATABASE FULL REPORT ★</b>\n"
        status_text += f"🗄️ <b>DB Name:</b> <code>{DATABASE_NAME}</code>\n\n"
        
        status_text += "📈 <b>Core Bot Growth Status:</b>\n"
        status_text += f" ├ 🔗 <code>connections</code> → <b>{total_connections}</b> Linked Users\n"
        status_text += f" ├ 📁 <code>Media</code> → <b>{total_media}</b> Indexed Movies\n"
        status_text += f" ├ 👥 <code>users</code> → <b>{total_users}</b> Total Bot Users\n"
        status_text += f" └ 👥 <code>group</code> → <b>{total_group}</b> Total Bot Chats\n\n"
        
        status_text += "📂 <b>Database Collections List:</b>\n"
        for col_name in sorted(collections):
            col_count = await clientDB[col_name].count_documents({})
            # നമ്മൾ ഒപ്റ്റിമൈസ് ചെയ്ത സിംഗിൾ കളക്ഷനുകൾക്ക് പ്രത്യേക നക്ഷത്ര ചിഹ്നം നൽകുന്നു
            if col_name in ["filters", "connections", "locks", "poster", "moviereq"]:
                status_text += f" ├ <code>{col_name}</code> → <b>{col_count}</b> ✨\n"
            else:
                status_text += f" ├ <code>{col_name}</code> → <b>{col_count}</b>\n"
                
        status_text += f" └ <b>Total Active Collections:</b> {len(collections)}\n\n"
        status_text += f"🗂️ <b>Total Overall Documents in DB:</b> <code>{total_all_documents}</code>\n\n"
        status_text += f"💡 <i>Note: ✨ എന്ന് അടയാളപ്പെടുത്തിയത് നമ്മൾ ഒപ്റ്റിമൈസ് ചെയ്ത സിംഗിൾ കളക്ഷനുകളാണ്.</i>"
        
        await msg.edit_text(status_text, parse_mode=enums.ParseMode.HTML)
        
    except Exception as e:
        await msg.edit_text(f"❌ സ്റ്റാറ്റ്സ് വിവരങ്ങൾ ശേഖരിക്കുന്നതിൽ പരാജയപ്പെട്ടു!\nഎറർ: <code>{e}</code>", parse_mode=enums.ParseMode.HTML)


@Client.on_message(filters.command("broadcast") & filters.user(ADMINS))
async def main_broadcast(client, message):
    if not message.reply_to_message:
        await message.reply_text("❌ ദയവായി ബ്രോഡ്കാസ്റ്റ് ചെയ്യേണ്ട മെസ്സേജിന് മറുപടിയായി ഈ കമാൻഡ് അയക്കുക.")
        return
    status_msg = await message.reply_text("📢 ബ്രോഡ്കാസ്റ്റിംഗ് ബാക്ക്ഗ്രൗണ്ടിൽ ആരംഭിച്ചിട്ടുണ്ട്. പൂർത്തിയാകുമ്പോൾ ഈ മെസ്സേജ് അപ്‌ഡേറ്റ് ആകും...")
    asyncio.create_task(run_broadcast_in_background(client, message.reply_to_message, status_msg))


@Client.on_message(filters.command('chats') & filters.user(ADMINS))
async def list_chats(bot, message):
    rju = await message.reply("`Processing... Please wait...`")
    chats = await db.get_all_chats()  
    file_name = "chats.txt"
    with open(file_name, "w", encoding="utf-8") as file:
        file.write("List of Chats/Groups connected to the bot:\n\n")
        async for chat in chats:
            chat_id = chat.get('id', 'N/A')
            chat_title = chat.get('title', 'Unknown Title')
            file.write(f"Chat Title: {chat_title} | Chat ID: {chat_id}\n")
    if os.path.exists(file_name):
        with open(file_name, 'rb') as doc:
            await message.reply_document(doc, caption="List Of Chats")
        await rju.delete()
        os.remove(file_name)
    else:
        await rju.edit("Failed to generate chats.txt file!")



@Client.on_message(filters.command('users') & filters.user(ADMINS))
async def list_users(bot, message):
    raju = await message.reply('Getting List Of Users...')
    users = await db.get_all_users()
    out = "Users Saved In DB Are:\n\n"
    
    async for user in users:
        out += f"Name: {user['name']} | ID: {user['id']}"
        if user['ban_status']['is_banned']:
            out += ' ( Banned User )'
        out += '\n'
        
    # എപ്പോഴും .txt ഫയൽ ആയി മാത്രം അയക്കാൻ വേണ്ടി:
    file_name = 'users.txt'
    with open(file_name, 'w+', encoding='utf-8') as outfile:
        outfile.write(out)
        
    await message.reply_document(file_name, caption="List Of Users")
    await raju.delete()

@Client.on_message(filters.command('gen_link') & filters.user(ADMINS))
async def gen_invite(bot, message):
    if len(message.command) == 1:
        return await message.reply('Give me a chat id')
    chat = message.command[1]
    try:
        chat = int(chat)
    except:
        return await message.reply('Give Me A Valid Chat ID')
    try:
        link = await bot.create_chat_invite_link(chat)
    except ChatAdminRequired:
        return await message.reply("Invite Link Generation Failed, Iam Not Having Sufficient Rights")
    except Exception as e:
        return await message.reply(f'Error {e}')
    await message.reply(f'Here is your Invite Link {link.invite_link}')


@Client.on_message(filters.command('purge_one') & filters.private & filters.user(ADMINS))
async def purge_req_one(bot, message):
    r = await message.reply("`processing...`")
    await db.delete_all_one()
    await r.edit("**Req db Cleared**" )


@Client.on_message(filters.command('purge_two') & filters.private & filters.user(ADMINS))
async def purge_req_two(bot, message):
    r = await message.reply("`processing...`")
    await db.delete_all_two()
    await r.edit("**Req db Cleared**" )

@Client.on_message(filters.command("totalreq") & filters.user(ADMINS))
async def total_requests(bot, message): 
    rju = await message.reply('Fetching stats..')
    total_one = await db.get_all_one_count()
    total_two = await db.get_all_two_count()
    
    if REQ_CHANNEL1 != False: 
        req_channel1 = await bot.get_chat(REQ_CHANNEL1)
        req_channel1 = req_channel1.title
    else:
        req_channel1 = "REQ_CHANNEL1"
        
    if REQ_CHANNEL2 != False:
        req_channel2 = await bot.get_chat(REQ_CHANNEL2)
        req_channel2 = req_channel2.title
    else:
        req_channel2 = "REQ_CHANNEL2"
    
    # 🛠️ MessageNotModified എറർ ഒഴിവാക്കാനായി try...except ബ്ലോക്ക് ചേർത്തു
    try:
        await rju.edit(
            f"<b>📊 Total Join Requests Stats</b>\n\n"
            f"📢 {req_channel1} : <code>{total_one}</code>\n"
            f"📢 {req_channel2} : <code>{total_two}</code>",
            parse_mode=enums.ParseMode.HTML
        )
    except Exception:
        # ഒരേ ഡാറ്റ വെച്ച് വീണ്ടും എഡിറ്റ് ചെയ്യാൻ നോക്കുമ്പോൾ വരുന്ന എറർ ഇവിടെ സ്കിപ്പ് ചെയ്യും
        pass
