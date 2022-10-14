# Code by Killua, Credits: Xyb, Diving_Fish
import asyncio
import os
import math
import numpy as np
from typing import Optional, Dict, List
from io import BytesIO

import requests
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from src.libraries.maimaidx_music import get_cover_len4_id, total_list
from src import static


scoreRank = 'D C B BB BBB A AA AAA S S+ SS SS+ SSS SSS+'.lower().split(' ')
combo = ' FC FC+ AP AP+'.split(' ')
diffs = 'Basic Advanced Expert Master Re:Master'.split(' ')


class ChartInfo(object):
    def __init__(self, idNum: str, diff: int, tp: str, achievement: float, ra: int, comboId: int, scoreId: int,
                 syncId: int, title: str, ds: float, lv: str):
        self.idNum = idNum
        self.diff = diff
        self.tp = tp
        self.achievement = achievement
        self.ra = ra
        self.comboId = comboId
        self.scoreId = scoreId
        self.syncId = syncId
        self.title = title
        self.ds = ds
        self.lv = lv

    def __str__(self):
        return '%-50s' % f'{self.title} [{self.tp}]' + f'{self.ds}\t{diffs[self.diff]}\t{self.ra}'

    def __eq__(self, other):
        return self.ra == other.ra

    def __lt__(self, other):
        return self.ra < other.ra

    @classmethod
    def from_json(cls, data):
        rate = ['d', 'c', 'b', 'bb', 'bbb', 'a', 'aa', 'aaa', 's', 'sp', 'ss', 'ssp', 'sss', 'sssp']
        ri = rate.index(data["rate"])
        fc = ['', 'fc', 'fcp', 'ap', 'app']
        fs = ['', 'fs', 'fsp', 'fsd', 'fsdp']
        fi = fc.index(data["fc"])
        fsi = fs.index(data["fs"])
        return cls(
            idNum=total_list.by_title(data["title"]).id,
            title=data["title"],
            diff=data["level_index"],
            ra=data["ra"],
            ds=data["ds"],
            comboId=fi,
            syncId=fsi,
            scoreId=ri,
            lv=data["level"],
            achievement=data["achievements"],
            tp=data["type"]
        )


class BestList(object):

    def __init__(self, size: int):
        self.data = []
        self.size = size

    def push(self, elem: ChartInfo):
        if len(self.data) >= self.size and elem < self.data[-1]:
            return
        self.data.append(elem)
        self.data.sort()
        self.data.reverse()
        while (len(self.data) > self.size):
            del self.data[-1]

    def pop(self):
        del self.data[-1]

    def __str__(self):
        return '[\n\t' + ', \n\t'.join([str(ci) for ci in self.data]) + '\n]'

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        return self.data[index]


