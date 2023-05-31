from typing import List


class GlobalSettings(object):
    log_level: str = "INFO"
    BOT_VERSION: str = 'v0.0.1'

    bot_guild_black_list: List[str] = []
    bot_developer_list: List[str] = [""]
    source_server_query_timeout: int = 10


settings = GlobalSettings()
