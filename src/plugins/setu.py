import random
import re

from collections import defaultdict
from PIL import Image
from nonebot import on_command, on_message, on_notice, require, get_driver, on_regex
from nonebot.typing import T_State
from nonebot.adapters.cqhttp import Message, Event, Bot
from nonebot.adapters.cqhttp import MessageSegment
from nonebot.exception import IgnoredException
from nonebot.message import event_preprocessor
from src.libraries.image import *
from random import randint
import time
from PIL import Image
import requests
from PIL import Image
from io import BytesIO

def setu():
    return 

require_setu = on_regex(r"来张.*色图")

@require_setu.handle()
async def _(bot: Bot, event: Event, state: T_State):
    import requests
    string = str(event.get_message())
    # await require_setu.send('{} {}'.format(string, len(string)))
    print('{} {}'.format(string, len(string)))
    if len(string) > 4:
        tag = string[2:-2]
        setu_api = r"https://api.lolicon.app/setu/v2?tag="+f"{tag}"
    else:
        setu_api = r"https://api.lolicon.app/setu/v2"
    headers = {
        "user-agent": "Mizilla/5.0",
    }
    import requests
    kw = {'wd':'python'}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36"}
    response = requests.get(setu_api, params = kw, headers = headers)
    result = response.json()
    image_url = result['data'][0]['urls']['original']

    await require_setu.send(Message([
        {
            "type": "image",
            "data": {
                "file": f"{image_url}"
            }
        }
    ]))
