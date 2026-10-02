from pyrogram import Client, filters
from info import CHANNELS
from database.ia_filterdb import save_file, check_file

# ഫിൽറ്ററിൽ നിന്നും audio ഒഴിവാക്കി (document, video എന്നിവ മാത്രം)
media_filter = filters.document | filters.video


@Client.on_message(filters.chat(CHANNELS) & media_filter)
async def media(bot, message):
    """Media Handler"""
    # ലൂപ്പിൽ നിന്നും "audio" ഒഴിവാക്കി
    for file_type in ("document", "video"):
        media = getattr(message, file_type, None)
        if media is not None:
            break
    else:
        return

    media.file_type = file_type
    media.caption = message.caption
    
    # ഡാറ്റാബേസ് പരിശോധിച്ച ശേഷം നേരിട്ട് സിംഗിൾ ഡിബിയിലേക്ക് സേവ് ചെയ്യുന്നു
    tru = await check_file(media)
    if tru == "okda":
        await save_file(media)