class DrawBest(object):

    def __init__(self, sdBest: BestList, dxBest: BestList, userName: str, playerRating: int, musicRating: int, qqId: int or str = None, b50: bool = False, platenum: int or str = 0):
        self.sdBest = sdBest
        self.dxBest = dxBest
        self.userName = self._stringQ2B(userName)
        self.playerRating = playerRating
        self.musicRating = musicRating
        self.qqId = qqId
        self.b50 = b50
        self.rankRating = self.playerRating - self.musicRating
        self.fail = 0
        if self.b50:
            self.playerRating = 0
            for sd in sdBest:
                self.playerRating += computeRa(sd.ds, sd.achievement, True)
            for dx in dxBest:
                self.playerRating += computeRa(dx.ds, dx.achievement, True)
        self.platenum = platenum
        self.pic_dir = 'src/static/mai/pic/'
        self.cover_dir = 'src/static/mai/cover/'
        if self.b50:
            self.img = Image.open(self.pic_dir + 'b50.png').convert('RGBA')
        else:
            self.img = Image.open(self.pic_dir + 'b40.png').convert('RGBA')
        self.ROWS_IMG = [2]
        if self.b50:
            for i in range(8):
                self.ROWS_IMG.append(140 + 144 * i)
        else:
            for i in range(6):
                self.ROWS_IMG.append(140 + 144 * i)
        self.COLOUMS_IMG = []
        for i in range(6):
            self.COLOUMS_IMG.append(2 + 258 * i)
        for i in range(4):
            self.COLOUMS_IMG.append(2 + 258 * i)
        self.draw()

    def _Q2B(self, uchar):
        """单个字符 全角转半角"""
        inside_code = ord(uchar)
        if inside_code == 0x3000:
            inside_code = 0x0020
        else:
            inside_code -= 0xfee0
        if inside_code < 0x0020 or inside_code > 0x7e:  # 转完之后不是半角字符返回原来的字符
            return uchar
        return chr(inside_code)

    def _stringQ2B(self, ustring):
        """把字符串全角转半角"""
        return "".join([self._Q2B(uchar) for uchar in ustring])

    def _getCharWidth(self, o) -> int:
        widths = [
            (126, 1), (159, 0), (687, 1), (710, 0), (711, 1), (727, 0), (733, 1), (879, 0), (1154, 1), (1161, 0),
            (4347, 1), (4447, 2), (7467, 1), (7521, 0), (8369, 1), (8426, 0), (9000, 1), (9002, 2), (11021, 1),
            (12350, 2), (12351, 1), (12438, 2), (12442, 0), (19893, 2), (19967, 1), (55203, 2), (63743, 1),
            (64106, 2), (65039, 1), (65059, 0), (65131, 2), (65279, 1), (65376, 2), (65500, 1), (65510, 2),
            (120831, 1), (262141, 2), (1114109, 1),
        ]
        if o == 0xe or o == 0xf:
            return 0
        for num, wid in widths:
            if o <= num:
                return wid
        return 1

    def _coloumWidth(self, s: str):
        res = 0
        for ch in s:
            res += self._getCharWidth(ord(ch))
        return res

    def _changeColumnWidth(self, s: str, len: int) -> str:
        res = 0
        sList = []
        for ch in s:
            res += self._getCharWidth(ord(ch))
            if res <= len:
                sList.append(ch)
        return ''.join(sList)

    def _resizePic(self, img: Image.Image, time: float):
        return img.resize((int(img.size[0] * time), int(img.size[1] * time)))

    def diffpic(self, diff: str) -> str:
        pic = ''
        if diff == 0:
            pic = 'BSC'
        elif diff == 1:
            pic = 'ADV'
        elif diff == 2:
            pic = 'EXP'
        elif diff == 3:
            pic = 'MST'
        elif diff == 4:
            pic = 'MST_Re'
        return f'UI_PFC_MS_Info02_{pic}.png' 

    def rank (self)-> str:
        ranker = '初学者'
        if self.rankRating == 250:
            ranker = '实习生'
        elif self.rankRating == 500:
            ranker = '初出茅庐'
        elif self.rankRating == 750:
            ranker = '修行中'
        elif self.rankRating == 1000:
            ranker = '初段'
        elif self.rankRating == 1200:
            ranker = '二段'
        elif self.rankRating == 1400:
            ranker = '三段'
        elif self.rankRating == 1500:
            ranker = '四段'
        elif self.rankRating == 1600:
            ranker = '五段'
        elif self.rankRating == 1700:
            ranker = '六段'
        elif self.rankRating == 1800:
            ranker = '七段'
        elif self.rankRating == 1850:
            ranker = '八段'
        elif self.rankRating == 1900:
            ranker = '九段'
        elif self.rankRating == 1950:
            ranker = '十段'
        elif self.rankRating == 2000:
            ranker = '真传'
        elif self.rankRating == 2010:
            ranker = '真传壹段'
        elif self.rankRating == 2020:
            ranker = '真传贰段'
        elif self.rankRating == 2030:
            ranker = '真传叁段'
        elif self.rankRating == 2040:
            ranker = '真传肆段'
        elif self.rankRating == 2050:
            ranker = '真传伍段'
        elif self.rankRating == 2060:
            ranker = '真传陆段'
        elif self.rankRating == 2070:
            ranker = '真传柒段'
        elif self.rankRating == 2080:
            ranker = '真传捌段'
        elif self.rankRating == 2090:
            ranker = '真传玖段'
        elif self.rankRating == 2100:
            ranker = '真传拾段'
        return ranker

    def _findRaPic(self) -> str:
        num = '10'
        if self.playerRating < 1000:
            num = '01'
        elif self.playerRating < 2000:
            num = '02'
        elif self.playerRating < (3000 if not self.b50 else 4000):
            num = '03'
        elif self.playerRating < (4000 if not self.b50 else 7000):
            num = '04'
        elif self.playerRating < (5000 if not self.b50 else 10000):
            num = '05'
        elif self.playerRating < (6000 if not self.b50 else 12000):
            num = '06'
        elif self.playerRating < (7000 if not self.b50 else 13000):
            num = '07'
        elif self.playerRating < (8000 if not self.b50 else 14500):
            num = '08'
        elif self.playerRating < (8500 if not self.b50 else 15000):
            num = '09'
        return f'UI_CMN_DXRating_S_{num}.png'

    def set_trans(self, img):
        img = img.convert("RGBA")
        x, y = img.size
        for i in range(x):
            for k in range(y):
                color = img.getpixel((i, k))
                color = color[:-1] + (100, )
                img.putpixel((i, k), color)
        return img

    def circle_corner(self, img, radii):  
        circle = Image.new('L', (radii * 2, radii * 2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, radii * 2, radii * 2), fill=255)
        img = img.convert("RGBA")
        w, h = img.size
        alpha = Image.new('L', img.size, 255)
        alpha.paste(circle.crop((0, 0, radii, radii)), (0, 0))
        alpha.paste(circle.crop((radii, 0, radii * 2, radii)), (w - radii, 0))
        alpha.paste(circle.crop((radii, radii, radii * 2, radii * 2)), (w - radii, h - radii))
        alpha.paste(circle.crop((0, radii, radii, radii * 2)), (0, h - radii))
        img.putalpha(alpha)
        return img

    def _drawRating(self, ratingBaseImg: Image.Image):
        COLOUMS_RATING = [74, 92, 110, 129, 147]
        theRa = self.playerRating
        i = 4
        while theRa:
            digit = theRa % 10
            theRa = theRa // 10
            digitImg = Image.open(os.path.join(self.pic_dir, f'UI_NUM_Drating_{digit}.png')).convert('RGBA')
            digitImg = self._resizePic(digitImg, 0.7)
            ratingBaseImg.paste(digitImg, (COLOUMS_RATING[i] - 2, 14), mask=digitImg.split()[3])
            i -= 1
        return ratingBaseImg

    def _drawBestList(self, img: Image.Image, sdBest: BestList, dxBest: BestList):
        itemW = 246
        itemH = 132
        Color = [(69, 193, 36), (255, 186, 1), (255, 90, 102), (134, 49, 200), (217, 197, 233)]
        levelTriagle = [(itemW, 0), (itemW - 12, 0), (itemW, 12)]
        rankPic = 'D C B BB BBB A AA AAA S Sp SS SSp SSS SSSp'.split(' ')
        comboPic = ' FC FCp AP APp'.split(' ')
        syncPic = ' FS FSp FSD FSDp'.split(' ')
        imgDraw = ImageDraw.Draw(img)
        font2 = ImageFont.truetype('src/static/HOS.ttf', 8, encoding='utf-8')
        font3 = ImageFont.truetype('src/static/HOS.ttf', 12, encoding='utf-8')
        titleFontName = 'src/static/adobe_simhei.otf'
        for num in range(0, len(sdBest)):
            i = num // 5
            j = num % 5
            chartInfo = sdBest[num]
            pngPath = os.path.join(self.cover_dir, f'{chartInfo.idNum}.png')
            if not os.path.exists(pngPath):
                pngPath = os.path.join(self.cover_dir, f'{chartInfo.idNum}.jpg')
            if not os.path.exists(pngPath):
                pngPath = os.path.join(self.cover_dir, f'{int(chartInfo.idNum)-10000}.jpg')
            if not os.path.exists(pngPath):
                pngPath = os.path.join(self.cover_dir, f'{int(chartInfo.idNum)-10000}.png')
            if not os.path.exists(pngPath):
                pngPath = os.path.join(self.cover_dir, '1000.png')
            temp = Image.open(pngPath).convert('RGB')
            temp = self._resizePic(temp, itemW / temp.size[0]) 
            temp = temp.crop((0, (temp.size[1] - itemH) / 2, itemW, (temp.size[1] + itemH) / 2))
            temp = temp.filter(ImageFilter.GaussianBlur(3))
            temp = temp.point(lambda p: p * 0.72)
            tempDraw = ImageDraw.Draw(temp)
            diffImg = Image.open(os.path.join(self.pic_dir, self.diffpic(chartInfo.diff))).convert('RGBA')
            diffImg = self._resizePic(diffImg, 0.8)
            temp.paste(diffImg, (6, 4), diffImg.split()[3])
            if chartInfo.tp == 'SD':
                sdImg = Image.open(os.path.join(self.pic_dir, 'UI_UPE_Infoicon_StandardMode.png')).convert('RGBA')
                sdImg = self._resizePic(sdImg, 0.65)
                temp.paste(sdImg, (165, 6), sdImg.split()[3])
            elif chartInfo.tp == 'DX':
                dxImg = Image.open(os.path.join(self.pic_dir, 'UI_UPE_Infoicon_DeluxeMode.png')).convert('RGBA')
                dxImg = self._resizePic(dxImg, 0.65)
                temp.paste(dxImg, (165, 6), dxImg.split()[3])
            font = ImageFont.truetype(titleFontName, 16, encoding='utf-8')
            idfont = ImageFont.truetype('src/static/HOS_Med.ttf', 11, encoding='utf-8')
            trackid = chartInfo.idNum
            if int(chartInfo.idNum) < 10000 and chartInfo.tp == 'DX':
                trackid = str(int(trackid) + 10000)
            if int(trackid) >= 10000:
                tempDraw.text((117, 8), f'D{trackid}', 'white', idfont)
            else:
                tempDraw.text((125, 8), f'S{trackid}', 'white', idfont)
            title = chartInfo.title
            if self._coloumWidth(title) > 14:
                title = self._changeColumnWidth(title, 13) + '...'
            tempDraw.text((8, 30), title, 'white', font)
            font = ImageFont.truetype('src/static/HOS.ttf', 13, encoding='utf-8')
            tempDraw.text((8, 50), f'Achievement Rate', 'white', font)
            font = ImageFont.truetype('src/static/HOS_Med.ttf', 26, encoding='utf-8')
            tempDraw.text((8, 62), f'{"%.4f" % chartInfo.achievement}%', 'white', font)
            if rankPic[chartInfo.scoreId] == 'SSSp':
                rankImg = Image.open(os.path.join(self.pic_dir, f'UI_GAM_Rank_{rankPic[chartInfo.scoreId]}.png')).convert('RGBA')
                rankImg = self._resizePic(rankImg, 0.8)
                temp.paste(rankImg, (163, 43), rankImg.split()[3])
            elif rankPic[chartInfo.scoreId] == 'SSS' or rankPic[chartInfo.scoreId] == 'AAA' or rankPic[chartInfo.scoreId] == 'BBB':
                rankImg = Image.open(os.path.join(self.pic_dir, f'UI_GAM_Rank_{rankPic[chartInfo.scoreId]}.png')).convert('RGBA')
                rankImg = self._resizePic(rankImg, 0.8)
                temp.paste(rankImg, (168, 43), rankImg.split()[3])
            elif rankPic[chartInfo.scoreId] == 'SSp':
                rankImg = Image.open(os.path.join(self.pic_dir, f'UI_GAM_Rank_{rankPic[chartInfo.scoreId]}.png')).convert('RGBA')
                rankImg = self._resizePic(rankImg, 0.8)
                temp.paste(rankImg, (171, 43), rankImg.split()[3])
            elif rankPic[chartInfo.scoreId] == 'SS' or rankPic[chartInfo.scoreId] == 'AA' or rankPic[chartInfo.scoreId] == 'BB':
                rankImg = Image.open(os.path.join(self.pic_dir, f'UI_GAM_Rank_{rankPic[chartInfo.scoreId]}.png')).convert('RGBA')
                rankImg = self._resizePic(rankImg, 0.8)
                temp.paste(rankImg, (175, 43), rankImg.split()[3])
            elif rankPic[chartInfo.scoreId] == 'Sp':
                rankImg = Image.open(os.path.join(self.pic_dir, f'UI_GAM_Rank_{rankPic[chartInfo.scoreId]}.png')).convert('RGBA')
                rankImg = self._resizePic(rankImg, 0.8)
                temp.paste(rankImg, (181, 43), rankImg.split()[3])
            else:
                rankImg = Image.open(os.path.join(self.pic_dir, f'UI_GAM_Rank_{rankPic[chartInfo.scoreId]}.png')).convert('RGBA')
                rankImg = self._resizePic(rankImg, 0.8)
                temp.paste(rankImg, (185, 43), rankImg.split()[3])
            if chartInfo.comboId:
                comboImg = Image.open(os.path.join(self.pic_dir, f'UI_MSS_MBase_Icon_{comboPic[chartInfo.comboId]}_S.png')).convert('RGBA')
                comboImg = self._resizePic(comboImg, 0.6)
                temp.paste(comboImg, (170, 80), comboImg.split()[3])
            else:
                comboImg = Image.open(os.path.join(self.pic_dir, f'UI_MSS_MBase_Icon_Blank.png')).convert('RGBA')
                comboImg = self._resizePic(comboImg, 0.6)
                temp.paste(comboImg, (172, 80), comboImg.split()[3])
            if chartInfo.syncId:
                syncImg = Image.open(os.path.join(self.pic_dir, f'UI_MSS_MBase_Icon_{syncPic[chartInfo.syncId]}_S.png')).convert('RGBA')
                syncImg = self._resizePic(syncImg, 0.6)
                temp.paste(syncImg, (202, 80), syncImg.split()[3])
            else:
                syncImg = Image.open(os.path.join(self.pic_dir, f'UI_MSS_MBase_Icon_Blank.png')).convert('RGBA')
                syncImg = self._resizePic(syncImg, 0.6)
                temp.paste(syncImg, (202, 80), syncImg.split()[3])
            font = ImageFont.truetype('src/static/HOS.ttf', 13, encoding='utf-8')
            tempDraw.text((8, 95), f'Base', 'white', font)
            font = ImageFont.truetype('src/static/HOS_Med.ttf', 16, encoding='utf-8')
            tempDraw.text((8, 108), f'{chartInfo.ds}', 'white', font)
            font = ImageFont.truetype('src/static/HOS_Med.ttf', 16, encoding='utf-8')
            tempDraw.text((51, 102), f'→', 'white', font)
            font = ImageFont.truetype('src/static/HOS_Med.ttf', 25, encoding='utf-8')
            tempDraw.text((74, 95), f'{chartInfo.ra if not self.b50 else computeRa(chartInfo.ds, chartInfo.achievement, True)}', 'white', font)
            if num >= 9:
                font = ImageFont.truetype('src/static/HOS.ttf', 13, encoding='utf-8')
                tempDraw.text((175, 105), f'#{num + 1}/{len(sdBest)}', 'white', font)
            else:
                font = ImageFont.truetype('src/static/HOS.ttf', 13, encoding='utf-8')
                tempDraw.text((179, 105), f'#{num + 1}/{len(sdBest)}', 'white', font)
            temp = self.circle_corner(temp, 15)
            recBase = Image.new('RGBA', (itemW, itemH), 'black')
            recBase = recBase.point(lambda p: p * 0.8)
            recBase = self.set_trans(recBase)
            recBase = self.circle_corner(recBase, 15)
            img.paste(recBase, (self.COLOUMS_IMG[j] + 5, self.ROWS_IMG[i + 1] + 5), mask=recBase.split()[3])
            img.paste(temp, (self.COLOUMS_IMG[j] + 4, self.ROWS_IMG[i + 1] + 4), mask=temp.split()[3])
        for num in range(len(sdBest), sdBest.size):
            i = num // 5
            j = num % 5
            temp = Image.open(os.path.join(self.cover_dir, f'1000.png')).convert('RGB')
            temp = self._resizePic(temp, itemW / temp.size[0])
            temp = temp.crop((0, (temp.size[1] - itemH) / 2, itemW, (temp.size[1] + itemH) / 2))
            temp = temp.filter(ImageFilter.GaussianBlur(1))
            temp = self.circle_corner(temp, 15)
            recBase = Image.new('RGBA', (itemW, itemH), 'black')
            recBase = recBase.point(lambda p: p * 0.8)
            recBase = self.set_trans(recBase)
            recBase = self.circle_corner(recBase, 15)
            img.paste(recBase, (self.COLOUMS_IMG[j] + 5, self.ROWS_IMG[i + 1] + 5), mask=recBase.split()[3])
            img.paste(temp, (self.COLOUMS_IMG[j] + 4, self.ROWS_IMG[i + 1] + 4), mask=temp.split()[3])

        for num in range(0, len(dxBest)):
            i = num // 5 
            j = num % 5
            chartInfo = dxBest[num]
            pngPath = os.path.join(self.cover_dir, f'{int(chartInfo.idNum)}.png')
            if not os.path.exists(pngPath):
                pngPath = os.path.join(self.cover_dir, f'{int(chartInfo.idNum)}.jpg')
            if not os.path.exists(pngPath):
                pngPath = os.path.join(self.cover_dir, f'{int(chartInfo.idNum)-10000}.jpg')
            if not os.path.exists(pngPath):
                pngPath = os.path.join(self.cover_dir, f'{int(chartInfo.idNum)-10000}.png')
                # print("ReGet {}".format(pngPath))
            if not os.path.exists(pngPath):
                pngPath = os.path.join(self.cover_dir, '1000.png')
            temp = Image.open(pngPath).convert('RGB')
            temp = self._resizePic(temp, itemW / temp.size[0])
            temp = temp.crop((0, (temp.size[1] - itemH) / 2, itemW, (temp.size[1] + itemH) / 2))
            temp = temp.filter(ImageFilter.GaussianBlur(3))
            temp = temp.point(lambda p: p * 0.72)

            tempDraw = ImageDraw.Draw(temp)
            diffImg = Image.open(os.path.join(self.pic_dir, self.diffpic(chartInfo.diff))).convert('RGBA')
            diffImg = self._resizePic(diffImg, 0.8)
            temp.paste(diffImg, (6, 4), diffImg.split()[3])
            if chartInfo.tp == 'SD':
                sdImg = Image.open(os.path.join(self.pic_dir, 'UI_UPE_Infoicon_StandardMode.png')).convert('RGBA')
                sdImg = self._resizePic(sdImg, 0.65)
                temp.paste(sdImg, (165, 6), sdImg.split()[3])
            elif chartInfo.tp == 'DX':
                dxImg = Image.open(os.path.join(self.pic_dir, 'UI_UPE_Infoicon_DeluxeMode.png')).convert('RGBA')
                dxImg = self._resizePic(dxImg, 0.65)
                temp.paste(dxImg, (165, 6), dxImg.split()[3])
            font = ImageFont.truetype(titleFontName, 16, encoding='utf-8')
            idfont = ImageFont.truetype('src/static/HOS_Med.ttf', 11, encoding='utf-8')
            trackid = chartInfo.idNum
            if int(chartInfo.idNum) < 10000 and chartInfo.tp == 'DX':
                trackid = str(int(trackid) + 10000)
            if int(trackid) >= 10000:
                tempDraw.text((117, 8), f'D{trackid}', 'white', idfont)
            else:
                tempDraw.text((125, 8), f'S{trackid}', 'white', idfont)
            title = chartInfo.title
            if self._coloumWidth(title) > 14:
                title = self._changeColumnWidth(title, 13) + '...'
            tempDraw.text((8, 30), title, 'white', font)
            font = ImageFont.truetype('src/static/HOS.ttf', 13, encoding='utf-8')
            tempDraw.text((8, 50), f'Achievement Rate', 'white', font)
            font = ImageFont.truetype('src/static/HOS_Med.ttf', 26, encoding='utf-8')
            tempDraw.text((8, 62), f'{"%.4f" % chartInfo.achievement}%', 'white', font)
            if rankPic[chartInfo.scoreId] == 'SSSp':
                rankImg = Image.open(os.path.join(self.pic_dir, f'UI_GAM_Rank_{rankPic[chartInfo.scoreId]}.png')).convert('RGBA')
                rankImg = self._resizePic(rankImg, 0.8)
                temp.paste(rankImg, (163, 43), rankImg.split()[3])
            elif rankPic[chartInfo.scoreId] == 'SSS' or rankPic[chartInfo.scoreId] == 'AAA' or rankPic[chartInfo.scoreId] == 'BBB':
                rankImg = Image.open(os.path.join(self.pic_dir, f'UI_GAM_Rank_{rankPic[chartInfo.scoreId]}.png')).convert('RGBA')
                rankImg = self._resizePic(rankImg, 0.8)
                temp.paste(rankImg, (168, 43), rankImg.split()[3])
            elif rankPic[chartInfo.scoreId] == 'SSp':
                rankImg = Image.open(os.path.join(self.pic_dir, f'UI_GAM_Rank_{rankPic[chartInfo.scoreId]}.png')).convert('RGBA')
                rankImg = self._resizePic(rankImg, 0.8)
                temp.paste(rankImg, (171, 43), rankImg.split()[3])
            elif rankPic[chartInfo.scoreId] == 'SS' or rankPic[chartInfo.scoreId] == 'AA' or rankPic[chartInfo.scoreId] == 'BB':
                rankImg = Image.open(os.path.join(self.pic_dir, f'UI_GAM_Rank_{rankPic[chartInfo.scoreId]}.png')).convert('RGBA')
                rankImg = self._resizePic(rankImg, 0.8)
                temp.paste(rankImg, (175, 43), rankImg.split()[3])
            elif rankPic[chartInfo.scoreId] == 'Sp':
                rankImg = Image.open(os.path.join(self.pic_dir, f'UI_GAM_Rank_{rankPic[chartInfo.scoreId]}.png')).convert('RGBA')
                rankImg = self._resizePic(rankImg, 0.8)
                temp.paste(rankImg, (181, 43), rankImg.split()[3])
            else:
                rankImg = Image.open(os.path.join(self.pic_dir, f'UI_GAM_Rank_{rankPic[chartInfo.scoreId]}.png')).convert('RGBA')
                rankImg = self._resizePic(rankImg, 0.8)
                temp.paste(rankImg, (185, 43), rankImg.split()[3])
            if chartInfo.comboId:
                comboImg = Image.open(os.path.join(self.pic_dir, f'UI_MSS_MBase_Icon_{comboPic[chartInfo.comboId]}_S.png')).convert('RGBA')
                comboImg = self._resizePic(comboImg, 0.6)
                temp.paste(comboImg, (170, 80), comboImg.split()[3])
            else:
                comboImg = Image.open(os.path.join(self.pic_dir, f'UI_MSS_MBase_Icon_Blank.png')).convert('RGBA')
                comboImg = self._resizePic(comboImg, 0.6)
                temp.paste(comboImg, (172, 80), comboImg.split()[3])
            if chartInfo.syncId:
                syncImg = Image.open(os.path.join(self.pic_dir, f'UI_MSS_MBase_Icon_{syncPic[chartInfo.syncId]}_S.png')).convert('RGBA')
                syncImg = self._resizePic(syncImg, 0.6)
                temp.paste(syncImg, (202, 80), syncImg.split()[3])
            else:
                syncImg = Image.open(os.path.join(self.pic_dir, f'UI_MSS_MBase_Icon_Blank.png')).convert('RGBA')
                syncImg = self._resizePic(syncImg, 0.6)
                temp.paste(syncImg, (202, 80), syncImg.split()[3])
            font = ImageFont.truetype('src/static/HOS.ttf', 13, encoding='utf-8')
            tempDraw.text((8, 95), f'Base', 'white', font)
            font = ImageFont.truetype('src/static/HOS_Med.ttf', 16, encoding='utf-8')
            tempDraw.text((8, 108), f'{chartInfo.ds}', 'white', font)
            font = ImageFont.truetype('src/static/HOS_Med.ttf', 16, encoding='utf-8')
            tempDraw.text((51, 102), f'→', 'white', font)
            font = ImageFont.truetype('src/static/HOS_Med.ttf', 25, encoding='utf-8')
            tempDraw.text((74, 95), f'{chartInfo.ra if not self.b50 else computeRa(chartInfo.ds, chartInfo.achievement, True)}', 'white', font)
            if num >= 9:
                font = ImageFont.truetype('src/static/HOS.ttf', 13, encoding='utf-8')
                tempDraw.text((175, 105), f'#{num + 1}/{len(dxBest)}', 'white', font)
            else:
                font = ImageFont.truetype('src/static/HOS.ttf', 13, encoding='utf-8')
                tempDraw.text((179, 105), f'#{num + 1}/{len(dxBest)}', 'white', font)
            temp = self.circle_corner(temp, 15)
            recBase = Image.new('RGBA', (itemW, itemH), 'black')
            recBase = recBase.point(lambda p: p * 0.8)
            recBase = self.set_trans(recBase)
            recBase = self.circle_corner(recBase, 15)
            if self.b50:
                img.paste(recBase, (self.COLOUMS_IMG[j] + 5, self.ROWS_IMG[i + 1] + 1082), mask=recBase.split()[3])
                img.paste(temp, (self.COLOUMS_IMG[j] + 4, self.ROWS_IMG[i + 1] + 1081), mask=temp.split()[3])
            else:
                img.paste(recBase, (self.COLOUMS_IMG[j] + 5, self.ROWS_IMG[i + 1] + 782), mask=recBase.split()[3])
                img.paste(temp, (self.COLOUMS_IMG[j] + 4, self.ROWS_IMG[i + 1] + 781), mask=temp.split()[3])
        for num in range(len(dxBest), dxBest.size):
            i = num // 5
            j = num % 5
            temp = Image.open(os.path.join(self.cover_dir, f'1000.png')).convert('RGB')
            temp = self._resizePic(temp, itemW / temp.size[0])
            temp = temp.crop((0, (temp.size[1] - itemH) / 2, itemW, (temp.size[1] + itemH) / 2))
            temp = temp.filter(ImageFilter.GaussianBlur(1))
            temp = self.circle_corner(temp, 15)
            recBase = Image.new('RGBA', (itemW, itemH), 'black')
            recBase = recBase.point(lambda p: p * 0.8)
            recBase = self.set_trans(recBase)
            recBase = self.circle_corner(recBase, 15)
            if self.b50:
                img.paste(recBase, (self.COLOUMS_IMG[j] + 5, self.ROWS_IMG[i + 1] + 1082), mask=recBase.split()[3])
                img.paste(temp, (self.COLOUMS_IMG[j] + 4, self.ROWS_IMG[i + 1] + 1081), mask=temp.split()[3])
            else:
                img.paste(recBase, (self.COLOUMS_IMG[j] + 5, self.ROWS_IMG[i + 1] + 782), mask=recBase.split()[3])
                img.paste(temp, (self.COLOUMS_IMG[j] + 4, self.ROWS_IMG[i + 1] + 781), mask=temp.split()[3])

    @staticmethod
    def _drawRoundRec(im, color, x, y, w, h, r):
        drawObject = ImageDraw.Draw(im)
        drawObject.ellipse((x, y, x + r, y + r), fill=color)
        drawObject.ellipse((x + w - r, y, x + w, y + r), fill=color)
        drawObject.ellipse((x, y + h - r, x + r, y + h), fill=color)
        drawObject.ellipse((x + w - r, y + h - r, x + w, y + h), fill=color)
        drawObject.rectangle((x + r / 2, y, x + w - (r / 2), y + h), fill=color)
        drawObject.rectangle((x, y + r / 2, x + w, y + h - (r / 2)), fill=color)

    def draw(self):
        topImg = Image.open(os.path.join(self.pic_dir, 'top.png')).convert('RGBA')
        self.img.paste(topImg, (0, 0), mask=topImg.split()[3])
        underImg = Image.open(os.path.join(self.pic_dir, 'under.png')).convert('RGBA')
        self.img.paste(underImg, (0, 810 if not self.b50 else 1110), mask=underImg.split()[3])
        groundImg = Image.open(os.path.join(self.pic_dir, 'ground.png')).convert('RGBA')
        self.img.paste(groundImg, (0, 0), mask=groundImg.split()[3])
        self.img.paste(groundImg, (0, 622), mask=groundImg.split()[3])
        self.img.paste(groundImg, (0, 1244), mask=groundImg.split()[3])
        leftImg = Image.open(os.path.join(self.pic_dir, 'left.png')).convert('RGBA')
        self.img.paste(leftImg, (0, 0), mask=leftImg.split()[3])
        rightImg = Image.open(os.path.join(self.pic_dir, 'right.png')).convert('RGBA')
        self.img.paste(rightImg, (738, 780 if not self.b50 else 1080), mask=rightImg.split()[3])

        if self.qqId:
            if self.platenum == 0:
                plateImg = Image.open(os.path.join(self.pic_dir, 'none.png')).convert('RGBA')
            else:
                plateImg = Image.open(os.path.join(self.pic_dir, f'plate_{self.platenum}.png')).convert('RGBA')
            plateImg = self._resizePic(plateImg, 2)
            self.img.paste(plateImg, (9, 8), mask=plateImg.split()[3])
            resp = requests.get(f'http://q1.qlogo.cn/g?b=qq&nk={self.qqId}&s=100')
            qqLogo = Image.open(BytesIO(resp.content))
            borderImg1 = Image.fromarray(np.zeros((200, 200, 4), dtype=np.uint8)).convert('RGBA')
            borderImg2 = Image.fromarray(np.zeros((200, 200, 4), dtype=np.uint8)).convert('RGBA')
            self._drawRoundRec(borderImg1, (255, 0, 80), 0, 0, 200, 200, 40)
            self._drawRoundRec(borderImg2, (255, 255, 255), 3, 3, 193, 193, 30)
            borderImg1.paste(borderImg2, (0, 0), mask=borderImg2.split()[3])
            borderImg = borderImg1.resize((108, 108))
            borderImg.paste(qqLogo, (4, 4))
            borderImg = self._resizePic(borderImg, 0.995)
            self.img.paste(borderImg, (17, 17), mask=borderImg.split()[3])
        else:
            splashLogo = Image.open(os.path.join(self.pic_dir, 'UI_CMN_TabTitle_MaimaiTitle_Ver214.png')).convert('RGBA')
            splashLogo = self._resizePic(splashLogo, 0.65)
            self.img.paste(splashLogo, (10, 35), mask=splashLogo.split()[3])

        ratingBaseImg = Image.open(os.path.join(self.pic_dir, self._findRaPic())).convert('RGBA')
        ratingBaseImg = self._drawRating(ratingBaseImg)
        ratingBaseImg = self._resizePic(ratingBaseImg, 0.8)
        self.img.paste(ratingBaseImg, (240 if not self.qqId else 139, 10), mask=ratingBaseImg.split()[3])

        namePlateImg = Image.open(os.path.join(self.pic_dir, 'UI_TST_PlateMask.png')).convert('RGBA')

        def round_corner(radius, fill):
            """Draw a round corner"""
            corner = Image.new('RGBA', (radius, radius), (0, 0, 0, 0))
            draw = ImageDraw.Draw(corner)
            draw.pieslice((0, 0, radius * 2, radius * 2), 180, 270, fill=fill)
            return corner
        
        def round_rectangle(size, radius, fill):
            """Draw a rounded rectangle"""
            width, height = size
            rectangle = Image.new('RGBA', size, fill)
            corner = round_corner(radius, fill)
            rectangle.paste(corner, (0, 0))
            rectangle.paste(corner.rotate(90), (0, height - radius)) # Rotate the corner and paste it
            rectangle.paste(corner.rotate(180), (width - radius, height - radius))
            rectangle.paste(corner.rotate(270), (width - radius, 0))
            return rectangle
        
        namePlateImg = round_rectangle((285, 40), 10, "white")
        namePlateDraw = ImageDraw.Draw(namePlateImg)
        font1 = ImageFont.truetype('src/static/HOS.ttf', 28, encoding='unic')
        namePlateDraw.text((12, 3), ' '.join(list(self.userName)), 'black', font1)
        nameDxImg = Image.open(os.path.join(self.pic_dir, 'UI_CMN_Name_DX.png')).convert('RGBA')
        nameDxImg = self._resizePic(nameDxImg, 0.9)
        namePlateImg.paste(nameDxImg, (230, 4), mask=nameDxImg.split()[3])
        self.img.paste(namePlateImg, (240 if not self.qqId else 139, 52), mask=namePlateImg.split()[3])

        shougouImg = Image.open(os.path.join(self.pic_dir, 'UI_CMN_Shougou_Rainbow.png')).convert('RGBA')
        shougouDraw = ImageDraw.Draw(shougouImg)
        font2 = ImageFont.truetype('src/static/HOS.ttf', 14, encoding='utf-8')
        font2s = ImageFont.truetype('src/static/HOS.ttf', 13, encoding='utf-8')
        font3 = ImageFont.truetype('src/static/HOS_Med.ttf', 13, encoding='utf-8')
        playCountInfo = f'Rank: {self.rankRating} | Rating: {self.musicRating}' if not self.b50 else f'Best 50 Rating'
        shougouImgW, shougouImgH = shougouImg.size
        playCountInfoW, playCountInfoH = shougouDraw.textsize(playCountInfo, font2)
        textPos = ((shougouImgW - playCountInfoW - font2.getoffset(playCountInfo)[0]) / 2, 5)
        shougouDraw.text(textPos, playCountInfo, (104, 186, 255), font2)
        shougouImg = self._resizePic(shougouImg, 1.05)
        self.img.paste(shougouImg, (240 if not self.qqId else 139, 95), mask=shougouImg.split()[3])
        
        splashImg = Image.open(os.path.join(self.pic_dir, 'Splash.png')).convert('RGBA')
        splashImg = self._resizePic(splashImg, 0.2)
        self.img.paste(splashImg, (685, 2), mask=splashImg.split()[3])

        self._drawBestList(self.img, self.sdBest, self.dxBest)
        total_sd = 0
        total_dx = 0
        for i in range(len(self.sdBest)):
            total_sd += self.sdBest[i].ra if not self.b50 else computeRa(self.sdBest[i].ds, self.sdBest[i].achievement, True)
        for i in range(len(self.dxBest)):
            total_dx += self.dxBest[i].ra if not self.b50 else computeRa(self.dxBest[i].ds, self.dxBest[i].achievement, True)
        authorBoardImg = Image.open(os.path.join(self.pic_dir, 'UI_CMN_MiniDialog_01.png')).convert('RGBA')
        authorBoardImg = self._resizePic(authorBoardImg, 0.45)
        authorBoardDraw = ImageDraw.Draw(authorBoardImg)
        mode = "B25" if not self.b50 else "B35"
        authorBoardDraw.text((19, 21), f' {mode}: {total_sd}     B15: {total_dx}\n Rank Level: {self.rank()}\n  --------------------------------\n Credits: Xyb & Diving-Fish\n Designer: Killua', 'black', font2s)
        self.img.paste(authorBoardImg, (1070, 10), mask=authorBoardImg.split()[3])
        dxImg = Image.open(os.path.join(self.pic_dir, 'UI_RSL_MBase_Parts_01.png')).convert('RGBA')
        dxImg = self._resizePic(dxImg, 0.5)
        self.img.paste(dxImg, (8, 1187 if self.b50 else 890), mask=dxImg.split()[3])

        # self.img.show()

    def getDir(self):
        return self.img


