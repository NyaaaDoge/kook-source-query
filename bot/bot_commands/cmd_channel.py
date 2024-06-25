import logging
from bot.bot_utils import utils_log
from bot.bot_configs import config_global
from khl import Bot, Message, PublicMessage
from bot.bot_utils.utils_bot import BotUtils
from bot.bot_apis.my_query_api import MyQueryApi
from bot.bot_utils import sqlite3_channel

global_settings = config_global.settings
logger = logging.getLogger(__name__)
cmd_channel_logger = utils_log.BotLogger(logger)
cmd_channel_logger.create_log_file("cmd_channel.log")


def reg_channel_cmd(bot: Bot):
    @bot.command(name="config", case_sensitive=False)
    async def config(msg: Message, command: str = None, *args):
        if not isinstance(msg, PublicMessage):
            return
        cmd_channel_logger.logging_public_msg(msg)
        current_channel_guild_id = msg.ctx.guild.id
        current_guild = await bot.client.fetch_guild(current_channel_guild_id)
        current_channel_id = msg.ctx.channel.id
        current_channel = await bot.client.fetch_public_channel(current_channel_id)
        if msg.author_id in global_settings.bot_developer_list:
            perm = True
        else:
            perm_util = BotUtils()
            perm = await perm_util.has_admin_and_manage(bot, msg.author_id, current_channel_guild_id)
        if perm:
            try:
                if not command:
                    chan_sql = sqlite3_channel.KookChannelSql()
                    db_info_list = chan_sql.get_all_sub_ip_by_channel_id(current_channel_id)
                    guild_info_list = chan_sql.get_all_sub_ip_by_guild_id(current_guild.id)
                    current_chan_sub_list = []
                    current_guild_sub_list = []
                    if any(db_info_list):
                        for row in db_info_list:
                            db_info = sqlite3_channel.DatabaseChannel(*row)
                            current_chan_sub_list.append(db_info.ip_subscription)
                        current_chan_desc = "\n".join(current_chan_sub_list)

                        for row in guild_info_list:
                            db_info = sqlite3_channel.DatabaseChannel(*row)
                            current_guild_sub_list.append(f"(chn){db_info.channel_id}(chn) 设置了 "
                                                          f"{db_info.ip_subscription}")
                        current_guild_desc = "\n".join(current_guild_sub_list)

                        await msg.reply(f"(ins)**当前频道设置信息({len(current_chan_sub_list)})：**(ins)"
                                        f"\n{current_chan_desc}\n"
                                        f"(ins)**当前服务器设置信息({len(current_guild_sub_list)})：**(ins)"
                                        f"\n{current_guild_desc}")

                    else:
                        await msg.reply("当前频道没有设置任何IP地址")

                if command in ["query"]:
                    if not any(args):
                        await msg.reply("/config query [IP地址:端口号] :red_square: 缺少所需参数：[IP地址:端口号]。\n"
                                        "举例：/config query 216.52.148.47:27015")
                        return

                    # 符合IP地址，端口格式
                    elif BotUtils.validate_ip_port(args[0]):
                        chan_sql = sqlite3_channel.KookChannelSql()
                        db_guild_info_list = chan_sql.get_all_sub_ip_by_guild_id(current_guild.id)
                        db_chan_info_list = chan_sql.get_all_sub_ip_by_channel_id(current_channel_id)
                        guild_saved_max_number = global_settings.guild_server_query_max_number
                        chan_saved_max_number = global_settings.channel_query_max_number
                        if len(db_guild_info_list) >= guild_saved_max_number:
                            await msg.reply(f":yellow_square: 服务器查询 ({args[0]}) 添加失败，"
                                            f"当前**服务器**配置IP数量大于{guild_saved_max_number}。")
                            return
                        elif len(db_chan_info_list) >= chan_saved_max_number:
                            await msg.reply(f":yellow_square: 服务器查询 ({args[0]}) 添加失败，"
                                            f"当前**频道**配置IP数量大于{chan_saved_max_number}。")
                            return
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

                    else:
                        await msg.reply(f":red_square: 服务器查询 ({args[0]}) 添加失败，可能是由于该地址不合法。")

                elif command in ["delete"]:
                    if not any(args):
                        await msg.reply("/config delete [IP地址:端口号] :red_square: 缺少所需参数：[IP地址:端口号]")
                        return

                    # 符合IP地址，端口格式
                    elif BotUtils.validate_ip_port(args[0]):
                        chan_sql = sqlite3_channel.KookChannelSql()
                        delete_result = chan_sql.delete_channel_ip_sub_by_ip(current_channel_id, args[0])
                        if delete_result:
                            await msg.reply(f":green_square: 服务器查询 ({args[0]}) 删除成功")
                        else:
                            await msg.reply(f":red_square: 服务器查询 ({args[0]}) 删除失败，请联系管理员")

                    else:
                        await msg.reply(f":red_square: 服务器查询 ({args[0]}) 删除失败，可能是由于该地址不合法。")

                elif command in ["showip"]:
                    if not any(args):
                        await msg.reply("`/config showip on` 开启查询结果IP地址显示\n"
                                        "`/config showip off` 关闭查询结果IP地址显示")
                        return

                    elif args[0] in ['on']:
                        chan_sql = sqlite3_channel.KookChannelSql()
                        update_flag = chan_sql.update_channel_show_ip_option(1, current_channel_id)
                        if update_flag:
                            await msg.reply(f":green_square: 开启频道IP地址显示成功")
                        else:
                            await msg.reply(f":red_square: 开启频道IP地址显示失败，请联系管理员")

                    elif args[0] in ['off']:
                        chan_sql = sqlite3_channel.KookChannelSql()
                        update_flag = chan_sql.update_channel_show_ip_option(0, current_channel_id)
                        if update_flag:
                            await msg.reply(f":green_square: 关闭频道IP地址显示成功")
                        else:
                            await msg.reply(f":red_square: 关闭频道IP地址显示失败，请联系管理员")

                elif command in ["showimg"]:
                    if not any(args):
                        await msg.reply("`/config showimg on`开启查询结果图片显示\n"
                                        "`/config showimg off` 关闭查询结果图片显示")
                        return

                    elif args[0] in ['on']:
                        chan_sql = sqlite3_channel.KookChannelSql()
                        update_flag = chan_sql.update_channel_show_img_option(1, current_channel_id)
                        if update_flag:
                            await msg.reply(f":green_square: 开启频道图片显示成功")
                        else:
                            await msg.reply(f":red_square: 开启频道图片显示失败，请联系管理员")

                    elif args[0] in ['off']:
                        chan_sql = sqlite3_channel.KookChannelSql()
                        update_flag = chan_sql.update_channel_show_img_option(0, current_channel_id)
                        if update_flag:
                            await msg.reply(f":green_square: 关闭频道图片显示成功")
                        else:
                            await msg.reply(f":red_square: 关闭频道图片显示失败，请联系管理员")

            except Exception as e:
                logging.exception(e, exc_info=True)
                await msg.reply("发生了一些未知错误，请联系开发者解决。")

        else:
            await msg.reply("您没有对应的管理权限。配置频道IP地址查询需要您的权限有：服务器管理员，频道管理员。")
