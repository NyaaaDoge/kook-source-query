import logging
import re
import time
from datetime import timedelta
from typing import Union
from khl.card import CardMessage, Card, Module, Element, Types, Color
from a2s.info import SourceInfo, GoldSrcInfo
from a2s.players import Player
from bot.bot_apis.map_img import load_cached_map_list, search_map
from bot.bot_apis.my_query_api import QueryFailInfo
from bot.bot_configs import config_global
from bot.bot_utils import utils_log

global_settings = config_global.settings
logger = logging.getLogger(__name__)
card_logger = utils_log.BotLogger(logger)
POPULARITY_VERY_HOT_RATIO = 0.80
POPULARITY_HOT_RATIO = 0.60
POPULARITY_WARM_RATIO = 0.40
VERY_HOT_COLOR = "#FF0000"
HOT_COLOR = "#DF4736"
WARM_COLOR = "#EC897d"

STEAM_CONNECT_URL = f"https://gitee.com/link?target="


def get_steam_connect_browser_protocol(ip_with_port, password=None, game_appid: int = None):
    # steam://connect/<IP>[:<port>][/<password>] detect the game and connect the server. dns not work here
    pattern = r'^((\d{1,3}\.){3}\d{1,3}):([0-9]{1,5})$'
    match = re.match(pattern, ip_with_port)
    if match:
        # 验证每个数字部分在0到255之间
        octets = match.group(1).split('.')
        for octet in octets:
            if not (0 <= int(octet) <= 255):
                return False
        # 验证端口在0到65535之间
        port = int(match.group(3))
        if 0 <= port <= 65535:
            protocol = f"steam://connect/{ip_with_port}"
            if password:
                protocol += f"/{password}"
            return protocol

    # 如果指定appid
    if game_appid:
        if game_appid == 730:
            protocol = f"steam://rungame/730/76561202255233023/+connect {ip_with_port}"
            if password:
                protocol += f"/{password}"
            return protocol


def help_card_msg():
    logger.debug(f"Build help card message")
    card_msg = CardMessage()
    card = Card(theme=Types.Theme.INFO)
    card.append(Module.Header(f"Sauce Query Bot 帮助文档"))
    card.append(Module.Context(f"版本: {global_settings.BOT_VERSION}"))
    card.append(Module.Divider())
    help_str = f"`/query ip [ip地址:端口号]` - 查询特定IP地址的起源/金源服务器信息" \
               "`/query server` - 查询该频道设置好的IP地址列表的服务器信息" \
               "`/notify map [map_name]` - 订阅特定地图，Bot监测到设定好的服务器（由bot管理员设置）有特定地图将会进行私信通知。" \
               "`/notify unsub [map_name]` - 取消订阅特定地图" \
               "`/notify list` - 查询当前订阅的地图列表" \
               "`/notify wipe` - 清除当前订阅的地图列表" \
               "`/config query [ip地址:端口号]` - 为当前频道设置添加要查询的IP地址" \
               "`/config delete [ip地址:端口号]` - 删除设置里面当前频道对应的IP地址" \
               "`/config showip [on/off]` - 为当前频道的查询设置显示/关闭IP地址结果" \
               "`/config showimg [on/off]` - 为当前频道的查询设置显示/关闭预览图片，关闭图片后可以有效提高查询速度" \
               "`/config` - 查看当前频道查询的设置信息和当前服务器的设置信息"
    card.append(Module.Section(Element.Text(help_str)))
    card.append(Module.Divider())
    bottom_str = "一个服务器最多设置30个IP地址查询，一个频道最多设置15个IP地址查询。如有更多需求请自行前往Github获取源码自行部署。" \
                 "小技巧：只要在频道发送消息里面有关键字“查”并且@机器人即可查询服务器信息。功能同`/query server`。如`@机器人 查`" \
                 "[本Github项目](https://github.com/NyaaaDoge/kook-source-query) 和 " \
                 "[预览图片项目](https://newpage-community.github.io/csgo-map-images/)，" \
                 "目前预览图片只有CSGO部分社区地图预览图片。" \
                 "觉得不错的话在 [Github页面](https://github.com/NyaaaDoge/kook-source-query) " \
                 "点个 star 吧！或者在 [爱发电](https://afdian.net/a/NyaaaDoge) 支持开发者。"
    card.append(Module.Context(Element.Text(bottom_str)))
    card_msg.append(card)
    return card_msg