def computeRa(ds: float, achievement: float, spp: bool = False) -> int:
    baseRa = 22.4 if spp else 14.0
    if achievement < 50:
        baseRa = 0.0 if spp else 0.0
    elif achievement < 60:
        baseRa = 8.0 if spp else 5.0
    elif achievement < 70:
        baseRa = 9.6 if spp else 6.0
    elif achievement < 75:
        baseRa = 11.2 if spp else 7.0
    elif achievement < 80:
        baseRa = 12.0 if spp else 7.5
    elif achievement < 90:
        baseRa = 13.6 if spp else 8.5
    elif achievement < 94:
        baseRa = 15.2 if spp else 9.5
    elif achievement < 97:
        baseRa = 16.8 if spp else 10.5
    elif achievement < 98:
        baseRa = 20.0 if spp else 12.5
    elif achievement < 99:
        baseRa = 20.0 if spp else 12.7
    elif achievement < 99.5:
        baseRa = 20.8 if spp else 13.0
    elif achievement < 100:
        baseRa = 21.1 if spp else 13.2
    elif achievement < 100.5:
        baseRa = 21.6 if spp else 13.5

    return math.floor(ds * (min(100.5, achievement) / 100) * baseRa)


async def get_player_data(payload: Dict):
    async with aiohttp.request("POST", "https://www.diving-fish.com/api/maimaidxprober/query/player", json=payload) as resp:
        if resp.status == 400:
            return None, 400
        elif resp.status == 403:
            return None, 403
        player_data = await resp.json()
        return player_data, 0


async def generate(payload: Dict, platenum: int or str) -> (Optional[Image.Image], bool):
    obj, success = await get_player_data(payload)
    if success != 0: return None, success
    qqId = None
    b50 = False
    if 'qq' in payload:
        qqId = payload['qq']
    if 'b50' in payload:
        b50 = True
        sd_best = BestList(35)
    else:
        sd_best = BestList(25)
    dx_best = BestList(15)

    dx: List[Dict] = obj["charts"]["dx"]
    sd: List[Dict] = obj["charts"]["sd"]
    for c in sd:
        sd_best.push(ChartInfo.from_json(c))
        # print(ChartInfo.from_json(c).idNum)
    for c in dx:
        dx_best.push(ChartInfo.from_json(c))
        # print(ChartInfo.from_json(c).idNum)
    pic = DrawBest(sd_best, dx_best, obj["nickname"], obj["rating"] + obj["additional_rating"], obj["rating"], qqId, b50, platenum).getDir()
    return pic, 0
