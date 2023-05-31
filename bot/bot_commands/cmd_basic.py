import logging

from bot.bot_configs import config_global
from bot.bot_utils.utils_log import BotLogger
from bot.bot_tasks import my_tasks
from khl import Bot, Message, MessageTypes

global_settings = config_global.settings
logger = logging.getLogger(__name__)
cmd_logger = BotLogger(logger)


def reg_basic_cmd(bot: Bot):
    @bot.command(name="hellosrc", case_sensitive=False)
    async def cmd_hello(msg: Message):
        cmd_logger.logging_msg(msg)
        await msg.reply("有什么想查的服务器？")

    @bot.command(name='admin')
    async def admin(msg: Message, command: str = None, *args):
        cmd_logger.logging_msg(msg)
        if msg.author.id in global_settings.bot_developer_list:
            try:
                if command is None:
                    await msg.reply("`/admin update maplist`", type=MessageTypes.KMD)

                elif command in ['update']:
                    if not any(args):
                        await msg.reply("`/admin update maplist`", type=MessageTypes.KMD)

                    elif args[0] in ['maplist']:
                        await my_tasks.task_update_map_list_json()
                        await msg.reply("执行更新地图列表json完成。", type=MessageTypes.KMD)

            except Exception as e:
                logging.error(e, exc_info=True)
                await msg.reply(f"{e}")
