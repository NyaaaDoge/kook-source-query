import logging
import re

from khl import Bot

logger = logging.getLogger(__name__)


class BotUtils(object):
    @staticmethod
    def validate_ip_port(string):
        pattern = r'^((\d{1,3}\.){3}\d{1,3}|[A-Za-z0-9.-]+):[0-9]{1,5}$'
        if re.match(pattern, string):
            return True
        else:
            return False

    @staticmethod
    async def has_admin_and_manage(bot: Bot, user_id, guild_id):
        try:
            guild = await bot.client.fetch_guild(guild_id)
            user_roles = (await guild.fetch_user(user_id)).roles
            guild_roles = await (await bot.client.fetch_guild(guild_id)).fetch_roles()
            # 遍历服务器身分组
            for role in guild_roles:
                # 查看当前遍历到的身分组是否在用户身分组内且是否有管理员权限
                if role.id in user_roles and role.has_permission(0) or role.has_permission(5):
                    return True
            # 由于腐竹可能没给自己上身分组，但是依旧拥有管理员权限
            if user_id == guild.master_id:
                return True
            return False
        except Exception as e:
            logger.exception(f"Failed to get permissions for U:{user_id},G:{guild_id}). {e}", exc_info=False)
            return False
