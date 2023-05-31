import logging
from bot.bot_configs import config_bot, config_global
from bot.bot_commands import reg_cmds
from bot.bot_tasks import my_tasks
from khl import Bot

logger = logging.getLogger("Main")
global_settings = config_global.settings
bot_settings = config_bot.settings

# 日志信息
logging.basicConfig(level=global_settings.log_level, format='%(asctime)s - %(name)s - %(levelname)s -%(message)s')
logger.info(f"Bot version {global_settings.BOT_VERSION}")

bot = Bot(token=bot_settings.token)

reg_cmds.register_cmds(bot)
my_tasks.register_tasks(bot)

if __name__ == '__main__':
    bot.run()
