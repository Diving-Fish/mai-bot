from nonebot import on_command, require, get_driver
from nonebot.typing import T_State
from nonebot.adapters import Bot, Event
from nonebot.adapters.cqhttp.message import Message
import nonebot.adapters.cqhttp
import _thread
import nonebot
import requests

scheduler = require('nonebot_plugin_apscheduler').scheduler

on_live_set = set()
on_live_dict = {}

@scheduler.scheduled_job('cron', minute='*')
async def demo():

    mybot, = nonebot.get_bots().values()

    def getRoomInfo(stringID):
        roomInfo = {}
        
        url = f"https://api.live.bilibili.com/room/v1/Room/get_info?id={stringID}&from=room"
        headers = {
            'Accept': 'application/json, text/plain, */*',
            #'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Origin': 'https://live.bilibili.com',
            'Referer': f'https://live.bilibili.com/blanc/{stringID}',
            'X-Requested-With': 'ShockwaveFlash/28.0.0.137',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0',
        }
        data_json = requests.get(url, timeout=10, headers=headers).json()['data']

        roomInfo['room_id'] = str(data_json['room_id'])
        roomInfo['live_status'] = str(data_json['live_status'])
        roomInfo['room_title'] = data_json['title']
        roomInfo['room_description'] = data_json['description']
        roomInfo['room_owner_id'] = data_json['uid']
        
        if roomInfo['live_status'] == '1':
            url = "https://api.live.bilibili.com/live_user/v1/UserInfo/get_anchor_in_room?roomid=%s"%roomInfo['room_id']
            data_json = requests.get(url, timeout=10, headers=headers).json()['data']
            roomInfo['room_owner_name'] = data_json['info']['uname']
        
        return roomInfo

    async def check_info(stringID):
        info = getRoomInfo(stringID)
        if stringID in on_live_set:
            if (info['live_status'] != '1'):
                on_live_set.remove(stringID)
                await mybot.send_group_msg(group_id=725194874, message=f"主播:{on_live_dict[stringID]}   下播了 😭")
                del on_live_dict[stringID]
        else :
            if (info['live_status'] == '1'):
                on_live_set.add(stringID)
                on_live_dict[stringID] = info['room_owner_name']
                await mybot.send_group_msg(group_id=725194874, message=f"主播:{info['room_owner_name']}   标题：{info['room_title']}, 开始直播了，围观地址， https://live.bilibili.com/{stringID}")


    id_zyh = "3216480"
    id_hjh_npy = "26760398"
    id_dys = "7777"
    await check_info(id_zyh)
    await check_info(id_hjh_npy)
    await check_info(id_dys)