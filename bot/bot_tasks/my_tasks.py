import logging
import re
import aiohttp
from khl import Bot, Message, MessageTypes
from bot.bot_apis import map_img
from bot.bot_utils.utils_log import BotLogger
from bot.bot_configs import config_bot
from bot.bot_utils import sqlite3_channel, sqlite3_map_imgs

bot_settings = config_bot.settings
logger = logging.getLogger(__name__)
task_logger = BotLogger(logger)


def register_tasks(bot: Bot):
    # 更新地图图片列表
    @bot.task.add_interval(hours=1)
    async def update_map_img_list():
        try:
            await task_update_map_list_json()
        except Exception as e:
            logger.exception(e)


async def task_update_map_list_json():
    try:
        json_data = await map_img.fetch_map_list()
        map_img.cache_map_list(json_data)
    except Exception as e:
        logger.exception(e)

