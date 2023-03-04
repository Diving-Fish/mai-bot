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
import openai
from PIL import Image
from io import BytesIO

# comments to let it go
# comments to let module works
openai.api_key = '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'

require_chat = on_command('c')

context = {}

@require_chat.handle()
async def _(bot: Bot, event: Event, state: T_State):
    group_id = event.get_session_id()
    print(group_id)
    if group_id not in context:
        context[group_id] = []
    input = str(event.get_message()).strip()
    # print(f'Input {input}')
    while(len(context[group_id]) > 10):
        context[group_id].pop(0)
    context[group_id].append({"role":"user", "content":input})
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", 
        messages=context[group_id]
    )
    answer = str(completion['choices'][0]['message']['content']).strip()
    context[group_id].append({"role":"assistant", "content":answer})
    answer = re.sub(r"(.{30})", "\\1\n", answer)
    await require_chat.finish(Message([
        {
            "type": "image",
            "data": {
                "file": f"base64://{str(image_to_base64(text_to_image(answer)), encoding='utf-8')}"
            }
        }
    ]))
        