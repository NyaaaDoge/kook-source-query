import logging

from bot.bot_apis.my_query_api import MyQueryApi
from bot.bot_configs import config_global
from bot.bot_utils import sqlite3_channel, sqlite3_submap
from bot.bot_utils.utils_bot import BotUtils
from bot.bot_utils.utils_log import BotLogger
from bot.bot_tasks import my_tasks
from khl import Bot, Message, MessageTypes, PublicMessage

global_settings = config_global.settings
logger = logging.getLogger(__name__)
cmd_logger = BotLogger(logger)


def reg_basic_cmd(bot: Bot):
    @bot.command(name="hellosrc", case_sensitive=False)
    async def cmd_hello(msg: Message):
        if not isinstance(msg, PublicMessage):
            return
        cmd_logger.logging_msg(msg)
        await msg.reply("有什么想查的服务器？")

    @bot.command(name="help", case_sensitive=False)
    async def cmd_help(msg: Message):
        if not isinstance(msg, PublicMessage):
            return
        cmd_logger.logging_msg(msg)
        await msg.reply(f"""Sauce Query Bot{global_settings.BOT_VERSION} 帮助文档：
`/query ip [ip地址:端口号]` - 查询特定IP地址的起源/金源服务器信息
`/query server` - 查询该频道设置好的IP地址列表的服务器信息
`/query sub [map_name]` - 订阅特定地图，Bot监测到设定好的服务器有特定地图将会私信通知。
`/query unsub [map_name]` - 取消订阅特定地图。
`/config query [ip地址:端口号]` - 为当前频道设置添加要查询的IP地址
`/config delete [ip地址:端口号]` - 删除设置里面当前频道对应的IP地址
`/config showip [on/off]` - 为当前频道的查询设置显示/关闭IP地址结果
`/config showimg [on/off]` - 为当前频道的查询设置显示/关闭预览图片，关闭图片后可以有效提高查询速度。
`/config` - 查看当前频道查询的设置信息和当前服务器的设置信息
一个服务器最多设置30个IP地址查询，一个频道最多设置15个IP地址查询。如有更多需求请自行前往Github获取源码自行部署。
小技巧：只要在频道发送消息里面有关键字“查”并且@机器人即可查询服务器信息。功能同`/query server`。如`@机器人 查`
[Github项目](https://github.com/NyaaaDoge/kook-source-query)
[预览图片项目](https://newpage-community.github.io/csgo-map-images/)，目前预览图片只有CSGO部分社区地图预览图片。
觉得不错的话在 [Github页面](https://github.com/NyaaaDoge/kook-source-query) 点个 star 吧！
或者在 [爱发电](https://afdian.net/a/NyaaaDoge) 支持作者！
""")

    @bot.command(name='admin')
    async def admin(msg: Message, command: str = None, *args):
        cmd_logger.logging_msg(msg)
        if msg.author.id in global_settings.bot_developer_list:
            try:
                if command is None:
                    await msg.reply("`/admin update maplist`\n"
                                    "`/admin update track`\n"
                                    "`/admin insert [ip:port]`\n"
                                    "`/admin leave [gid]`\n"
                                    "`/admin track [ip:port]`\n"
                                    "`/admin untrack [ip:port]`", type=MessageTypes.KMD)

                elif command in ['insert']:
                    current_channel_id = msg.ctx.channel.id
                    current_channel = await bot.client.fetch_public_channel(current_channel_id)
                    chan_sql = sqlite3_channel.KookChannelSql()
                    ip_addr_to_be_save = await MyQueryApi().get_server_info(args[0])
                    if not ip_addr_to_be_save:
                        await msg.reply(f":red_square: 服务器查询 ({args[0]}) 添加失败，"
                                        f"无法查询该地址对应的游戏服务器信息，有可能是服务器无法通信，也有可能地址错误。")
                        return
                    insert_flag = chan_sql.insert_channel_ip_sub(current_channel, args[0])
                    if insert_flag:
                        await msg.reply(f":green_square: 服务器查询 ({args[0]}) 添加成功")
                    else:
                        await msg.reply(f":red_square: 服务器查询 ({args[0]}) 添加失败，可能是由于该地址已经添加过。")

                elif command in ['update']:
                    if not any(args):
                        await msg.reply("`/admin update maplist`\n"
                                        "`/admin update track`", type=MessageTypes.KMD)

                    elif args[0] in ['maplist']:
                        await my_tasks.task_update_map_list_json()
                        await msg.reply("执行更新地图列表json完成。", type=MessageTypes.KMD)

                    elif args[0] in ['track']:
                        await my_tasks.task_track_server_map_info(bot)
                        await msg.reply("执行监控服务器地图信息任务完成。", type=MessageTypes.KMD)

                elif command in ['leave']:
                    if not any(args):
                        await msg.reply("用法 `/admin leave [gid]`", type=MessageTypes.KMD)
                        return

                    elif len(args) == 1:
                        try:
                            target_guild = await bot.client.fetch_guild(args[0])
                            await msg.reply(f"获取到Bot加入了此服务器。服务器信息如下：\n"
                                            f"服务器id: {target_guild.id}\n"
                                            f"服务器name: {target_guild.name}\n"
                                            f"服务器master_id: {target_guild.master_id}\n"
                                            f"您确定要退出该服务器吗？\n"
                                            f"确定请输入 `.admin leave {target_guild.id} confirm`", type=MessageTypes.KMD)

                        except Exception as e:
                            logger.exception(e, exc_info=True)
                            await msg.reply("获取服务器失败，请检查服务器id是否正确。", type=MessageTypes.KMD)

                    elif any(args[0]) and args[1] == "confirm":
                        target_guild = await bot.client.fetch_guild(args[0])
                        await target_guild.leave()
                        await msg.reply("Bot成功退出此服务器！", type=MessageTypes.KMD)

                elif command in ['track']:
                    if not any(args):
                        track_sql = sqlite3_submap.ServerTrackSql()
                        track_info_list = track_sql.get_all_server_track()
                        track_info = []
                        for info in track_info_list:
                            track_info.append(f"IP: {info.ip_and_port} 名称: {info.server_name}")
                        track_info_desc = "\n".join(track_info)
                        await msg.reply("用法 `/admin track [ip:port]`\n"
                                        f"**服务器监测信息({len(track_info)}):**\n{track_info_desc}",
                                        type=MessageTypes.KMD)
                        return

                    elif BotUtils.validate_ip_port(args[0]):
                        track_sql = sqlite3_submap.ServerTrackSql()
                        ip_addr_to_be_save = await MyQueryApi().get_server_info(args[0])
                        if not ip_addr_to_be_save:
                            await msg.reply(f":red_square: 服务器监测 ({args[0]}) 添加失败，"
                                            f"无法查询该地址对应的游戏服务器信息，有可能是服务器无法通信，也有可能地址错误。")
                            return
                        insert_flag = track_sql.insert_server_track(args[0], ip_addr_to_be_save.server_name)
                        if insert_flag:
                            await msg.reply(f":green_square: 服务器监测 ({args[0]}) 添加成功")
                        else:
                            await msg.reply(f":red_square: 服务器监测 ({args[0]}) 添加失败，可能是由于该地址已经添加过。")

                elif command in ['untrack']:
                    if not any(args):
                        await msg.reply("用法 `/admin untrack [ip:port]`", type=MessageTypes.KMD)
                        return

                    elif BotUtils.validate_ip_port(args[0]):
                        track_sql = sqlite3_submap.ServerTrackSql()
                        del_flag = track_sql.delete_server_track(args[0])
                        if del_flag:
                            await msg.reply(f":green_square: 服务器监测 ({args[0]}) 删除成功")
                        else:
                            await msg.reply(f":red_square: 服务器监测 ({args[0]}) 删除失败，可能是由于该地址不存在。")

            except Exception as e:
                logging.error(e, exc_info=True)
                await msg.reply(f"{e}")
