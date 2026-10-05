import re
import os
import json
import base64
import logging
from pyrogram import filters, Client, enums
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, UsernameInvalid, UsernameNotModified
from info import ADMINS, LOG_CHANNEL, FILE_STORE_CHANNEL, PUBLIC_FILE_STORE
from database.ia_filterdb import unpack_new_file_id
from utils import temp

logger = logging.getLogger(__name__)

async def allowed(_, __, message):
    if PUBLIC_FILE_STORE:
        return True
    if message.from_user and message.from_user.id in ADMINS:
        return True
    return False

@Client.on_message(filters.command(['link', 'plink']) & filters.create(allowed))
async def gen_link_s(bot, message):
    replied = message.reply_to_message
    if not replied:
        return await message.reply('Reply to a message to get a shareable link.')
        
    file_type = replied.media
    if file_type not in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.AUDIO, enums.MessageMediaType.DOCUMENT]:
        return await message.reply("Reply to a supported media asset (Document, Video, or Audio).")
        
    if message.has_protected_content and message.chat.id not in ADMINS:
        return await message.reply("Access Denied.")
        
    file_id, ref = unpack_new_file_id((getattr(replied, file_type.value)).file_id)
    string = 'filep_' if message.command[0].lower() == "plink" else 'file_'
    string += file_id
    outstr = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
    await message.reply(f"Here is your Link:\n<code>https://t.me{temp.U_NAME}?start={outstr}</code>")

# Fixed: Updated the command list matching array criteria to accurately track text commands
@Client.on_message(filters.command(['batch', 'pbatch']) & filters.create(allowed))
async def gen_link_batch(bot, message):
    # Fixed: Uses split() without explicit spacing strings to handle multiple spaces safely
    links = message.text.strip().split()
    if len(links) != 3:
        return await message.reply("Use correct format.\nExample: <code>/batch https://t.mesources_cods/10 https://t.mesources_cods/20</code>")
        
    cmd, first, last = links
    regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)\$")
    
    match = regex.match(first)
    if not match:
        return await message.reply('Invalid starting message link specified.')
    f_chat_id = match.group(4)
    f_msg_id = int(match.group(5))
    if f_chat_id.isnumeric():
        f_chat_id = int(("-100" + f_chat_id))

    match = regex.match(last)
    if not match:
        return await message.reply('Invalid ending message link specified.')
    l_chat_id = match.group(4)
    l_msg_id = int(match.group(5))
    if l_chat_id.isnumeric():
        l_chat_id = int(("-100" + l_chat_id))

    if f_chat_id != l_chat_id:
        return await message.reply("Chat IDs do not match. Both links must originate from the same channel.")
        
    try:
        chat_id = (await bot.get_chat(f_chat_id)).id
    except ChannelInvalid:
        return await message.reply('This may be a private channel/group. Make me an admin there to read the files.')
    except (UsernameInvalid, UsernameNotModified):
        return await message.reply('Invalid link specified.')
    except Exception as e:
        return await message.reply(f'Errors encountered: {e}')

    sts = await message.reply("Generating link for your batch request...\nThis may take some time.")
    
    if chat_id in FILE_STORE_CHANNEL:
        string = f"{f_msg_id}_{l_msg_id}_{chat_id}_{cmd.lower().strip()}"
        b_64 = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
        return await sts.edit(f"Here is your link:\n<code>https://t.me/{temp.U_NAME}?start=DSTORE-{b_64}</code>")

    FRMT = "Generating Link...\nTotal Messages: `{total}`\nProcessed: `{current}`\nRemaining: `{rem}`"

    outlist = []
    og_msg = 0
    tot = 0
    
    # Fixed: Correctly calculated target total range limit boundary to match bot.py's implementation
    total_messages_to_scan = (l_msg_id - f_msg_id) + 1
    
    async for msg in bot.iter_messages(f_chat_id, limit=total_messages_to_scan, offset=f_msg_id):
        tot += 1
        if msg.empty or msg.service:
            continue
        if not msg.media:
            continue
            
        try:
            file_type = msg.media
            file = getattr(msg, file_type.value)
            caption = getattr(msg, 'caption', '')
            if caption and hasattr(caption, 'html'):
                caption = caption.html
            elif caption:
                caption = str(caption)
                
            if file:
                file_data = {
                    "file_id": file.file_id,
                    "caption": caption,
                    "title": getattr(file, "file_name", ""),
                    "size": file.file_size,
                    "protect": cmd.lower().strip() == "/pbatch",
                }
                og_msg += 1
                outlist.append(file_data)
        except Exception:
            pass
            
        if not tot % 20:
            try:
                await sts.edit(FRMT.format(total=total_messages_to_scan, current=tot, rem=max(0, total_messages_to_scan - tot)))
            except Exception:
                pass
                
    if not outlist:
        return await sts.edit("❌ No supported media files were found within the specified range.")

    file_path = f"batchmode_{message.from_user.id}.json"
    with open(file_path, "w+") as out:
        json.dump(outlist, out)
        
    post = await bot.send_document(
        LOG_CHANNEL, 
        file_path, 
        file_name="Batch.json", 
        caption="⚠️ Generated Batch File Store Mapping."
    )
    
    if os.path.exists(file_path):
        os.remove(file_path)
        
    file_id, ref = unpack_new_file_id(post.document.file_id)
    await sts.edit(f"Here is your batch link containing `{og_msg}` files:\n<code>https://t.me/{temp.U_NAME}?start=BATCH-{file_id}</code>")
