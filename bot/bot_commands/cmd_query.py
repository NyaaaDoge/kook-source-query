import asyncio
import logging
import re

from khl.command import Rule
from bot.bot_utils import utils_log
from bot.bot_apis.my_query_api import MyQueryApi, QueryFailInfo
from bot.bot_configs import config_global
from khl import Bot, Message, MessageTypes, HTTPRequester, PublicMessage
from bot.bot_cards_message.cards_msg_server import query_server_result_card_msg, query_server_results_batch_card_msg, \
    query_server_player_list_card_msg
from bot.bot_utils.utils_bot import BotUtils
from bot.bot_utils import sqlite3_channel

global_settings = config_global.settings
logger = logging.getLogger(__name__)
cmd_query_logger = utils_log.BotLogger(logger)
cmd_query_logger.create_log_file("cmd_query.log")


def reg_query_cmd(bot: Bot):
    @bot.command(name="query", case_sensitive=False)
    async def query(msg: Message, command: str = None, *args):
        if not isinstance(msg, PublicMessage):
            return
        cmd_query_logger.logging_public_msg(msg)
        if not command:
            await msg.reply("用法：\n`/query ip [ip地址:端口号]` - 查询特定IP的起源/金源游戏服务器信息\n"
                            "`/query server` - 查询当前频道配置好的服务器信息。可以使用关键字“查”并且@机器人触发该指令。\n"
                            "举例：`/query ip 216.52.148.47:27015`", type=MessageTypes.KMD)
            return

        elif command in ['ip']:
            if not any(args):
                await msg.reply("用法：`/query ip [ip地址:端口号]` - 查询特定IP的服务器信息\n"
                                "举例：`/query ip 216.52.148.47:27015`", type=MessageTypes.KMD)
                return

            elif len(args) == 1:
                if BotUtils.validate_ip_port(args[0]):
                    ip_addr = args[0]
                    await query_single_ip(msg, ip_addr)
                else:
                    await msg.reply("请输入要查询的服务器地址，包括端口号，您可能遗漏了端口号。正确格式：[ip地址:端口号]")

        elif command in ['server']:
            await query_batch(msg)

        elif command in ['player']:
            if len(args) == 1:
                if BotUtils.validate_ip_port(args[0]):
                    ip_addr = args[0]
                    await query_player_list(msg, ip_addr)

        else:
            await msg.reply("用法：\n`/query ip [ip地址:端口号]` - 查询特定IP的服务器信息\n"
                            "`/query server` - 查询当前频道配置好的服务器信息\n"
                            "举例：`/query ip 216.52.148.47:27015`", type=MessageTypes.KMD)

    @bot.command(regex=r".*查.*", rules=[Rule.is_bot_mentioned(bot)])
    async def query_batch_cmd(msg: Message):
        await query_batch(msg)

    @bot.command(regex="connect .*")
    async def connect_query_cmd(msg: Message):
        # 消息connect xxx:xxx会触发该指令
        pattern = r"connect ((?:\d{1,3}\.){3}\d{1,3}|[a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+):(\d+)"
        match = re.search(pattern, msg.content)
        if not match:
            logger.info("failed to match ip and address")
            return
        address = match.group(1)
        port = match.group(2)
        ip_addr = f"{address}:{port}"
        await query_single_ip(msg, ip_addr, True)

    @bot.command(regex="player .*")
    async def player_query_cmd(msg: Message):
        # 消息player xxx:xxx会触发该指令
        pattern = r"player ((?:\d{1,3}\.){3}\d{1,3}|[a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+):(\d+)"
        match = re.search(pattern, msg.content)
        if not match:
            logger.info("failed to match ip and address")
            return
        address = match.group(1)
        port = match.group(2)
        ip_addr = f"{address}:{port}"
        await query_player_list(msg, ip_addr)


