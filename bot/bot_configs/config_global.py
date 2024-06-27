import logging
from typing import List


class GlobalSettings(object):
    log_level = logging.INFO
    BOT_VERSION: str = 'v0.1.1'

    bot_guild_black_list: List[str] = []
    bot_developer_list: List[str] = [""]
    source_server_query_timeout: int = 10
    channel_query_max_number: int = 15
    guild_server_query_max_number: int = 30
    server_monitor_interval_minutes: int = 5


settings = GlobalSettings()
