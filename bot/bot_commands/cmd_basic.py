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

    @bot.command(name="help", case_sensitive=False)
    async def cmd_help(msg: Message):
        cmd_logger.logging_msg(msg)
        await msg.reply(f"""Sauce Query Bot{global_settings.BOT_VERSION} 帮助文档：
`/query ip [ip地址:端口号]` - 查询特定IP地址的起源/金源服务器信息
`/query server` - 查询该频道设置好的IP地址列表的服务器信息
`/config query [ip地址:端口号]` - 为当前频道设置添加要查询的IP地址
`/config delete [ip地址:端口号]` - 删除设置里面当前频道对应的IP地址
`/config showip [on/off]` - 为当前频道的查询设置显示/关闭IP地址结果
`/config showimg [on/off]` - 为当前频道的查询设置显示/关闭预览图片，关闭图片后可以有效提高查询速度。
`/config` - 查看当前频道查询的设置信息和当前服务器的设置信息
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
                    await msg.reply("`/admin update maplist`", type=MessageTypes.KMD)

                elif command in ['update']:
                    if not any(args):
                        await msg.reply("`/admin update maplist`", type=MessageTypes.KMD)

                    elif args[0] in ['maplist']:
                        await my_tasks.task_update_map_list_json()
                        await msg.reply("执行更新地图列表json完成。", type=MessageTypes.KMD)

                elif command in ['leave']:
                    if not any(args):
                        await msg.reply("用法 `.admin leave {gid}`", type=MessageTypes.KMD)
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

            except Exception as e:
                logging.error(e, exc_info=True)
                await msg.reply(f"{e}")
