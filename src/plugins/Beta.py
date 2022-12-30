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
from src.libraries.maimaidx_music import total_list
from src.libraries.image import *
from random import randint
import time
import csv

maimai_spot_person_number = {}


person_record = on_regex("[七西良悦奥]([0-9]+)")

@person_record.handle()
async def _(bot: Bot, event: Event, state: T_State):
    regex = "([七西良悦奥])([0-9]+)"
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


person_query = on_regex("[七西良悦奥]几")

@person_query.handle()
async def _(bot: Bot, event: Event, state: T_State):
    regex = "([七西良悦奥])几"
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


from PIL import Image, ImageDraw, ImageFont, ImageFilter
import aiohttp
from io import BytesIO
from typing import Optional, Dict, List
import numpy as np
import math
import os
import asyncio
import requests
from copy import deepcopy
from typing import Dict, List, Optional, Union, Tuple, Any
import random
import json

class DrawQuery(object):
    def __init__(
        self,
        result_set,
        cover_dir='src/static/mai/cover/',
        font_dir='src/static/'
    ):
        self.height_title = 50
        self.width_lv = 80
        self.height_calc = self.height_title
        self.height_per_line = 60
        self.songs_per_line = 8
        self.width_per_songs = 80
        self.width_kernel_songs = 70
        self.width_songs_bargin = 10
        self.height_per_set = self.width_per_songs
        self.height_per_line = self.width_per_songs + self.width_songs_bargin
        self.start = result_set[0][0][2]
        self.end = result_set[-1][0][2]
        self.result_set = deepcopy(result_set)
        self.width_calc = self.width_lv+(self.width_per_songs+self.width_songs_bargin)*self.songs_per_line
        for fuck_set in result_set:
            self.height_calc += (len(fuck_set) + self.songs_per_line -
                            1)//self.songs_per_line * self.height_per_line + self.height_per_set
        self.img = Image.new(mode='RGB', size=(
            self.width_calc , self.height_calc), color=(255, 255, 255))
        # print(f'Pic Size = {self.width_lv+(self.width_per_songs+self.width_songs_bargin)*self.songs_per_line, self.height_calc}')
        self.cover_dir = cover_dir
        self.font_dir = font_dir
        self.draw()
        self.img = self._resizePic(self.img, 1.0)

    def _resizePic(self, img: Image.Image, time: float):
        return img.resize((int(img.size[0] * time), int(img.size[1] * time)))

    def _get_cover_image(self, idNum):
        
        pngPath = os.path.join(self.cover_dir, f'{idNum}.png')
        # print(pngPath)
        if not os.path.exists(pngPath):
            pngPath = os.path.join(
                self.cover_dir, f'{idNum}.jpg')
        if not os.path.exists(pngPath):
            pngPath = os.path.join(
                self.cover_dir, f'{idNum.rjust(4, "0")}.jpg')
        if not os.path.exists(pngPath):
            pngPath = os.path.join(
                self.cover_dir, f'{idNum.rjust(4, "0")}.png')
        if not os.path.exists(pngPath):
            pngPath = os.path.join(
                self.cover_dir, f'{int(idNum)-10000}.jpg')
        if not os.path.exists(pngPath):
            pngPath = os.path.join(
                self.cover_dir, f'{int(idNum)-10000}.png')
        if not os.path.exists(pngPath):
            pngPath = os.path.join(
                self.cover_dir, f'{str(int(idNum)-10000).rjust(4, "0")}.png')
        if not os.path.exists(pngPath):
            pngPath = os.path.join(
                self.cover_dir, f'{str(int(idNum)-10000).rjust(4, "0")}.jpg')
        if not os.path.exists(pngPath):
            pngPath = os.path.join(self.cover_dir, '1000.png')
            
        temp = Image.open(pngPath).convert('RGB')
        return temp
        pass

    def draw(self):

        font1 = ImageFont.truetype(
            os.path.join(self.font_dir, 'HOS.ttf'), 28, encoding='unic')
        font1_small = ImageFont.truetype(
            os.path.join(self.font_dir, 'HOS.ttf'), 25, encoding='unic')
        titlePlateDraw = ImageDraw.Draw(self.img)
        titlePlateDraw.text(
            ((self.width_calc - 200) // 2, 40), f'定数表 {self.start} - {self.end}', 'black', font1)


        Color = [(69, 193, 36), (255, 186, 1), (255, 90, 102),
                 (134, 49, 200), (217, 197, 233)]

        diff_label = ['Bas', 'Adv', 'Exp', 'Mst', 'ReM']

        nowHeight = self.height_title

        lineCounter = 0
        for fuck_set in self.result_set:
            
            nowHeight += self.height_per_set
            titlePlateDraw.text(
                (15, 18+nowHeight), f'{fuck_set[0][2]}', 'black', font1_small)

            lineCounter = 0
            for item in fuck_set:
                if lineCounter == self.songs_per_line:
                    lineCounter=0
                    nowHeight += self.height_per_line
                # print(f'Item : {item[0]}')
                tempImg = self._get_cover_image(item[0])
                tempImg = self._resizePic(tempImg, self.width_kernel_songs / tempImg.size[0])
                tempBack = Image.new(mode='RGB', size=(self.width_per_songs, self.width_per_songs), color=Color[diff_label.index(item[3])])
                # print(f'{item[3]} - {diff_label.index(item[3])} - {Color[diff_label.index(item[3])]}')
                tempBack.paste(
                    tempImg, ((self.width_per_songs - self.width_kernel_songs) // 2, (self.width_per_songs - self.width_kernel_songs) // 2)
                )
                self.img.paste(
                tempBack, ((lineCounter) * (self.width_per_songs+self.width_songs_bargin)+self.width_lv, nowHeight))
                # print(f"Past Position {nowHeight, (lineCounter) * (self.width_per_songs+self.width_songs_bargin)+self.width_lv}")
                lineCounter+=1
                pass
            nowHeight+=self.height_per_set
        # "{elem[0]}. {elem[1]} {elem[3]} {elem[4]}({elem[2]})\n"
        # ID Name Exp/Mas/Adv 10+ 10.9

        return


    def getDir(self):
        return self.img


async def level_picture_test(ds1=8.0, ds2=14.6):

    def cross(checker: List[Any], elem: Optional[Union[Any, List[Any]]], diff):
        ret = False
        diff_ret = []
        if not elem or elem is Ellipsis:
            return True, diff
        if isinstance(elem, List):
            for _j in (range(len(checker)) if diff is Ellipsis else diff):
                if _j >= len(checker):
                    continue
                __e = checker[_j]
                if __e in elem:
                    diff_ret.append(_j)
                    ret = True
        elif isinstance(elem, Tuple):
            for _j in (range(len(checker)) if diff is Ellipsis else diff):
                if _j >= len(checker):
                    continue
                __e = checker[_j]
                if elem[0] <= __e <= elem[1]:
                    diff_ret.append(_j)
                    ret = True
        else:
            for _j in (range(len(checker)) if diff is Ellipsis else diff):
                if _j >= len(checker):
                    continue
                __e = checker[_j]
                if elem == __e:
                    return True, [_j]
        return ret, diff_ret

    def in_or_equal(checker: Any, elem: Optional[Union[Any, List[Any]]]):
        if elem is Ellipsis:
            return True
        if isinstance(elem, List):
            return checker in elem
        elif isinstance(elem, Tuple):
            return elem[0] <= checker <= elem[1]
        else:
            return checker == elem

    class Chart(Dict):
        tap: Optional[int] = None
        slide: Optional[int] = None
        hold: Optional[int] = None
        touch: Optional[int] = None
        brk: Optional[int] = None
        charter: Optional[int] = None

        def __getattribute__(self, item):
            if item == 'tap':
                return self['notes'][0]
            elif item == 'hold':
                return self['notes'][1]
            elif item == 'slide':
                return self['notes'][2]
            elif item == 'touch':
                return self['notes'][3] if len(self['notes']) == 5 else 0
            elif item == 'brk':
                return self['notes'][-1]
            elif item == 'charter':
                return self['charter']
            return super().__getattribute__(item)

    class Music(Dict):
        id: Optional[str] = None
        title: Optional[str] = None
        ds: Optional[List[float]] = None
        level: Optional[List[str]] = None
        genre: Optional[str] = None
        type: Optional[str] = None
        bpm: Optional[float] = None
        version: Optional[str] = None
        charts: Optional[Chart] = None
        release_date: Optional[str] = None
        artist: Optional[str] = None

        diff: List[int] = []

        def __getattribute__(self, item):
            if item in {'genre', 'artist', 'release_date', 'bpm', 'version'}:
                if item == 'version':
                    return self['basic_info']['from']
                return self['basic_info'][item]
            elif item in self:
                return self[item]
            return super().__getattribute__(item)

    class MusicList(List[Music]):
        def by_id(self, music_id: str) -> Optional[Music]:
            for music in self:
                if music.id == music_id:
                    return music
            return None

        def by_title(self, music_title: str) -> Optional[Music]:
            for music in self:
                if music.title == music_title:
                    return music
            return None

        def random(self):
            return random.choice(self)

        def filter(self,
                   *,
                   level: Optional[Union[str, List[str]]] = ...,
                   ds: Optional[Union[float, List[float],
                                      Tuple[float, float]]] = ...,
                   title_search: Optional[str] = ...,
                   charter_search: Optional[str] = ...,
                   composer_search: Optional[str] = ...,
                   genre: Optional[Union[str, List[str]]] = ...,
                   bpm: Optional[Union[float, List[float],
                                       Tuple[float, float]]] = ...,
                   type: Optional[Union[str, List[str]]] = ...,
                   diff: List[int] = ...,
                   ):
            new_list = MusicList()
            chart_list = []
            for music in self:
                diff2 = diff
                music = deepcopy(music)
                ret, diff2 = cross(music.level, level, diff2)
                if not ret:
                    continue
                ret, diff2 = cross(music.ds, ds, diff2)
                if not ret:
                    continue
                if not in_or_equal(music.genre, genre):
                    continue
                if not in_or_equal(music.type, type):
                    continue
                if not in_or_equal(music.bpm, bpm):
                    continue
                if title_search is not Ellipsis and title_search.lower() not in music.title.lower():
                    continue
                # if charter_search is not Ellipsis and charter_search.lower() not in music.charts.charter.lower():
                #    continue
                if composer_search is not Ellipsis and composer_search.lower() not in music.artist.lower():
                    continue
                if charter_search is not Ellipsis:
                    for chart_id in range(len(music.charts)):
                        if charter_search.lower() not in music.charts[chart_id].charter.lower():
                            continue
                        tmp = [music, chart_id]
                        chart_list.append(tmp)
                        # print(music.title)
                else:
                    music.diff = diff2
                    new_list.append(music)
            if charter_search is not Ellipsis:
                return chart_list
            return new_list

    result_set = []
    diff_label = ['Bas', 'Adv', 'Exp', 'Mst', 'ReM']

    start = int(ds1 * 10 + 0.1)
    end = int(ds2 * 10 + 0.1)
    if end - start > 10:
        end = start + 10
    for i in range(start, end+1):
        query_value = i/10
        music_data = total_list.filter(ds=query_value)
        fuck_set = []
        for music in sorted(music_data, key=lambda i: int(i['id'])):
            for i in music.diff:
                fuck_set.append(
                    (music['id'], music['title'], music['ds'][i], diff_label[i], music['level'][i]))
        if len(fuck_set) != 0:
            result_set.append(fuck_set)

    s = ""
    for fuck_set in result_set:
        for elem in fuck_set:
            s += f"{elem[0]}. {elem[1]} {elem[3]} {elem[4]}({elem[2]})\n"
        s += f"-------\n"
    # print(s)
    # ID Name Exp/Mas/Adv 10+ 10.9

    query_result = DrawQuery(result_set)
    return query_result.getDir()


level_table = on_command('level_table ', aliases={'定数表 '})
@level_table.handle()
async def _(bot: Bot, event: Event, state: T_State):
    argv = str(event.get_message()).strip().split(" ")
    if len(argv) > 2 or len(argv) == 0:
        await level_table.finish("命令格式为\n定数表 <定数>\n定数表 <定数下限> <定数上限>")
        return
    result_pic = None
    if len(argv) == 1:
        result_pic = await level_picture_test(float(argv[0]), float(argv[0]))
    else:
        result_pic = await level_picture_test(float(argv[0]), float(argv[1]))

    if result_pic is not None:

        await level_table.finish(Message([
            {
                "type": "image",
                "data": {
                    "file": f"base64://{str(image_to_base64(result_pic), encoding='utf-8')}"
                }
            }
        ]))
    else:
        
        await level_table.finish("寄了喵")