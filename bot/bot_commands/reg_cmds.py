from khl import Bot, Message
from bot.bot_commands import cmd_basic, cmd_query, cmd_channel


def register_cmds(bot: Bot):
    cmd_basic.reg_basic_cmd(bot)
    cmd_query.reg_query_cmd(bot)
    cmd_channel.reg_channel_cmd(bot)
