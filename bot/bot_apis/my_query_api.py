import logging
import re

import a2s
import dns.asyncresolver

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
cache_dns = TTLCache(maxsize=300, ttl=6000)
cache_server = TTLCache(maxsize=300, ttl=60)
cache_player = TTLCache(maxsize=500, ttl=10)


@dataclass()
class QueryFailInfo(object):
    ip_and_port: str


async def resolve_domain(domain, **kwargs):
    logger.info(f"resolving domain: {domain} with kw{kwargs}")
    try:
        if domain in cache_dns:
            logger.debug(f"Retrieving server info from cache: {domain}")
            return cache_dns[domain]

        result = await dns.asyncresolver.resolve(domain, **kwargs)
        cache_dns[domain] = result
        return result
    except Exception as e:
        logger.exception(e)


class MyQueryApi(object):
    @staticmethod
    async def get_server_info(address, timeout=glob_timeout, dns_resolve=False) \
            -> Union[SourceInfo, GoldSrcInfo]:
        if BotUtils.validate_ip_port(address):
            ip_addr_and_port = address
            spilt_res = ip_addr_and_port.split(":")
            ip_addr = spilt_res[0]
            ip_port = int(spilt_res[1])
            address = ( ip_addr, ip_port)

            # 检查缓存中是否存在对应的查询结果
            if address in cache_server:
                logger.debug(f"Retrieving server info from cache: {ip_addr_and_port}")
                return cache_server[address]

            try:
                logger.debug(f"Querying {ip_addr_and_port}")
                server_info = await a2s.ainfo(address, timeout=timeout)
                domain_pattern = r'^(?!\d{1,3}(\.\d{1,3}){3}$)([A-Za-z0-9.-]+)$'
                domain_match = re.search(domain_pattern, ip_addr)
                server_info.resolved_ip_address = [ip_addr]
                # 只解析域名
                if domain_match and dns_resolve:
                    domain = domain_match.group(0)
                    res = await resolve_domain(domain,  rdtype="A")
                    if res:
                        ip_addresses = [rdata.to_text() for rdata in res]
                        server_info.resolved_ip_address = ip_addresses

                server_info.ip_and_port = ip_addr_and_port

                # 将查询结果添加到缓存中
                cache_server[address] = server_info
                logger.info(f"Successfully query {ip_addr_and_port}")
                return server_info
            except exceptions.TimeoutError:
                logger.exception(f"Timeout {ip_addr_and_port}", exc_info=False)
            except Exception as e:
                logger.exception(f"{ip_addr_and_port} Exception: {e}", exc_info=True)
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
