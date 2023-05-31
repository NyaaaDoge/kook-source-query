from khl.card import CardMessage, Card, Module, Element, Types
from a2s.info import SourceInfo
from bot.bot_apis.map_img import load_cached_map_list, search_map


def query_server_result_card_msg(server_info: SourceInfo,
                                 map_img=True, show_ip=False) -> CardMessage:
    map_list = load_cached_map_list()
    card_msg = CardMessage()
    server_player_info = f"{server_info.player_count} / {server_info.max_players}"
    if isinstance(server_info.ping, float):
        server_ping = f"{round(server_info.ping * 1000)} ms"
    else:
        server_ping = "N/A"
    card = Card(theme=Types.Theme.INFO)
    card.append(Module.Header(f"{server_info.game} 服务器查询"))
    card.append(Module.Divider())
    # 没上锁的描述
    if not server_info.password_protected:
        card.append(Module.Section(Element.Text(f"(ins)**{server_info.server_name}**(ins)\n"
                                                f"地图：{server_info.map_name}\n"
                                                f"玩家：{server_player_info}  延迟：{server_ping}")))
    # 上锁的描述
    else:
        card.append(Module.Section(Element.Text(f"(ins)**{server_info.server_name}**(ins)\n"
                                                f"地图：{server_info.map_name}\n"
                                                f"玩家：{server_player_info}  延迟：{server_ping} :lock:")))
    if show_ip:
        card.append(Module.Section(Element.Text(f"{server_info.ip_addr}")))
    if map_img:
        # 地图图片预览项目地址 https://github.com/NewPage-Community/csgo-map-images
        search_result = search_map(server_info.map_name, map_list)
        if search_result:
            img_src = search_result['medium']
            card.append(Module.Container(Element.Image(src=img_src, circle=False, size=Types.Size.LG)))

    card_msg.append(card)
    return card_msg


def query_server_results_batch_card_msg(server_info_list: list,
                                        map_img=True, show_ip=False) -> CardMessage:
    map_list = load_cached_map_list()
    card_msg = CardMessage()
    card = Card(theme=Types.Theme.INFO)
    if any(server_info_list):
        card.append(Module.Header(f"{server_info_list[0].game} 服务器查询"))
        card.append(Module.Divider())
    for server_info in server_info_list[:12]:
        server_player_info = f"{server_info.player_count} / {server_info.max_players}"
        if isinstance(server_info.ping, float):
            server_ping = f"{round(server_info.ping * 1000)} ms"
        else:
            server_ping = "N/A"
        # 没上锁的描述
        if not server_info.password_protected:
            card.append(Module.Section(Element.Text(f"(ins)**{server_info.server_name}**(ins)\n"
                                                    f"地图：{server_info.map_name}\n"
                                                    f"玩家：{server_player_info}  延迟：{server_ping}")))
        # 上锁的描述
        else:
            card.append(Module.Section(Element.Text(f"(ins)**{server_info.server_name}**(ins)\n"
                                                    f"地图：{server_info.map_name}\n"
                                                    f"玩家：{server_player_info}  延迟：{server_ping} :lock:")))
        if show_ip:
            card.append(Module.Section(Element.Text(f"{server_info.ip_addr}")))
        if map_img:
            # 地图图片预览项目地址 https://github.com/NewPage-Community/csgo-map-images
            search_result = search_map(server_info.map_name, map_list)
            if search_result:
                img_src = search_result['medium']
                card.append(Module.Container(Element.Image(src=img_src, circle=False, size=Types.Size.LG)))
    card_msg.append(card)
    return card_msg
