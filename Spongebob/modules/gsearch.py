import asyncio
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from SaitamaRobot.event import register
from SaitamaRobot import telethn
import sys
import shutil
from re import findall
from telethon import *
from telethon.tl import functions
from telethon.tl import types
from telethon.tl.types import *
import html2text


async def is_register_admin(chat, user):
    if isinstance(chat, (types.InputPeerChannel, types.InputChannel)):

        return isinstance(
            (await telethn(functions.channels.GetParticipantRequest(chat, user))).participant,
            (types.ChannelParticipantAdmin, types.ChannelParticipantCreator)
        )
    elif isinstance(chat, types.InputPeerChat):

        ui = await telethn.get_peer_id(user)
        ps = (await telethn(functions.messages.GetFullChatRequest(chat.chat_id))) \
            .full_chat.participants.participants
        return isinstance(
            next((p for p in ps if p.user_id == ui), None),
            (types.ChatParticipantAdmin, types.ChatParticipantCreator)
        )
    else:
        return None


@register(pattern="^/google (.*)") 
async def _(event):
    if event.fwd_from:
        return
    if event.is_group:
     if not (await is_register_admin(event.input_chat, event.message.sender_id)):
       await event.reply(" Hai.. You are not admin..  You can't use this command.. But you can use in my pm")
       return
    # SHOW_DESCRIPTION = False
    input_str = event.pattern_match.group(1) # + " -inurl:(htm|html|php|pls|txt) intitle:index.of \"last modified\" (mkv|mp4|avi|epub|pdf|mp3)"
    input_url = "https://bots.shrimadhavuk.me/search/?q={}".format(input_str)
    headers = {"USER-AGENT": "UniBorg"}
    response = requests.get(input_url, headers=headers).json()
    output_str = " "
    for result in response["results"]:
        text = result.get("title")
        url = result.get("url")
        description = result.get("description")
        last = html2text.html2text(description)
        output_str += "[{}]({})\n{}\n".format(text, url, last)       
    await event.reply("{}".format(output_str), link_preview=False, parse_mode='Markdown')