def query_server_result_card_msg(server_info: Union[SourceInfo, GoldSrcInfo],
                                 map_img=True, show_ip=True, show_keywords=False) -> CardMessage:
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
    try:
        popular_ratio = server_info.player_count / server_info.max_players
    except ZeroDivisionError:
        popular_ratio = 0
    popularity_indicator = ""
    if popular_ratio >= POPULARITY_VERY_HOT_RATIO:
        popularity_indicator = ":fire::fire::fire: "
        server_player_info = f"(font){server_player_info}(font)[warning]"
        card.color = Color(hex_color=VERY_HOT_COLOR)
    elif popular_ratio >= POPULARITY_HOT_RATIO:
        popularity_indicator = ":fire::fire: "
        server_player_info = f"(font){server_player_info}(font)[pink]"
        card.color = Color(hex_color=HOT_COLOR)
    elif popular_ratio >= POPULARITY_WARM_RATIO:
        popularity_indicator = ":fire: "
        server_player_info = f"(font){server_player_info}(font)[success]"
        card.color = Color(hex_color=WARM_COLOR)
    if isinstance(server_info.ping, float):
        server_ping = f"{round(server_info.ping * 1000)} ms"
    else:
        server_ping = "N/A"
    card.append(Module.Header(f"{popularity_indicator}{server_info.server_name}"))
    card.append(Module.Divider())
    server_desc = f"(ins)**{server_info.game}**(ins)\n" \
                  f"地图：{server_info.map_name}\n" \
                  f"玩家：{server_player_info}  延迟：{server_ping}"
    if server_info.password_protected:
        server_desc += " :lock:"
    if show_ip:
        ip_port = server_info.__getattribute__('ip_and_port')
        protocol = get_steam_connect_browser_protocol(ip_port)
        if ip_addr_resolved := server_info.__getattribute__('resolved_ip_address'):
            protocol = get_steam_connect_browser_protocol(f"{ip_addr_resolved[0]}:{server_info.port}")
        if protocol:
            server_desc += f"\n[{ip_port}]({STEAM_CONNECT_URL}{protocol})"
        else:
            server_desc += f"\n{ip_port}"
    card.append(Module.Section(Element.Text(server_desc)))
    if map_img:
        # 地图图片预览项目地址 https://github.com/NewPage-Community/csgo-map-images
        search_result = search_map(server_info.map_name, map_list)
        if search_result:
            img_src = search_result['medium']
            card.append(Module.Container(Element.Image(src=img_src, circle=False, size=Types.Size.LG)))
    end_desc = f"查询于 {time.strftime('%H:%M')}"
    if server_info.version:
        end_desc += f" 版本号 {server_info.version}"
    if server_info.platform:
        end_desc += f" 平台 "
        if server_info.platform == 'l':
            end_desc += f"Linux"
        elif server_info.platform == 'w':
            end_desc += f"Windows"
        else:
            end_desc += f"{server_info.platform}"
    if show_keywords and server_info.keywords:
        end_desc += f"\n*{server_info.keywords}*"
    card.append(Module.Context(Element.Text(end_desc, type=Types.Text.KMD)))
    card_msg.append(card)
    logger.debug(f"Return card message for {server_info}")
    return card_msg


def query_server_results_batch_card_msg(server_info_list: list,
                                        map_img=True, show_ip=True) -> CardMessage:
    logger.debug(f"Build card message for {server_info_list}")
    map_list = load_cached_map_list()
    card_msg = CardMessage()
    card = Card(theme=Types.Theme.INFO)
    card.append(Module.Header(f"服务器查询结果"))
    card.append(Module.Divider())
    for server_info in server_info_list[:20]:
        if isinstance(server_info, QueryFailInfo):
            card.append(Module.Section(Element.Text(f"**(font){server_info.ip_and_port} 查询失败(font)[warning]**")))
            continue
        elif server_info is None:
            card.append(Module.Section(Element.Text(f"**(font)查询失败(font)[warning]**"
                                                    f"\n请确认查询的服务器是起源或者金源游戏服务器。")))
        server_player_info = f"{server_info.player_count} / {server_info.max_players}"
        try:
            popular_ratio = server_info.player_count / server_info.max_players
        except ZeroDivisionError:
            popular_ratio = 0
        popularity_indicator = ""
        if popular_ratio >= POPULARITY_VERY_HOT_RATIO:
            # popularity_indicator = ":fire::fire::fire: "
            server_player_info = f"(font){server_player_info}(font)[warning]"
        elif popular_ratio >= POPULARITY_HOT_RATIO:
            # popularity_indicator = ":fire::fire: "
            server_player_info = f"(font){server_player_info}(font)[pink]"
        elif popular_ratio >= POPULARITY_WARM_RATIO:
            # popularity_indicator = ":fire: "
            server_player_info = f"(font){server_player_info}(font)[success]"
        if isinstance(server_info.ping, float):
            server_ping = f"{round(server_info.ping * 1000)} ms"
        else:
            server_ping = "N/A"
        server_desc = f"(ins)**{popularity_indicator}{server_info.server_name}**(ins)\n" \
                      f"地图：{server_info.map_name}\n" \
                      f"玩家：{server_player_info}  延迟：{server_ping}"
        if server_info.password_protected:
            server_desc += " :lock:"
        if show_ip:
            ip_port = server_info.__getattribute__('ip_and_port')
            protocol = get_steam_connect_browser_protocol(ip_port)
            if ip_addr_resolved := server_info.__getattribute__('resolved_ip_address'):
                protocol = get_steam_connect_browser_protocol(f"{ip_addr_resolved[0]}:{server_info.port}")
            if protocol:
                server_desc += f"\n[{ip_port}]({STEAM_CONNECT_URL}{protocol})"
            else:
                server_desc += f"\n{ip_port}"
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


