import logging
import asyncio
import re
from pyrogram import Client, filters, enums
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, ChatAdminRequired, UsernameInvalid, UsernameNotModified
from info import ADMINS, INDEX_REQ_CHANNEL as LOG_CHANNEL
from database.ia_filterdb import save_file, check_file
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import temp

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
lock = asyncio.Lock()


def get_forward_source(message):
    origin = getattr(message, "forward_origin", None)
    if origin:
        chat = getattr(origin, "chat", None)
        msg_id = getattr(origin, "message_id", None)
        if chat and msg_id:
            return chat.id, msg_id

    chat = getattr(message, "forward_from_chat", None)
    msg_id = getattr(message, "forward_from_message_id", None)
    if chat and msg_id:
        return chat.id, msg_id

    return None, None


@Client.on_callback_query(filters.regex(r"^index"))
async def index_files(bot, query):
    try:
        if query.data.startswith("index_cancel"):
            temp.CANCEL = True
            return await query.answer("Cancelling Indexing")

        parts = query.data.split("#")
        if len(parts) != 5:
            return await query.answer("Invalid indexing request.", show_alert=True)

        _, action, chat, lst_msg_id, from_user = parts

        if action == "reject":
            await query.message.delete()
            return await bot.send_message(
                int(from_user),
                f"Your Submission for indexing {chat} has been declined by our moderators.",
                reply_to_message_id=int(lst_msg_id)
            )

        if action != "accept":
            return await query.answer("Invalid request.", show_alert=True)

        if lock.locked():
            return await query.answer(
                "Wait until previous process complete.",
                show_alert=True
            )

        await query.answer("Processing...⏳", show_alert=True)
        msg = query.message

        if int(from_user) not in ADMINS:
            await bot.send_message(
                int(from_user),
                f"Your Submission for indexing {chat} has been accepted by our moderators and will be added soon.",
                reply_to_message_id=int(lst_msg_id)
            )

        await msg.edit(
            "Starting Indexing",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Cancel", callback_data="index_cancel")]]
            )
        )

        try:
            chat = int(chat)
        except (TypeError, ValueError):
            pass

        await index_files_to_db(int(lst_msg_id), chat, msg, bot)

    except Exception as e:
        logger.exception("Index callback error: %s", e)


@Client.on_message(
    filters.private &
    filters.incoming &
    filters.user(ADMINS)
)
async def send_for_index(bot, message):
    chat_id, last_msg_id = get_forward_source(message)

    if chat_id is None or last_msg_id is None:
        if message.text:
            regex = re.compile(
                r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)"
                r"(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$"
            )
            match = regex.match(message.text.strip())

            if not match:
                return await message.reply(
                    "Invalid channel message link."
                )

            chat_id = match.group(4)
            last_msg_id = int(match.group(5))

            if chat_id.isnumeric():
                chat_id = int("-100" + chat_id)
        else:
            return await message.reply(
                "⚠️ Forward ചെയ്ത message-ന്റെ source channel information Telegram നൽകിയിട്ടില്ല.\n\n"
                "Index ചെയ്യേണ്ട channel message നേരിട്ട് Forward ചെയ്യുക."
            )

    try:
        await bot.get_chat(chat_id)
    except ChannelInvalid:
        return await message.reply(
            "This may be a private channel / group. "
            "Make me an admin over there to index the files."
        )
    except (UsernameInvalid, UsernameNotModified):
        return await message.reply("Invalid Link specified.")
    except Exception as e:
        logger.exception("get_chat error: %s", e)
        return await message.reply(f"Errors - {e}")

    try:
        target = await bot.get_messages(chat_id, last_msg_id)
    except Exception:
        return await message.reply(
            "Make Sure That Iam An Admin In The Channel, "
            "if channel is private"
        )

    if not target or target.empty:
        return await message.reply(
            "This may be group and iam not a admin of the group."
        )

    user_id = message.from_user.id if message.from_user else 0

    buttons = [
        [
            InlineKeyboardButton(
                "Index to Database",
                callback_data=f"index#accept#{chat_id}#{last_msg_id}#{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "Close",
                callback_data="close_data"
            )
        ]
    ]

    return await message.reply(
        f"Do you Want To Index This Channel/ Group ?\n\n"
        f"Chat ID/ Username: <code>{chat_id}</code>\n"
        f"Last Message ID: <code>{last_msg_id}</code>",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@Client.on_message(
    filters.command("setskip") &
    filters.user(ADMINS)
)
async def set_skip_number(bot, message):
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) != 2:
            return await message.reply("Give me a skip number")

        skip = int(parts[1])
        temp.CURRENT = skip
        await message.reply(
            f"Successfully set SKIP number as {skip}"
        )
    except ValueError:
        await message.reply("Skip number should be an integer.")
    except Exception as e:
        logger.exception("Setskip error: %s", e)