async def query_batch(msg: Message):
    if not isinstance(msg, PublicMessage):
        return
    cmd_query_logger.logging_public_msg(msg)
    try:
        current_channel_id = msg.ctx.channel.id
        chan_sql = sqlite3_channel.KookChannelSql()
        db_info = chan_sql.get_all_sub_ip_by_channel_id(current_channel_id)
        ip_to_query_list = []
        # server_info_list = []
        show_ip_flag = False
        show_img_flag = True
        if db_info:
            for row in db_info:
                db_channel = sqlite3_channel.DatabaseChannel(*row)
                if db_channel.show_ip == 1:
                    show_ip_flag = True
                if db_channel.show_img == 0:
                    show_img_flag = False
                ip_to_query_list.append(db_channel.ip_subscription)
        else:
            await msg.reply(f"当前频道尚未配置任何IP地址，请使用`/config query [ip:端口]`进行配置添加。")
            return
        if any(ip_to_query_list):
            # TODO 使用异步并发执行所有查询
            query_tasks_list = [MyQueryApi().get_server_info(ip, timeout=3) for ip in ip_to_query_list]
            results = await asyncio.gather(*query_tasks_list)
            # 处理查询结果
            server_info_list = [
                result if result else QueryFailInfo(ip)
                for ip, result in zip(ip_to_query_list, results)
            ]
            #
            # for ip in ip_to_query_list:
            #     query_tasks_list.append(asyncio.create_task(MyQueryApi().get_server_info(ip, timeout=3)))
            #     server_info = await MyQueryApi().get_server_info(ip, timeout=timeout_glob)
            #     if server_info:
            #         server_info_list.append(server_info)
            #     else:
            #         server_info_list.append(QueryFailInfo(ip))
            try:
                # 使用多服务器卡片消息
                card_msg = query_server_results_batch_card_msg(server_info_list, map_img=show_img_flag,
                                                               show_ip=show_ip_flag)
                await msg.reply(type=MessageTypes.CARD, content=card_msg)
            except HTTPRequester.APIRequestFailed as failed:
                try:
                    # 如果遇到 40000 代码再创建不发送图片的任务。如果是卡片消息创建失败，首先尝试发送没有图片的卡片消息。
                    if failed.err_code == 40000:
                        card_msg = query_server_results_batch_card_msg(server_info_list, map_img=show_img_flag,
                                                                       show_ip=show_ip_flag)
                        await msg.reply(type=MessageTypes.CARD, content=card_msg)
                except Exception as e:
                    logger.exception(f"exception {e}")
                    await msg.reply(f"出现了一些问题，可能是服务器通信错误，也可能是IP地址有误，请稍后再试。")
    except Exception as e:
        logger.exception(f"exception {e}")
        await msg.reply(f"出现了一些问题，请稍后再试，或联系开发者。")


async def query_single_ip(msg: Message, ip_addr: str, key_words: bool = False):
    try:
        timeout_glob = global_settings.source_server_query_timeout
        server_info = await MyQueryApi().get_server_info(ip_addr, timeout=timeout_glob)
        try:
            # 首次发送先尝试发送图片
            card_msg = query_server_result_card_msg(server_info, map_img=True, show_keywords=key_words)
            await msg.reply(type=MessageTypes.CARD, content=card_msg)
        except HTTPRequester.APIRequestFailed as failed:
            try:
                logger.info(f"Failed to send map img. Sending info without img...")
                # 如果遇到 40000 代码再创建不发送图片的任务。如果是卡片消息创建失败，首先尝试发送没有图片的卡片消息。
                if failed.err_code == 40000:
                    card_msg = query_server_result_card_msg(server_info, map_img=False, show_keywords=key_words)
                    await msg.reply(type=MessageTypes.CARD, content=card_msg)
            except Exception as e:
                logger.exception(f"exception {e}")
    except Exception as e:
        logger.exception(f"exception {e}")
        await msg.reply(f"出现了一些问题，可能是服务器通信错误，也可能是IP地址有误，请稍后再试。")


async def query_player_list(msg: Message, ip_addr: str):
    try:
        server_info = await MyQueryApi.get_server_info(ip_addr)
        player_info = await MyQueryApi.get_server_player_info(ip_addr)
        card_msg = query_server_player_list_card_msg(server_info, player_info)
        await msg.reply(type=MessageTypes.CARD, content=card_msg)
    except Exception as e:
        await msg.reply("查询失败，出现未知问题，请联系开发者解决")
        logger.exception(e)
