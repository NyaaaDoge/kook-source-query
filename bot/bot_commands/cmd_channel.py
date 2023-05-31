import logging
from bot.bot_utils import utils_log
from bot.bot_configs import config_global
from khl import Bot, Message, MessageTypes, HTTPRequester
from bot.bot_cards_message.cards_msg_server import query_server_result_card_msg
from bot.bot_utils.utils_bot import BotUtils
from bot.bot_utils import sqlite3_channel

global_settings = config_global.settings
logger = logging.getLogger(__name__)
cmd_channel_logger = utils_log.BotLogger(logger)
cmd_channel_logger.create_log_file("cmd_channel.log")


def reg_channel_cmd(bot: Bot):
    @bot.command(name="config")
    async def config(msg: Message, command: str = None, *args):
        cmd_channel_logger.logging_msg(msg)
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
                    await msg.reply("`/config query [IP地址:端口号]` - 为当前频道保存查询的服务器地址", type=MessageTypes.KMD)
                    return

                if command in ["query"]:
                    if not any(args):
                        await msg.reply("""/config query [IP地址:端口号] :red_square: 缺少所需参数：[IP地址:端口号]""")
                        return

                    # 符合IP地址，端口格式
                    elif BotUtils.validate_ip_port(args[0]):
                        chan_sql = sqlite3_channel.KookChannelSql()
                        insert_flag = chan_sql.insert_channel_ip_sub(current_channel, args[0])
                        if insert_flag:
                            await msg.reply(f":green_square: 服务器查询({args[0]}) 插入成功")
                        else:
                            await msg.reply(f":red_square: 服务器查询({args[0]}) 插入失败，请联系管理员")

            except Exception as e:
                logging.exception(e, exc_info=True)
                await msg.reply("发生了一些未知错误，请联系开发者解决。")

