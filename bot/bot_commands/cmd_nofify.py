import logging
import re
from bot.bot_utils import utils_log
from bot.bot_configs import config_global
from bot.bot_cards_message import cards_msg_server
from khl import Bot, Message, MessageTypes, PublicMessage
from bot.bot_utils import sqlite3_submap

global_settings = config_global.settings
logger = logging.getLogger(__name__)
cmd_notify_logger = utils_log.BotLogger(logger)
cmd_notify_logger.create_log_file("cmd_notify.log")


def reg_notify_cmd(bot: Bot):
    @bot.command(name="notify", case_sensitive=False)
    async def notify(msg: Message, command: str = None, *args):
        if not isinstance(msg, PublicMessage):
            return
        cmd_notify_logger.logging_msg(msg)

        if not command:
            await msg.reply("`/notify map [完整地图名]` - 订阅特定地图。当管理员设置的监控服务器里面有你订阅的地图名时，Bot将私信通知您。\n"
                            "`/notify unsub [完整地图名]` - 取消订阅特定地图。\n"
                            "`/notify list` - 查看当前订阅的地图列表。\n"
                            "`/notify wipe` - 清除当前设置的订阅地图列表。", type=MessageTypes.KMD)
            return

        elif command in ['map']:
            if not any(args):
                await msg.reply("`/notify map [map_name]` - 订阅特定地图，每当监测到该地图时会进行私信推送通知。\n"
                                "`/notify unsub [map_name]` - 取消订阅特定地图。\n"
                                "请使用 [完整地图名] 如 ze_2012_p3, ze_k19_escape_go1 等格式来订阅，需要版本号精确匹配。\n"
                                "举例：`/notify map ze_2012_p3`")

            elif len(args) == 1:
                input_str = args[0]
                # 支持使用逗号分隔多个地图名
                if "," in input_str:
                    map_name_list = input_str.split(',')
                elif "，" in input_str:
                    map_name_list = input_str.split('，')
                else:
                    map_name_list = [input_str]
                # 需要将用户输入的kmd等字符串处理掉。使用正则表达式替换非英文字符、下划线和数字
                for map_name in map_name_list:
                    map_name = re.sub(r'[^a-zA-Z_\d]', '', map_name)
                    current_channel_id = msg.ctx.channel.id
                    current_channel = await bot.client.fetch_public_channel(current_channel_id)
                    sub_sql = sqlite3_submap.KookUserSubSql()
                    insert_flag = sub_sql.insert_user_sub_map(current_channel, msg.author_id, map_name)
                    if insert_flag:
                        await msg.reply(f":green_square: 地图订阅 ({map_name}) 添加成功，当bot检测到该地图时将私信通知您。")
                    else:
                        await msg.reply(f":red_square: 地图订阅 ({map_name}) 添加失败，可能是由于地图订阅已经添加过。")

        elif command in ['unsub']:
            if not any(args):
                await msg.reply("`/notify unsub [map_name]` - 取消订阅特定地图，每当监测到该地图进行推送通知。"
                                "请使用 [完整地图名] 如 ze_2012_p3, ze_k19_escape_go1 等格式来订阅，需要版本号精确匹配。\n"
                                "举例：`/notify unsub ze_2012_p3`", type=MessageTypes.KMD)
                return

            elif len(args) == 1:
                input_str = args[0]
                # 支持使用逗号分隔多个地图名
                if "," in input_str:
                    map_name_list = input_str.split(',')
                elif "，" in input_str:
                    map_name_list = input_str.split('，')
                else:
                    map_name_list = [input_str]
                sub_sql = sqlite3_submap.KookUserSubSql()
                for map_name in map_name_list:
                    delete_flag = sub_sql.delete_user_sub_map(msg.author_id, map_name)
                    if delete_flag:
                        await msg.reply(f":green_square: 地图订阅 ({map_name}) 删除成功")
                    else:
                        await msg.reply(f":red_square: 地图订阅 ({map_name}) 删除失败，可能是地图名出错。")

        elif command in ['list']:
            if not any(args):
                user_sub_sql = sqlite3_submap.KookUserSubSql()
                user_sub_info_list = user_sub_sql.get_all_user_sub_map_by_user_id(msg.author_id)
                sub_info = []
                for row in user_sub_info_list:
                    db_info = sqlite3_submap.DatabaseUserSub(*row)
                    sub_info.append(db_info.sub_map_name)
                card_msg = cards_msg_server.player_notify_map_list_card_msg(msg.author_id, sub_info)
                await msg.reply(type=MessageTypes.CARD, content=card_msg)
                # sub_info_desc = "\n".join(sub_info)
                # await msg.reply(f"**当前订阅地图({len(sub_info)})：**\n{sub_info_desc}", type=MessageTypes.KMD)

        elif command in ['wipe']:
            if not any(args):
                user_sub_sql = sqlite3_submap.KookUserSubSql()
                user_sub_info_list = user_sub_sql.get_all_user_sub_map_by_user_id(msg.author_id)
                await msg.reply(f"当前订阅地图数量为 {len(user_sub_info_list)} ，您确定要清除您的所有地图订阅吗？\n"
                                f"需要查看订阅的地图列表请输入`/notify list`\n"
                                f"确认清除请再次输入`/notify wipe confirm`", type=MessageTypes.KMD)
                return

            elif args[0] == 'confirm':
                sub_sql = sqlite3_submap.KookUserSubSql()
                delete_flag = sub_sql.delete_user_all_sub_map_by_user_id(msg.author_id)
                if delete_flag:
                    await msg.reply(f":green_square: 地图订阅列表删除成功，总计删除了 {delete_flag} 个地图订阅。")
                else:
                    await msg.reply(f":red_square: 地图订阅列表删除失败，可能是您尚未订阅任一地图，或联系开发者解决。")
