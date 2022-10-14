import random
import re

from collections import defaultdict
from PIL import Image
from nonebot import on_command, on_message, on_notice, require, get_driver, on_regex
from re import escape
from nonebot.typing import T_State
from nonebot.adapters.cqhttp import Message, Event, Bot
from nonebot.adapters.cqhttp import MessageSegment
from nonebot.exception import IgnoredException
from nonebot.message import event_preprocessor
from src.libraries.image import *
from random import randint
import time
import csv

maimai_spot_person_number = {}


person_record = on_regex("[西良悦奥]([0-9]+)")

@person_record.handle()
async def _(bot: Bot, event: Event, state: T_State):
    regex = "([西良悦奥])([0-9]+)"
    groups = re.match(regex, str(event.get_message())).groups()
    if len(groups[1]) < 3:
        tempTime = time.localtime(time.time())
        date_d = int(time.strftime("%d", tempTime))
        date_m = int(time.strftime("%m", tempTime))
        date_y = int(time.strftime("%Y", tempTime))
        date_hour = int(time.strftime("%H", tempTime))
        date_min = int(time.strftime("%M", tempTime))
        person_name = event.sender.card

        maimai_spot_person_number[groups[0]] = (
            date_y,
            date_m,
            date_d,
            date_hour,
            date_min,
            person_name,
            groups[1]
        )
        
    await person_record.finish(Message([
        {
            "type": "poke",
            "data": {
                "qq": f"{event.sender.user_id}"
            }
        }
    ]))


person_query = on_regex("[西良悦奥]几")

@person_query.handle()
async def _(bot: Bot, event: Event, state: T_State):
    regex = "([西良悦奥])几"
    groups = re.match(regex, str(event.get_message())).groups()
    
    tempString = ""

    tempTime = time.localtime(time.time())
    date_d = int(time.strftime("%d", tempTime))
    date_m = int(time.strftime("%m", tempTime))
    date_y = int(time.strftime("%Y", tempTime))

    if groups[0] in maimai_spot_person_number.keys():
        query_answer = maimai_spot_person_number[groups[0]]
        if (query_answer[0] != date_y) or (query_answer[1] != date_m) or (query_answer[2] != date_d) :
            tempString =  "今天还没有人报告过喵"
        else:
            tempString =  f"{query_answer[0]}/{query_answer[1]}/{query_answer[2]}, {query_answer[3]}:{query_answer[4]}  {query_answer[5]}  :  {query_answer[6]}"
    else:
        tempString =  "今天还没有人报告过喵"

    await person_query.finish(Message([
        {
            "type": "text",
            "data": {
                "text": tempString
            }
        }
    ]))


