from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors.exceptions.bad_request_400 import MessageTooLong, PeerIdInvalid
from info import ADMINS, LOG_CHANNEL, SUPPORT_CHAT, MELCOW_NEW_USERS, REQ_CHANNEL1, REQ_CHANNEL2
from database.users_chats_db import db
# Mediaa, clientDB3 എന്നിവ ഒഴിവാക്കി
from database.ia_filterdb import Media, db as clientDB, db1 as clientDB2 
from utils import get_size, temp, get_settings, run_broadcast_in_background
from Script import script
from pyrogram.errors import ChatAdminRequired
import os
import asyncio

@Client.on_message(filters.command('checkk') & filters.incoming)
async def get_ststs(bot, message):
    rju = await message.reply('Fetching stats..')
    tot = await Media.count_documents()
    tota = await Mediaa.count_documents()
    total = tot + tota
    users = await db.total_users_count()
    chats = await db.total_chat_count()
    
    stats = await clientDB.command('dbStats')
    used_dbSize = (stats['dataSize']/(1024*1024))+(stats['indexSize']/(1024*1024))        
    free_dbSize = 512-used_dbSize
    
    stats2 = await clientDB2.command('dbStats')
    used_dbSize2 = (stats2['dataSize']/(1024*1024))+(stats2['indexSize']/(1024*1024))
    free_dbSize2 = 512-used_dbSize2
    
    stats3 = await clientDB3.command('dbStats')
    used_dbSize3 = (stats3['dataSize']/(1024*1024))+(stats3['indexSize']/(1024*1024))
    free_dbSize3 = 512-used_dbSize3
    
    status_text = (
        "📊 **Bot Statistics**\n\n"
        f"▪️ **Total Files:** {total}\n"
        f"▪️ **Main DB Files (Media):** {tot}\n"
        f"▪️ **DB 2 Files (Mediaa):** {tota}\n\n"
        ...



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
