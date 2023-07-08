import logging
import time
from datetime import timedelta
from typing import Union
from khl.card import CardMessage, Card, Module, Element, Types, Struct
from a2s.info import SourceInfo, GoldSrcInfo
from a2s.players import Player
from bot.bot_apis.map_img import load_cached_map_list, search_map
from bot.bot_apis.my_query_api import QueryFailInfo
from bot.bot_configs import config_global
from bot.bot_utils import utils_log

global_settings = config_global.settings
logger = logging.getLogger(__name__)
card_logger = utils_log.BotLogger(logger)


def help_card_msg():
    logger.debug(f"Build help card message")
    card_msg = CardMessage()
    card = Card(theme=Types.Theme.INFO)
    card.append(Module.Header(f"Sauce Query Bot 帮助文档"))
    card.append(Module.Context(f"版本: {global_settings.BOT_VERSION}"))
    card.append(Module.Divider())
    help_str = f"""`/query ip [ip地址:端口号]` - 查询特定IP地址的起源/金源服务器信息
`/query server` - 查询该频道设置好的IP地址列表的服务器信息
`/notify map [map_name]` - 订阅特定地图，Bot监测到设定好的服务器（由bot管理员设置）有特定地图将会进行私信通知。
`/notify unsub [map_name]` - 取消订阅特定地图
`/notify list` - 查询当前订阅的地图列表
`/notify wipe` - 清除当前订阅的地图列表
`/config query [ip地址:端口号]` - 为当前频道设置添加要查询的IP地址
`/config delete [ip地址:端口号]` - 删除设置里面当前频道对应的IP地址
`/config showip [on/off]` - 为当前频道的查询设置显示/关闭IP地址结果
`/config showimg [on/off]` - 为当前频道的查询设置显示/关闭预览图片，关闭图片后可以有效提高查询速度
`/config` - 查看当前频道查询的设置信息和当前服务器的设置信息
"""
    card.append(Module.Section(Element.Text(help_str)))
    card.append(Module.Divider())
    bottom_str = """一个服务器最多设置30个IP地址查询，一个频道最多设置15个IP地址查询。如有更多需求请自行前往Github获取源码自行部署。
小技巧：只要在频道发送消息里面有关键字“查”并且@机器人即可查询服务器信息。功能同`/query server`。如`@机器人 查`
[本Github项目](https://github.com/NyaaaDoge/kook-source-query) 和 [预览图片项目](https://newpage-community.github.io/csgo-map-images/)，目前预览图片只有CSGO部分社区地图预览图片。
觉得不错的话在 [Github页面](https://github.com/NyaaaDoge/kook-source-query) 点个 star 吧！或者在 [爱发电](https://afdian.net/a/NyaaaDoge) 支持开发者。"""
    card.append(Module.Context(Element.Text(bottom_str)))
    card_msg.append(card)
    return card_msg


def query_server_result_card_msg(server_info: Union[SourceInfo, GoldSrcInfo],
                                 map_img=True, show_ip=False) -> CardMessage:
    logger.debug(f"Build card message for{server_info}")
    map_list = load_cached_map_list()
    card_msg = CardMessage()
    card = Card(theme=Types.Theme.INFO)
    if isinstance(server_info, QueryFailInfo):
        card.append(Module.Section(Element.Text(f"{server_info.ip_and_port} 查询失败")))
        card_msg.append(card)
        return card_msg
    elif server_info is None:
        card.append(Module.Section(Element.Text(f"**(font)查询失败(font)[warning]**\n"
                                                f"请确认查询的服务器是起源或者金源游戏服务器。\n"
                                                f"也有可能是服务器通信出错，无法查询，请稍后再试。")))
        card_msg.append(card)
        return card_msg
    server_player_info = f"{server_info.player_count} / {server_info.max_players}"
    if isinstance(server_info.ping, float):
        server_ping = f"{round(server_info.ping * 1000)} ms"
    else:
        server_ping = "N/A"
    card.append(Module.Header(f"{server_info.game}"))
    card.append(Module.Divider())
    server_desc = f"(ins)**{server_info.server_name}**(ins)\n" \
                  f"地图：{server_info.map_name}\n" \
                  f"玩家：{server_player_info}  延迟：{server_ping}"
    if server_info.password_protected:
        server_desc += " :lock:"
    if show_ip:
        server_desc += f"\n{server_info.ip_and_port}"
    card.append(Module.Section(Element.Text(server_desc)))
    if map_img:
        # 地图图片预览项目地址 https://github.com/NewPage-Community/csgo-map-images
        search_result = search_map(server_info.map_name, map_list)
        if search_result:
            img_src = search_result['medium']
            card.append(Module.Container(Element.Image(src=img_src, circle=False, size=Types.Size.LG)))
    card.append(Module.Context(Element.Text(f"查询于 {time.strftime('%H:%M')}")))
    card_msg.append(card)
    logger.debug(f"Return card message for {server_info}")
    return card_msg