async def index_files_to_db(lst_msg_id, chat, msg, bot):
    total_files = 0
    duplicate = 0
    errors = 0
    deleted = 0
    no_media = 0
    unsupported = 0

    async with lock:
        try:
            current = temp.CURRENT
            temp.CANCEL = False

            async for message in bot.iter_messages(
                chat,
                lst_msg_id,
                temp.CURRENT
            ):
                if temp.CANCEL:
                    await msg.edit(
                        f"Successfully Cancelled!!\n\n"
                        f"Saved <code>{total_files}</code> files to dataBase!\n"
                        f"Duplicate Files Skipped: <code>{duplicate}</code>\n"
                        f"Deleted Messages Skipped: <code>{deleted}</code>\n"
                        f"Non-Media messages skipped: <code>{no_media + unsupported}</code> "
                        f"(Unsupported Media - `{unsupported}` )\n"
                        f"Errors Occurred: <code>{errors}</code>"
                    )
                    break

                current += 1

                if current % 200 == 0:
                    await msg.edit_text(
                        text=(
                            f"Total messages fetched: <code>{current}</code>\n"
                            f"Total messages saved: <code>{total_files}</code>\n"
                            f"Duplicate Files Skipped: <code>{duplicate}</code>\n"
                            f"Deleted Messages Skipped: <code>{deleted}</code>\n"
                            f"Non-Media messages skipped: <code>{no_media + unsupported}</code> "
                            f"(Unsupported Media - `{unsupported}` )\n"
                            f"Errors Occurred: <code>{errors}</code>"
                        ),
                        reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton(
                                "Cancel",
                                callback_data="index_cancel"
                            )]]
                        )
                    )

                if message.empty:
                    deleted += 1
                    continue

                if not message.media:
                    no_media += 1
                    continue

                if message.media not in (
                    enums.MessageMediaType.VIDEO,
                    enums.MessageMediaType.AUDIO,
                    enums.MessageMediaType.DOCUMENT
                ):
                    unsupported += 1
                    continue

                media = getattr(
                    message,
                    message.media.value,
                    None
                )

                if not media:
                    unsupported += 1
                    continue

                media.file_type = message.media.value
                media.caption = message.caption

                try:
                    exists = await check_file(media)

                    if exists == "okda":
                        saved, status = await save_file(media)

                        if saved:
                            total_files += 1
                        elif status == 0:
                            duplicate += 1
                        elif status == 2:
                            errors += 1
                    else:
                        duplicate += 1

                except Exception:
                    errors += 1
                    logger.exception("File save error")

        except Exception as e:
            logger.exception("Indexing error")
            try:
                await msg.edit(f"Error: {e}")
            except Exception:
                pass
        else:
            await msg.edit(
                f"Succesfully saved <code>{total_files}</code> to dataBase!\n"
                f"Duplicate Files Skipped: <code>{duplicate}</code>\n"
                f"Deleted Messages Skipped: <code>{deleted}</code>\n"
                f"Non-Media messages skipped: <code>{no_media + unsupported}</code> "
                f"(Unsupported Media - `{unsupported}` )\n"
                f"Errors Occurred: <code>{errors}</code>"
            )
