from nonebot import on_command, require, get_driver
from nonebot.typing import T_State
from nonebot.adapters import Bot, Event
from nonebot.adapters.cqhttp.message import Message
import nonebot.adapters.cqhttp
import _thread

scheduler = require('nonebot_plugin_apscheduler').scheduler

@scheduler.scheduled_job('cron', minute='*')
async def demo():
    driver = get_driver()
    BOT_ID = str(driver.config.bot_id)
    bot = driver.bots[BOT_ID]
    group_id=725194874
    await bot.send_group_msg(group_id=group_id, message="测试消息，每分钟发送一次")
