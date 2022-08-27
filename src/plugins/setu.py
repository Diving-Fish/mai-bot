import random
import re

from typing import Optional, Dict, List
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
import aiohttp
from nonebot.adapters.cqhttp import MessageSegment

import requests as req
from PIL import Image
from io import BytesIO

# comments to let it go
comments to let module works

def setu():
    return 


async def setu_generate(payload : Dict) -> (Optional[Image.Image], list, int):
    try:
        async with aiohttp.request("POST", "https://api.lolicon.app/setu/v2", json=payload) as resp:
            if resp.status == 400:
                return None, None, 400
            if resp.status == 403:
                return None, None, 403
            obj = await resp.json()
            # print(obj)
            if 'data' not in obj or 'urls' not in obj['data'][0] or 'original' not in obj['data'][0]['urls']:
                return None, None, None
            else:
                pic_url = obj['data'][0]['urls']['original']
                resp = req.get(pic_url)
                image = Image.open(BytesIO(resp.content))
                Image_copy = Image.Image.copy(image)
                image.close()
                Image_copy = Image_copy.convert("RGBA")
                if 'tags' not in obj['data'][0]:
                    return Image_copy, None, 0
                else:
                    return Image_copy, obj['data'][0]['tags'], 0
            return None, None, None
    except Exception as e:
        return None, None, None


require_setu = on_regex(r"来张.*色图")

@require_setu.handle()
async def _(bot: Bot, event: Event, state: T_State):
    string = str(event.get_message())
    if len(string) > 4:
        tag = string[2:-2]
        payload = {'tag' : tag}
    else:
        payload = {}
    img, tags, flag = await setu_generate(payload)
    print(img, flag)
    if flag != 0:
        # await require_setu.finish('寄！')
        await require_setu.finish(Message([
            MessageSegment.reply(event.message_id), {
                "type": "text",
                "data": {
                    "text": f"没有这样的色图喵"
                }
        }]))
    else:
        # await require_setu.send(Message([
        #     MessageSegment.reply(event.message_id), {
        #         "type": "image",
        #         "data": {
        #             "file": f"base64://{str(image_to_base64(img), encoding='utf-8')}"
        #         }
        #     }
        # ]))        
        
        await require_setu.finish(Message([
            MessageSegment.reply(event.message_id),
            {
                "type": "image",
                "data": {
                    "file": f"base64://{str(image_to_base64(img), encoding='utf-8')}"
                }
            }
        ]))        

        # await require_setu.send(Message([
        #     MessageSegment.reply(event.message_id), {
        #         "type": "image",
        #         "data": {
        #             "file": f"base64://{str(image_to_base64(img), encoding='utf-8')}"
        #         }
        #     }
        # ]))        