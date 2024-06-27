import logging
import a2s
from asyncio import exceptions
from typing import Union
from cachetools import TTLCache
from bot.bot_configs import config_global
from bot.bot_utils import utils_log
from bot.bot_utils.utils_bot import BotUtils
from a2s.info import SourceInfo, GoldSrcInfo
from dataclasses import dataclass

logger = logging.getLogger(__name__)
api_query_logger = utils_log.BotLogger(logger)
glob_config = config_global.settings
glob_timeout = glob_config.source_server_query_timeout

# 创建一个带有过期时间的缓存对象
cache_server = TTLCache(maxsize=300, ttl=60)
cache_player = TTLCache(maxsize=500, ttl=10)


@dataclass()
class QueryFailInfo(object):
    ip_and_port: str


class MyQueryApi(object):
    @staticmethod
    async def get_server_info(address, timeout=glob_timeout) \
            -> Union[SourceInfo, GoldSrcInfo]:
        if BotUtils.validate_ip_port(address):
            ip_addr = address
            spilt_res = ip_addr.split(":")
            address = (spilt_res[0], int(spilt_res[1]))

            # 检查缓存中是否存在对应的查询结果
            if address in cache_server:
                logger.debug(f"Retrieving server info from cache: {ip_addr}")
                return cache_server[address]

            try:
                logger.debug(f"Querying {ip_addr}")
                server_info = await a2s.ainfo(address, timeout=timeout)
                server_info.ip_and_port = ip_addr

                # 将查询结果添加到缓存中
                cache_server[address] = server_info
                logger.info(f"Successfully query {ip_addr}")
                return server_info
            except exceptions.TimeoutError:
                logger.exception(f"Timeout {ip_addr}", exc_info=False)
            except Exception as e:
                logger.exception(f"{ip_addr} Exception: {e}", exc_info=True)
        else:
            logger.info(f"ip is invalid.")

    @staticmethod
    async def get_server_player_info(address, timeout=glob_timeout):
        if BotUtils.validate_ip_port(address):
            ip_addr = address
            spilt_res = ip_addr.split(":")
            address = (spilt_res[0], int(spilt_res[1]))

            # 检查缓存中是否存在对应的查询结果
            if address in cache_player:
                logger.debug(f"Retrieving player info from cache: {ip_addr}")
                return cache_player[address]

            try:
                logger.debug(f"Querying {ip_addr} player info...")
                player_info = await a2s.aplayers(address, timeout=timeout)
                # 将查询结果添加到缓存中
                cache_player[address] = player_info
                logger.info(f"Successfully query player info for {ip_addr}")
                return player_info
            except exceptions.TimeoutError:
                logger.exception(f"Timeout {ip_addr}", exc_info=False)
            except Exception as e:
                logger.exception(f"{ip_addr} Exception: {e}", exc_info=True)
