import logging
import a2s
from typing import Union
from cachetools import TTLCache
from bot.bot_configs import config_global
from bot.bot_utils import utils_log
from bot.bot_utils.utils_bot import BotUtils
from a2s.info import SourceInfo, GoldSrcInfo
from dataclasses import dataclass

logger = logging.getLogger(__name__)
cmd_query_logger = utils_log.BotLogger(logger)
cmd_query_logger.create_log_file("cmd_query.log")
glob_config = config_global.settings

# 创建一个带有过期时间的缓存对象，设置过期时间为60秒，最大缓存条目数为200
cache = TTLCache(maxsize=200, ttl=60)


@dataclass()
class QueryFailInfo(object):
    ip_and_port: str


class MyQueryApi(object):

    @staticmethod
    async def get_server_info(address, timeout=glob_config.source_server_query_timeout) \
            -> Union[SourceInfo, GoldSrcInfo]:
        if BotUtils.validate_ip_port(address):
            ip_addr = address
            spilt_res = ip_addr.split(":")
            address = (spilt_res[0], int(spilt_res[1]))

            # 检查缓存中是否存在对应的查询结果
            if address in cache:
                logger.info(f"Retrieving server info from cache: {ip_addr}")
                return cache[address]

            try:
                logger.info(f"Querying {ip_addr}...")
                server_info = await a2s.ainfo(address, timeout=timeout)
                server_info.ip_and_port = ip_addr

                # 将查询结果添加到缓存中
                cache[address] = server_info
                logger.info(f"Successfully query {ip_addr}.")
                return server_info
            except Exception as e:
                logger.exception(e, exc_info=True)
        else:
            logger.info(f"ip is invalid.")
