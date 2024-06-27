import asyncio
import logging
from khl import Bot, MessageTypes, HTTPRequester
from bot.bot_apis import map_img, my_query_api
from bot.bot_utils.utils_log import BotLogger
from bot.bot_cards_message.cards_msg_server import query_server_result_card_msg
from bot.bot_utils import sqlite3_submap
from bot.bot_configs import config_bot, config_global

bot_settings = config_bot.settings
glob_settings = config_global.settings
logger = logging.getLogger(__name__)
task_logger = BotLogger(logger)
# task_logger.create_log_file_by_rotate_handler("bot_tasks.log")


def register_tasks(bot: Bot):
    # 更新地图图片列表
    @bot.task.add_interval(hours=6)
    async def update_map_img_list():
        try:
            await task_update_map_list_json()
        except Exception as e:
            logger.exception(e)

    # 监控服务器地图信息
    @bot.task.add_interval(minutes=glob_settings.server_monitor_interval_minutes)
    async def track_server_map():
        try:
            await task_track_server_map_info(bot)
        except Exception as e:
            logger.exception(e)


async def task_update_map_list_json():
    logger.info(f"Task updating map list json...")
    try:
        json_data = await map_img.fetch_map_list()
        map_img.cache_map_list(json_data)
    except Exception as e:
        logger.exception(e)
    logger.info(f"Task updating map list json done.")


async def task_track_server_map_info(bot: Bot):
    logger.info(f"Task tracking server map info...")
    try:
        # 先从数据库从取出IP
        sub_sql = sqlite3_submap.ServerTrackSql()
        server_list = sub_sql.get_all_server_track()
        if not any(server_list):
            logger.info(f"No server to be tracked.")
            return
        query_tasks_list = []
        # 要监控的每个服务器，创建任务列表
        for server in server_list:
            # 使用异步任务列表同时请求
            query_tasks_list.append(asyncio.create_task(update_server_and_get_notify_user(server.ip_and_port)))
        # 执行更新任务
        notify_list = await asyncio.gather(*query_tasks_list)
        # 对每个需要推送的服务器进行逐一推送
        for server in notify_list:
            if type(server) is not dict:
                continue
            data = dict(server)
            for server_info, user_list in data.items():
                # 逐一推送给用户
                for user in user_list:
                    try:
                        # 获取要私信的用户
                        user = await bot.client.fetch_user(user.user_id)
                        logger.info(f"Notify {user.id} for {server_info.map_name}.")
                        try:
                            # 首次私信通知发送图片
                            card_msg = query_server_result_card_msg(server_info, show_ip=True)
                            await user.send(type=MessageTypes.CARD, content=card_msg)
                        except HTTPRequester.APIRequestFailed as failed:
                            logger.info(f"Failed to send map img. Sending info without img...")
                            # 如果遇到 40000 代码再创建不发送图片的任务。如果是卡片消息创建失败，首先尝试发送没有图片的卡片消息。
                            if failed.err_code == 40000:
                                card_msg = query_server_result_card_msg(server_info,
                                                                        map_img=False, show_ip=True)
                                await user.send(type=MessageTypes.CARD, content=card_msg)
                    except Exception as e:
                        logger.exception(f"exception user: {user.user_id}. {e}")
    except Exception as e:
        logger.exception(e)
    logger.info(f"Task tracking server map info done.")


async def update_server_and_get_notify_user(ip_addr):
    try:
        if ip_addr is None:
            return
        query_info = await my_query_api.MyQueryApi.get_server_info(ip_addr)
        if query_info is None:
            return
        sub_sql = sqlite3_submap.ServerTrackSql()
        user_sub_sql = sqlite3_submap.KookUserSubSql()
        db_track_info = sub_sql.get_track_info_by_ip_and_port(query_info.__getattribute__("ip_and_port"))
        # 如果当前查询的地图与上次推送的地图名一致，认为当前服务器仍在该会话中，直接跳过更新
        if query_info.map_name.lower() == db_track_info.last_map_name.lower():
            return
        # 更新推送地图数据
        sub_sql.update_track_info_by_ip_and_port(query_info.__getattribute__("ip_and_port"),
                                                 query_info.map_name)
        # 获取订阅地图的用户
        notify_user_list = user_sub_sql.get_user_list_by_sub_map(query_info.map_name)
        # 如果有用户订阅地图，返回查询信息和用户列表
        if any(notify_user_list):
            # 为接口返回的user_list数据封装成DatabaseUserSub类
            sealed_data_list = []
            for db_user_info in notify_user_list:
                sealed_data_list.append(sqlite3_submap.DatabaseUserSub(*db_user_info))
            return {query_info: sealed_data_list}

    except Exception as e:
        logger.exception(e)


async def old_task_track_server_map_info(bot: Bot):
    logger.info(f"Old task tracking server map info...")
    try:
        # 先从数据库从取出IP
        sub_sql = sqlite3_submap.ServerTrackSql()
        user_sub_sql = sqlite3_submap.KookUserSubSql()
        server_list = sub_sql.get_all_server_track()
        query_api = my_query_api.MyQueryApi()
        if not any(server_list):
            logger.info(f"No server to be tracked.")
            return
        # 要监控的每个服务器
        for server in server_list:
            query_info = await query_api.get_server_info(server.ip_and_port)
            sub_sql.get_all_server_track()
            db_track_info = sub_sql.get_track_info_by_ip_and_port(server.ip_and_port)
            # 无服务器查询信息跳过
            if query_info is None:
                continue
            # 更新推送地图数据
            sub_sql.update_track_info_by_ip_and_port(server.ip_and_port,
                                                     query_info.map_name)
            # 如果当前查询的地图与上次推送的地图名一致，认为当前服务器仍在该会话中，直接跳过推送
            if query_info.map_name.lower() == db_track_info.last_map_name.lower():
                continue
            notify_user_list = user_sub_sql.get_user_list_by_sub_map(query_info.map_name)
            # 无用户订阅地图跳过
            if not any(notify_user_list):
                continue
            for user_info in notify_user_list:
                db_user_info = sqlite3_submap.DatabaseUserSub(*user_info)
                try:
                    # 获取要私信的用户
                    user = await bot.client.fetch_user(db_user_info.user_id)
                    logger.info(f"Notify {user.id} for {query_info.map_name}.")
                    try:
                        # 首次私信通知发送图片
                        card_msg = query_server_result_card_msg(query_info, show_ip=True)
                        await user.send(type=MessageTypes.CARD, content=card_msg)
                    except HTTPRequester.APIRequestFailed as failed:
                        try:
                            logger.info(f"Failed to send map img. Sending info without img...")
                            # 如果遇到 40000 代码再创建不发送图片的任务。如果是卡片消息创建失败，首先尝试发送没有图片的卡片消息。
                            if failed.err_code == 40000:
                                card_msg = query_server_result_card_msg(query_info,
                                                                        map_img=False, show_ip=True)
                                await user.send(type=MessageTypes.CARD, content=card_msg)
                        except Exception as e:
                            logger.exception(f"exception {e}")

                except Exception as e:
                    logger.exception(f"exception user: {db_user_info.user_id}. {e}")
    except Exception as e:
        logger.exception(e)
    logger.info(f"Old task tracking server map info done.")
