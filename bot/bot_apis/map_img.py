import aiohttp
import json
from pathlib import Path

MAPS_JSON = "https://newpage-community.github.io/csgo-map-images/maps.json"


async def fetch_map_list():
    async with aiohttp.ClientSession() as session:
        async with session.get(MAPS_JSON) as response:
            if response.status == 200:
                return await response.json()
            else:
                return None


def cache_map_list(map_list):
    json_path = Path() / "data" / "map_list.json"
    with open(json_path, 'w') as file:
        json.dump(map_list, file)


def load_cached_map_list():
    try:
        json_path = Path() / "data" / "map_list.json"
        with open(json_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return None


def search_map(map_name, map_list):
    for map_data in map_list:
        if map_data['name'].lower() == map_name.lower():
            return map_data
    return None
