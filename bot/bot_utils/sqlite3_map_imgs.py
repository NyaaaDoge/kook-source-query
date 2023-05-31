import logging
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

from khl import PublicChannel

SQL = Path() / "data" / "server.db"

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DatabaseMapImg(object):
    map_name: str
    map_src: str
    map_full: str
    map_medium: str
    map_thumb: str
    map_webp: str
    map_webp_medium: str
    map_webp_thumb: str


    