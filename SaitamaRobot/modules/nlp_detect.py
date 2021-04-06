from pyrogram import filters
from SaitamaRobot import kp, CF_API_KEY, EVENT_LOGS
from pyrogram.handlers import MessageHandler
from pyrogram.types import ChatPermissions, Message
from pyrogram.errors import BadRequest
import aiohttp, json, asyncio
from SaitamaRobot.modules.global_bans import SPB_MODE
import SaitamaRobot.modules.sql.nlp_detect_sql as sql

from pyrogram.types import Message

session = aiohttp.ClientSession()


async def admin_check(message: Message) -> bool:
    client = message._client
    chat_id = message.chat.id
    user_id = message.from_user.id

    check_status = await client.get_chat_member(
        chat_id=chat_id,
        user_id=user_id
    )
    admin_strings = [
        "creator",
        "administrator"
    ]
    return check_status.status in admin_strings

__mod_name__ = "NLP"
__help__ = f"""
*Chatroom Spam Prediction*
This feature uses @Intellivoid's Coffeehouse AI to
process chat messages and detect spam.
This comes under Coffehouse' NLP. Learn more about
it [here](https://docs.intellivoid.net/coffeehouse/v1/nlp/spam_prediction/chatroom)
*Command:*
• `/nlpstat <on/off/yes/no>`*:* toggle NLP in your chat.
"""

@kp.on_message(filters.command("nlpstat"), group=8)
async def nlp_mode(client, message):
    is_admin = await admin_check(message)
    args = message.text.split(None, 1)

    if is_admin == True:
        if len(args) > 1:
            if args[1].lower() in ["on", "yes"]:
                sql.enable_nlp(message.chat.id)
                await message.reply_text(
                    "I've enabled NLP moderation in this group. This will help protect you "
                    "from spammers, unsavoury characters, and the biggest trolls."
                )
            elif args[1].lower() in ["off", "no"]:
                sql.disable_nlp(message.chat.id)
                await message.reply_text(
                    "I've disabled NLP moderation in this group. NLP wont affect your users "
                    "anymore. You'll be less protected from any trolls and spammers "
                    "though!"
                )
        else:
            await message.reply_text(
                "Give me some arguments to choose a setting! on/off, yes/no!\n\n"
                "Your current setting is: {}\n"
                "When True, any messsages will go through NLP and spammers will be banned.\n"
                "When False, they won't, leaving you at the possible mercy of spammers\n"
                "NLP powered by @Intellivoid.".format(sql.does_chat_nlp(message.chat.id))
            )
    else:
        await message.reply_text("You aren't an admin.")


@kp.on_message(filters.text & filters.group, group=3)
async def detect_spam(client, message):
    url = "https://api.intellivoid.net/coffeehouse/v1/nlp/spam_prediction/chatroom"
    user = message.from_user
    chat = message.chat
    msg = message.text
    chat_state = sql.does_chat_nlp(chat.id)
    if SPB_MODE and CF_API_KEY and chat_state == True:
        try:
            payload = {'access_key': CF_API_KEY, 'input': msg}
            data = await session.post(url, data=payload)
            res_json = await data.json()
            if res_json['success']:
                spam_check = res_json['results']['spam_prediction']['is_spam']
                if spam_check == True:
                    pred = res_json['results']['spam_prediction']['prediction']
                    await kp.restrict_chat_member(chat.id, user.id, ChatPermissions(can_send_messages=False))
                    try:
                        await message.reply_text(
                        f"**⚠ SPAM DETECTED!**\nSpam Prediction: `{pred}`\nUser: `{user.id}` was muted.",
                        parse_mode="md",
                    )
                    except BadRequest:
                        await message.reply_text(
                        f"**⚠ SPAM DETECTED!**\nSpam Prediction: `{pred}`\nUser: `{user.id}`\nUser could not be restricted due to insufficient admin perms.",
                        parse_mode="md",
                    )

            elif res_json['error']['error_code'] == 21:
                reduced_msg = msg[0:170]
                payload = {'access_key': CF_API_KEY, 'input': reduced_msg}
                data = await session.post(url, data=payload)
                res_json = await data.json()
                spam_check = res_json['results']['spam_prediction']['is_spam']
                if spam_check is True:
                    pred = res_json['results']['spam_prediction']['prediction']
                    await kp.restrict_chat_member(chat.id, user.id, ChatPermissions(can_send_messages=False))
                    try:
                        await message.reply_text(
                            f"**⚠ SPAM DETECTED!**\nSpam Prediction: `{pred}`\nUser: `{user.id}` was muted.", parse_mode="markdown")
                    except BadRequest:
                        await message.reply_text(f"**⚠ SPAM DETECTED!**\nSpam Prediction: `{pred}`\nUser: `{user.id}`\nUser could not be restricted due to insufficient admin perms.", parse_mode="markdown")
        except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
            log.warning("Can't reach SpamProtection API")
            await asyncio.sleep(0.5)
