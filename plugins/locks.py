import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from info import ADMINS
from database.lock_filterdb import settings_collection, get_group_locks, set_group_lock
 
VALID_LOCKS = {
    "photos": "Photos", "videos": "Videos", "stickers": "Stickers / Emojis",
    "voice": "Voice Messages", "audio": "Audios / Music", "document": "Documents",
    "animation": "GIFs / Animations", "poll": "Polls", "video_note": "Video Messages",
    "contact": "Contacts", "location": "Locations", "inline": "Inline Bots",
    "story": "Stories", "game": "Games", "channel": "As a Channel",
    "new_members": "New Members Info", "left_members": "Left Members Info",
    "title_changed": "Group Title Changed", "photo_changed": "Group Photo Updates",
    "pinned": "Pinned Messages Info", "video_chat": "Video Chat Actions",
    "fwd_channel": "Channel Forwards", "usernames": "@Usernames",
    "hashtags": "#Hashtags", "commands": "/Commands", "emails": "E-mails",
    "links": "Links / URLs", "text_styles": "Bold/Italic/Spoiler", "edited": "Edited Messages"
}

async def get_locks_markup(chat_id: int):
    # ഇവിടെ നമ്മൾ ഫങ്ഷൻ അസിങ്ക് (async def) ആക്കുകയും ഉള്ളിൽ await ചേർക്കുകയും ചെയ്തു
    locks = await get_group_locks(chat_id)
    keyboard = []
    row = []
    for key, name in VALID_LOCKS.items():
        status_emoji = "🗑️" if locks.get(key) else "✅"
        row.append(InlineKeyboardButton(f"{name} {status_emoji}", callback_data=f"lck_{key}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row: keyboard.append(row)
    keyboard.append([InlineKeyboardButton("📊 Close Settings", callback_data="lck_close")])
    return InlineKeyboardMarkup(keyboard)




# 🛠️ ഗ്രൂപ്പിൽ നേരിട്ട് ലോക്കുകൾ നിയന്ത്രിക്കാനുള്ള സിസ്റ്റം 🔒/🔓
@Client.on_message(filters.group & filters.command(["lock", "unlock"]))
async def lock_unlock_command(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    if not user_id: return

    chat_id = message.chat.id
    chat_title = message.chat.title
    
    try:
        member = await message.chat.get_member(user_id)
        if member.status not in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR] and user_id != ADMINS:
            return
    except: return

    if len(message.command) < 2:
        available_types = "\n".join([f"• <code>{k}</code>" for k in VALID_LOCKS.keys()])
        await message.reply_text(
            f"⚠️ **ഉപയോഗിക്കേണ്ട രീതി:**\n"
            f"🔒 ലോക്ക് ചെയ്യാൻ: <code>/lock [media_type]</code>\n"
            f"🔓 അൺലോക്ക് ചെയ്യാൻ: <code>/unlock [media_type]</code>\n\n"
            f"**Media Types:**\n{available_types}",
            parse_mode=enums.ParseMode.HTML
        )
        return

    action = message.command[0].lower()
    media = message.command[1].lower()

    if media not in VALID_LOCKS:
        await message.reply_text(f"❌ തെറ്റായ മീഡിയ ടൈപ്പ്! പരിശോധിക്കാൻ വെറുതെ <code>/{action}</code> എന്ന് ടൈപ്പ് ചെയ്യുക.", parse_mode=enums.ParseMode.HTML)
        return

    status = True if action == "lock" else False
    # ഇവിടെ await ചേർത്തു 
    await set_group_lock(chat_id, media, status)
    
    status_text = "🔒 **ലോക്ക് ചെയ്തു (Delete Mode)**" if status else "🔓 **അനുവദിച്ചു (Allow Mode)**"
    await message.reply_text(
        f"✅ <b>{chat_title}</b> ഗ്രൂപ്പിൽ <b>{VALID_LOCKS[media].upper()}</b> ഇനി മുതൽ {status_text}!", 
        parse_mode=enums.ParseMode.HTML
    )

# 📋 മുഴുവൻ ലോക്ക് സ്റ്റാറ്റസും ഗ്രൂപ്പിൽ പരിശോധിക്കാനുള്ള കമാൻഡ് 🔍
@Client.on_message(filters.group & filters.command(["locktypes", "locks"]))
async def view_all_lock_types(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    if not user_id: return

    chat_id = message.chat.id
    chat_title = message.chat.title
    
    try:
        member = await message.chat.get_member(user_id)
        if member.status not in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR] and user_id != ADMINS:
            return
    except: return

    # ഇവിടെ await ചേർത്തു
    locks = await get_group_locks(chat_id)
    status_text = f"📋 <b>★ {chat_title} - LOCK TYPES STATUS ★</b>\n\n"
    
    for key, name in VALID_LOCKS.items():
        emoji = "🔴 <b>LOCK</b>" if locks.get(key) else "🟢 <b>ALLOW</b>"
        status_text += f"• <code>{key}</code> → {emoji}\n"
        
    status_text += f"\n🛠️ <b>മാറ്റങ്ങൾ വരുത്താൻ:</b>\n<code>/lock [type]</code> അല്ലെങ്കിൽ <code>/unlock [type]</code> ഉപയോഗിക്കുക."
    await message.reply_text(status_text, parse_mode=enums.ParseMode.HTML)

# 🚨 ഒന്നിച്ച് ലോക്ക്/അൺലോക്ക് ചെയ്യാനുള്ള കമാൻഡുകൾ 🔒/🔓
@Client.on_message(filters.group & filters.command(["lockall", "unlockall"]))
async def lock_unlock_all_command(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    if not user_id: return

    chat_id = message.chat.id
    chat_title = message.chat.title
    
    try:
        member = await message.chat.get_member(user_id)
        if member.status not in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR] and user_id != ADMINS:
            return
    except: return
            
    action = message.command[0].lower()
    status = True if action == "lockall" else False

    updated_locks = {key: status for key in VALID_LOCKS.keys()}

    # 🚀 Motor അസിങ്ക് ഡ്രൈവറിന് അനുയോജ്യമായ രീതിയിൽ update_one കൃത്യമാക്കുന്നു ✨
    await settings_collection.update_one(
        {'_id': f'locks_{int(chat_id)}'}, 
        {'$set': {'locks': updated_locks}}, 
        upsert=True
    )

    
    if status:
        msg_text = f"🚨 <b>{chat_title} - EMERGENCY LOCKDOWN!</b> 🚨\n\n🔒 ഗ്രൂപ്പിലെ മുഴുവൻ മീഡിയകളും ഒന്നിച്ച് <b>ലോക്ക് ചെയ്തിരിക്കുന്നു</b>. ഇനി അഡ്മിൻമാർക്ക് മാത്രമേ മെസ്സേജ് അയക്കാൻ സാധിക്കൂ!"
    else:
        msg_text = f"🔓 <b>{chat_title} - LOCKDOWN LIFTED!</b> 🔓\n\n✅ ഗ്രൂപ്പിലെ മുഴുവൻ ലോക്കുകളും ഒന്നിച്ച് <b>ഒഴിവാക്കിയിരിക്കുന്നു</b>."

    await message.reply_text(msg_text, parse_mode=enums.ParseMode.HTML)

# ⚙️ ഇൻലൈൻ ബട്ടൺ വഴി ഗ്രൂപ്പിൽ തന്നെ സെറ്റിങ്സ് പാനൽ കാണിക്കാൻ
@Client.on_message(filters.group & filters.command("settings"))
async def group_settings_panel(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else None
    if not user_id: return

    chat_id = message.chat.id
    chat_title = message.chat.title
    
    try:
        member = await message.chat.get_member(user_id)
        if member.status not in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR] and user_id != ADMINS:
            return
    except: return

    # get_locks_markup എന്ന ഫങ്ഷന് മുന്നിൽ await ചേർത്തു
    await message.reply_text(
        f"⚙️ <b>★ {chat_title} - SETTINGS ★</b>\n\n✅ = Allow\n🗑️ = Delete",
        reply_markup=await get_locks_markup(chat_id), parse_mode=enums.ParseMode.HTML
    )

# ഇൻലൈൻ ബട്ടൺ ക്ലിക്ക് ഹാൻഡ്‌ലർ
@Client.on_callback_query(filters.regex("^lck_"))
async def locks_callback_handler(client: Client, query):
    user_id = query.from_user.id
    chat_id = query.message.chat.id
    
    try:
        member = await query.message.chat.get_member(user_id)
        if member.status not in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR] and user_id != ADMINS:
            await query.answer("❌ നിങ്ങൾക്ക് ഇതിന് അനുവാദമില്ല!", show_alert=True)
            return
    except: return

    action = query.data.split("_")[1]
    if action == "close":
        await query.message.delete()
        return

    # ഈ രണ്ട് വരികളിൽ await ചേർത്തു
    locks = await get_group_locks(chat_id)
    new_status = not locks.get(action, False)
    await set_group_lock(chat_id, action, new_status)
    
    await query.answer(f"{VALID_LOCKS[action]} മാറ്റം വരുത്തി!")
    try: 
        # ഇവിടെയും await get_locks_markup ചേർത്തു
        await query.edit_message_reply_markup(reply_markup=await get_locks_markup(chat_id))
    except: pass


# 🛡️ മീഡിയകളും മറ്റ് മെസ്സേജുകളും ചെക്ക് ചെയ്ത് ഡിലീറ്റ് ചെയ്യുന്ന ഭാഗം
@Client.on_message(filters.group, group=2)
async def check_group_media_locks(client: Client, message: Message):
    chat_id = int(message.chat.id)
    # ഇവിടെ await ചേർത്തു
    locks = await get_group_locks(chat_id)

    if getattr(message, "sender_chat", None) and message.sender_chat.type == enums.ChatType.CHANNEL:
        if locks.get("channel") and not getattr(message, "is_automatic_forward", False):
            try: await message.delete(); return
            except: pass

    should_delete = False

    if getattr(message, "forward_from_chat", None) and message.forward_from_chat.type == enums.ChatType.CHANNEL:
        if locks.get("fwd_channel"): should_delete = True

    if getattr(message, "new_chat_members", None) and locks.get("new_members"): should_delete = True
    elif getattr(message, "left_chat_member", None) and locks.get("left_members"): should_delete = True
    elif getattr(message, "new_chat_title", None) and locks.get("title_changed"): should_delete = True
    elif (getattr(message, "new_chat_photo", None) or getattr(message, "delete_chat_photo", None)) and locks.get("photo_changed"): should_delete = True
    elif getattr(message, "pinned_message", None) and locks.get("pinned"): should_delete = True
    elif (getattr(message, "video_chat_started", None) or getattr(message, "video_chat_ended", None) or getattr(message, "video_chat_members_invited", None) or getattr(message, "video_chat_scheduled", None)) and locks.get("video_chat"): should_delete = True

    elif getattr(message, "from_user", None):
        user_id = message.from_user.id
        try:
            member = await message.chat.get_member(user_id)
            if member.status in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR] or user_id == ADMINS:
                return
        except: return

        if getattr(message, "photo", None) and locks.get("photos"): should_delete = True
        elif getattr(message, "video", None) and locks.get("videos"): should_delete = True
        elif getattr(message, "sticker", None) and locks.get("stickers"): should_delete = True
        elif getattr(message, "voice", None) and locks.get("voice"): should_delete = True
        elif getattr(message, "audio", None) and locks.get("audio"): should_delete = True
        elif getattr(message, "document", None) and locks.get("document"): should_delete = True
        elif getattr(message, "animation", None) and locks.get("animation"): should_delete = True
        elif getattr(message, "poll", None) and locks.get("poll"): should_delete = True
        elif getattr(message, "video_note", None) and locks.get("video_note"): should_delete = True
        elif getattr(message, "contact", None) and locks.get("contact"): should_delete = True
        elif getattr(message, "location", None) and locks.get("location"): should_delete = True
        elif getattr(message, "via_bot", None) and locks.get("inline"): should_delete = True
        elif getattr(message, "story", None) and locks.get("story"): should_delete = True
        elif getattr(message, "game", None) and locks.get("game"): should_delete = True

        elif (getattr(message, "text", None) or getattr(message, "caption", None)):
            entities = message.entities if message.text else message.caption_entities
            if entities:
                for ent in entities:
                    if ent.type == enums.MessageEntityType.MENTION and locks.get("usernames"): should_delete = True
                    elif ent.type == enums.MessageEntityType.HASHTAG and locks.get("hashtags"): should_delete = True
                    elif ent.type == enums.MessageEntityType.BOT_COMMAND and locks.get("commands"): should_delete = True
                    elif ent.type == enums.MessageEntityType.EMAIL and locks.get("emails"): should_delete = True
                    elif ent.type in [enums.MessageEntityType.URL, enums.MessageEntityType.TEXT_LINK] and locks.get("links"): should_delete = True
                    elif ent.type in [enums.MessageEntityType.BOLD, enums.MessageEntityType.ITALIC, enums.MessageEntityType.SPOILER, enums.MessageEntityType.CODE] and locks.get("text_styles"): should_delete = True
                    
                    if should_delete:
                        break
                        
    if should_delete:
        try: await message.delete()
        except: pass  
    

# എഡിറ്റ് ചെയ്യുന്ന മെസ്സേജുകൾ ഡിലീറ്റ് ചെയ്യാൻ
@Client.on_edited_message(filters.group, group=3)
async def check_edited_messages(client: Client, message: Message):
    chat_id = int(message.chat.id)
    # ഇവിടെ await ചേർത്തു
    locks = await get_group_locks(chat_id)
    from_user = getattr(message, "from_user", None)
    if locks.get("edited") and from_user:
        user_id = from_user.id
        try:
            member = await message.chat.get_member(user_id)
            if member.status in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR] or user_id == ADMINS: return
            await message.delete()
        except: pass

