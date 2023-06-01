import logging
from bot.bot_utils import utils_log
from bot.bot_apis.my_query_api import MyQueryApi
from bot.bot_configs import config_global
from khl import Bot, Message, MessageTypes, HTTPRequester
from bot.bot_cards_message.cards_msg_server import query_server_result_card_msg, query_server_results_batch_card_msg
from bot.bot_utils.utils_bot import BotUtils
from bot.bot_utils import sqlite3_channel

global_settings = config_global.settings
logger = logging.getLogger(__name__)
cmd_query_logger = utils_log.BotLogger(logger)
cmd_query_logger.create_log_file("cmd_query.log")


def reg_query_cmd(bot: Bot):
    @bot.command(name="query")
    async def query(msg: Message, command: str = None, *args):
        cmd_query_logger.logging_msg(msg)
        if not command:
            await msg.reply("用法：\n`/query ip [ip地址:端口号]` - 查询特定IP的服务器信息\n"
                            "`/query server` - 查询当前频道配置好的服务器信息", type=MessageTypes.KMD)
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
                        await msg.reply(f"出现了一些问题，可能是服务器通信错误，请稍后再试。")
                else:
                    await msg.reply("请输入要查询的服务器地址，包括端口号，您可能遗漏了端口号。正确格式：[ip地址:端口号]")

        elif command in ['server']:
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
            if any(ip_to_query_list):
                for ip in ip_to_query_list:
                    timeout_glob = global_settings.source_server_query_timeout
                    server_info = await MyQueryApi().get_server_info(ip, timeout=timeout_glob)
                    server_info_list.append(server_info)
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
                        await msg.reply(f"出现了一些问题，可能是服务器通信错误，请稍后再试。")

