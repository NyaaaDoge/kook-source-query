from khl import Bot
from bot.bot_commands import cmd_basic, cmd_query, cmd_channel, cmd_nofify


def register_cmds(bot: Bot):
    cmd_basic.reg_basic_cmd(bot)
    cmd_query.reg_query_cmd(bot)
    cmd_channel.reg_channel_cmd(bot)
    cmd_nofify.reg_notify_cmd(bot)
