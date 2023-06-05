import logging
import time
from typing import Union
from khl.card import CardMessage, Card, Module, Element, Types
from a2s.info import SourceInfo, GoldSrcInfo
from bot.bot_apis.map_img import load_cached_map_list, search_map
from bot.bot_apis.my_query_api import QueryFailInfo
from bot.bot_utils import utils_log

logger = logging.getLogger(__name__)
card_logger = utils_log.BotLogger(logger)


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
        card.append(Module.Section(Element.Text(f"查询失败\n请确认查询的服务器是起源或者金源游戏服务器。")))
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
            card.append(Module.Section(Element.Text(f"{server_info.ip_and_port} 查询失败")))
            continue
        elif server_info is None:
            card.append(Module.Section(Element.Text(f"查询失败\n请确认查询的服务器是起源或者金源游戏服务器。")))
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