def query_server_results_batch_card_msg(server_info_list: list,
                                        map_img=True, show_ip=False) -> CardMessage:
    logger.debug(f"Build card message for {server_info_list}")
    map_list = load_cached_map_list()
    card_msg = CardMessage()
    card = Card(theme=Types.Theme.INFO)
    card.append(Module.Header(f"服务器查询结果"))
    card.append(Module.Divider())
    for server_info in server_info_list[:15]:
        if isinstance(server_info, QueryFailInfo):
            card.append(Module.Section(Element.Text(f"**(font){server_info.ip_and_port} 查询失败(font)[warning]**")))
            continue
        elif server_info is None:
            card.append(Module.Section(Element.Text(f"**(font)查询失败(font)[warning]**"
                                                    f"\n请确认查询的服务器是起源或者金源游戏服务器。")))
        server_player_info = f"{server_info.player_count} / {server_info.max_players}"
        if isinstance(server_info.ping, float):
            server_ping = f"{round(server_info.ping * 1000)} ms"
        else:
            server_ping = "N/A"
        server_desc = f"(ins)**{server_info.server_name}**(ins)\n" \
                      f"地图：{server_info.map_name}\n" \
                      f"玩家：{server_player_info}  延迟：{server_ping}"
        if server_info.password_protected:
            server_desc += " :lock:"
        if show_ip:
            server_desc += f"\n{server_info.ip_and_port}"
        if map_img:
            # 地图图片预览项目地址 https://github.com/NewPage-Community/csgo-map-images
            search_result = search_map(server_info.map_name, map_list)
            if search_result:
                card.append(Module.Section(Element.Text(server_desc),
                                           Element.Image(search_result['thumb'], size=Types.Size.SM),
                                           Types.SectionMode.RIGHT))
            else:
                card.append(Module.Section(Element.Text(server_desc)))
        else:
            card.append(Module.Section(Element.Text(server_desc)))
    card.append(Module.Context(Element.Text(f"查询于 {time.strftime('%H:%M')}")))
    card_msg.append(card)
    logger.debug(f"Return card message for {server_info_list}")
    return card_msg


def query_server_player_list_card_msg(player_list: list[Player]):
    logger.debug(f"Build card message for {player_list}")
    card_msg = CardMessage()
    card = Card(theme=Types.Theme.INFO)
    card.append(Module.Header(f"服务器玩家列表查询结果"))
    card.append(Module.Divider())
    card.append(Module.Context(f"服务器玩家数量：{len(player_list)}"))
    if not any(player_list):
        card.append(Module.Section(Element.Text("该服务器没有任何玩家")))
    player_desc = ""
    for player in player_list:
        # if not any(player.name):
        #     continue
        player_name_desc = rf"{player.name}"
        player_score_desc = f"{player.score}"
        duration = timedelta(seconds=player.duration)
        days = duration.days
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        seconds = duration.seconds % 60
        if days > 0:
            time_desc = f"{days}天 {hours}时 {minutes}分 {seconds}秒"
        elif hours > 0:
            time_desc = f"{hours}时 {minutes}分 {seconds}秒"
        elif minutes > 0:
            time_desc = f"{minutes}分 {seconds}秒"
        else:
            time_desc = f"{seconds}秒"
        player_duration_desc = f"{time_desc}"
        player_desc += f"{player_name_desc}\n"
    card.append(Module.Section(Element.Text(player_desc)))
    card.append(Module.Context(Element.Text(f"查询于 {time.strftime('%H:%M')}")))
    card_msg.append(card)
    logger.debug(f"Return card message for {player_list}")
    return card_msg
