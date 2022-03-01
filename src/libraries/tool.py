import time

import aiohttp


def hash(qq: int):
    days = int(time.strftime("%d", time.localtime(time.time()))) + 31 * int(
        time.strftime("%m", time.localtime(time.time()))) + 77
    return (days * qq) >> 8


async def get_music_by_alias(alias: str):
    async with aiohttp.request("GET", "https://maimai.ohara-rinne.tech/api/alias/query/" + alias) as resp:
        if resp.status != 200:
            return None
        obj = await resp.json()
        return obj["data"]


async def add_alias_request(music_id: str, alias: str):
    payload = {"alias": alias}
    async with aiohttp.request("POST", "https://maimai.ohara-rinne.tech/api/alias/" + music_id, data=payload) as resp:
        if resp.status != 200:
            return None
        obj = await resp.json()
        return obj