def query_server_player_list_card_msg(server_info: Union[SourceInfo, GoldSrcInfo], player_list: list[Player]):
    logger.debug(f"Build card message for {server_info},{player_list}")
    card_msg = CardMessage()
    card = Card(theme=Types.Theme.INFO)
    card.append(Module.Header(f"服务器玩家列表查询结果"))
    card.append(Module.Divider())
    if server_info is not None:
        server_player_info = f"{server_info.player_count} / {server_info.max_players}"
        server_desc = f"(ins)**{server_info.game}**(ins)\n" \
                      f"{server_info.server_name}\n" \
                      f"*地图：{server_info.map_name}\n" \
                      f"玩家：{server_player_info}*"
        card.append(Module.Section(Element.Text(server_desc)))
    if not any(player_list):
        card.append(Module.Section(Element.Text("该服务器没有任何玩家")))
        card_msg.append(card)
        return card_msg
    player_desc = "  游玩时长  |  玩家名称\n"
    for player in player_list:
        if not player.name:
            player.name = "Player"
        player_name_desc = rf"{player.name}"
        duration = timedelta(seconds=player.duration)
        # days = f"{duration.days}"
        # hours = f"{duration.seconds // 3600:02}"
        hours = f"{duration.days * 24 + duration.seconds // 3600:02}"
        minutes = f"{(duration.seconds % 3600) // 60:02}"
        seconds = f"{duration.seconds % 60:02}"
        # if int(days) > 0:
        #     time_desc = f"{days}天 {hours}时 {minutes}分"
        if int(hours) > 0:
            time_desc = f"{hours}时 {minutes}分"
        elif int(minutes) > 0:
            time_desc = f"{minutes}分 {seconds}秒"
        else:
            time_desc = f"00分 {seconds}秒"
        player_duration_desc = f"{time_desc}"
        player_desc += f"{player_duration_desc}  |  {player_name_desc}"
        # if player.score:
        #     player_desc += f"  |  {player.score}"
        player_desc += "\n"
    card.append(Module.Section(Element.Text(player_desc, type=Types.Text.PLAIN)))
    end_desc = f"查询于 {time.strftime('%H:%M')}"
    if server_info.version:
        end_desc += f" 版本号 {server_info.version}"
    card.append(Module.Context(Element.Text(end_desc)))
    card_msg.append(card)
    logger.debug(f"Return card message for {player_list}")
    return card_msg


def player_notify_map_list_card_msg(kook_id: str, map_list: list[str]):
    logger.debug(f"Build card message for{map_list}")
    card_msg = CardMessage()
    card = Card(theme=Types.Theme.INFO)
    card.append(Module.Header(f":scroll: 玩家地图订阅列表"))
    card.append(Module.Divider())
    card.append(Module.Context(Element.Text(f"(met){kook_id}(met) 订阅了 **{len(map_list)}** 张地图",
                                            type=Types.Text.KMD)))
    if len(map_list) == 0:
        card.append(Module.Section(Element.Text("当前没有订阅任何地图")))
        card_msg.append(card)
        return card_msg
    # 分组
    chunk_size = 100
    map_list_chunks = []
    for index in range(0, len(map_list), chunk_size):
        map_chunk = map_list[index: index + chunk_size]
        map_list_chunks.append(map_chunk)
    for chunk_list in map_list_chunks:
        map_name_desc = ""
        for map_name in chunk_list:
            map_name_desc += f"{map_name}\n"
        card.append(Module.Section(Element.Text(map_name_desc)))
    card_msg.append(card)
    return card_msg
