import logging
from khl.command import Rule
from bot.bot_utils import utils_log
from bot.bot_apis.my_query_api import MyQueryApi, QueryFailInfo
from bot.bot_configs import config_global
from khl import Bot, Message, MessageTypes, HTTPRequester, PublicMessage
from bot.bot_cards_message.cards_msg_server import query_server_result_card_msg, query_server_results_batch_card_msg
from bot.bot_utils.utils_bot import BotUtils
from bot.bot_utils import sqlite3_channel, sqlite3_submap

global_settings = config_global.settings
logger = logging.getLogger(__name__)
cmd_query_logger = utils_log.BotLogger(logger)
cmd_query_logger.create_log_file("cmd_query.log")


def reg_query_cmd(bot: Bot):
    @bot.command(name="query", case_sensitive=False)
    async def query(msg: Message, command: str = None, *args):
        if not isinstance(msg, PublicMessage):
            return
        cmd_query_logger.logging_msg(msg)
        if not command:
            await msg.reply("用法：\n`/query ip [ip地址:端口号]` - 查询特定IP的起源/金源游戏服务器信息\n"
                            "`/query server` - 查询当前频道配置好的服务器信息。可以使用关键字“查”并且@机器人触发该指令。\n"
                            "`/query sub [完整地图名]` - 订阅特定地图。当管理员设置的监控服务器里面有你订阅的地图名时，Bot将私信通知您。\n"
                            "`/query unsub [完整地图名]` - 取消订阅特定地图。"
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
                    try:
                        timeout_glob = global_settings.source_server_query_timeout
                        server_info = await MyQueryApi().get_server_info(ip_addr, timeout=timeout_glob)
                        try:
                            # 首次发送先尝试发送图片
                            card_msg = query_server_result_card_msg(server_info, map_img=True)
                            await msg.reply(type=MessageTypes.CARD, content=card_msg)
                        except HTTPRequester.APIRequestFailed as failed:
                            try:
                                logger.info(f"Failed to send map img. Sending info without img...")
                                # 如果遇到 40000 代码再创建不发送图片的任务。如果是卡片消息创建失败，首先尝试发送没有图片的卡片消息。
                                if failed.err_code == 40000:
                                    card_msg = query_server_result_card_msg(server_info, map_img=False)
                                    await msg.reply(type=MessageTypes.CARD, content=card_msg)
                            except Exception as e:
                                logger.exception(f"exception {e}")
                    except Exception as e:
                        logger.exception(f"exception {e}")
                        await msg.reply(f"出现了一些问题，可能是服务器通信错误，也可能是IP地址有误，请稍后再试。")
                else:
                    await msg.reply("请输入要查询的服务器地址，包括端口号，您可能遗漏了端口号。正确格式：[ip地址:端口号]")

        elif command in ['server']:
            await query_batch(msg)

        elif command in ['sub']:
            if not any(args):
                user_sub_sql = sqlite3_submap.KookUserSubSql()
                user_sub_info_list = user_sub_sql.get_all_user_sub_map_by_user_id(msg.author_id)
                sub_info = []
                for row in user_sub_info_list:
                    db_info = sqlite3_submap.DatabaseUserSub(*row)
                    sub_info.append(db_info.sub_map_name)
                sub_info_desc = "\n".join(sub_info)
                await msg.reply("用法：`/query sub [map_name]` - 订阅特定地图，每当监测到该地图时会进行私信推送通知。\n"
                                "`/query unsub [map_name]` - 取消订阅特定地图。\n"
                                "请使用 [完整地图名] 如 ze_2012_p3, ze_k19_escape_go1 等格式来订阅，需要版本号精确匹配。\n"
                                "举例：`/query sub ze_2012_p3`\n"
                                f"**当前订阅地图({len(sub_info)})：**\n{sub_info_desc}", type=MessageTypes.KMD)
                return

            elif len(args) == 1:
                map_name = args[0]
                current_channel_id = msg.ctx.channel.id
                current_channel = await bot.client.fetch_public_channel(current_channel_id)
                sub_sql = sqlite3_submap.KookUserSubSql()
                insert_flag = sub_sql.insert_user_sub_map(current_channel, msg.author_id, map_name)
                if insert_flag:
                    await msg.reply(f":green_square: 地图订阅 ({map_name}) 添加成功")
                else:
                    await msg.reply(f":red_square: 地图订阅 ({map_name}) 添加失败，可能是由于地图订阅已经添加过。")

        elif command in ['unsub']:
            if not any(args):
                await msg.reply("用法：`/query unsub [map_name]` - 取消订阅特定地图，每当监测到该地图进行推送通知。"
                                "请使用 [完整地图名] 如 ze_2012_p3, ze_k19_escape_go1 等格式来订阅，需要版本号精确匹配。\n"
                                "举例：`/query unsub ze_2012_p3`", type=MessageTypes.KMD)
                return

            elif len(args) == 1:
                map_name = args[0]
                sub_sql = sqlite3_submap.KookUserSubSql()
                delete_flag = sub_sql.delete_user_sub_map(msg.author_id, map_name)
                if delete_flag:
                    await msg.reply(f":green_square: 地图订阅 ({args[0]}) 删除成功")
                else:
                    await msg.reply(f":red_square: 地图订阅 ({args[0]}) 删除失败，可能是地图名出错。")

        else:
            await msg.reply("用法：\n`/query ip [ip地址:端口号]` - 查询特定IP的服务器信息\n"
                            "`/query server` - 查询当前频道配置好的服务器信息\n"
                            "举例：`/query ip 216.52.148.47:27015`", type=MessageTypes.KMD)

    @bot.command(regex=r".*查.*", rules=[Rule.is_bot_mentioned(bot)])
    async def query_batch_cmd(msg: Message):
        await query_batch(msg)


async def query_batch(msg: Message):
    if not isinstance(msg, PublicMessage):
        return
    cmd_query_logger.logging_msg(msg)
    try:
        current_channel_id = msg.ctx.channel.id
        chan_sql = sqlite3_channel.KookChannelSql()
        db_info = chan_sql.get_all_sub_ip_by_channel_id(current_channel_id)
        ip_to_query_list = []
        server_info_list = []
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
            for ip in ip_to_query_list:
                timeout_glob = global_settings.source_server_query_timeout
                server_info = await MyQueryApi().get_server_info(ip, timeout=timeout_glob)
                if server_info:
                    server_info_list.append(server_info)
                else:
                    server_info_list.append(QueryFailInfo(ip))
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
