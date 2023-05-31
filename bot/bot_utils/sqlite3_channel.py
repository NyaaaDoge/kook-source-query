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
class DatabaseChannel(object):
    ID: int
    guild_id: str
    channel_id: str
    channel_name: str
    sub_time: str
    ip_subscription: str
    show_ip: int


class KookChannelSql(object):
    def __init__(self):
        if not SQL.exists():
            SQL.parent.mkdir(parents=True, exist_ok=True)
        self.make_table()

    @staticmethod
    def conn():
        with sqlite3.connect(SQL) as conn:
            return conn

    def close_conn(self):
        return self.conn().close()

    def make_table(self):
        try:
            conn = self.conn()
            conn.execute('''create table kook_channel(
    ID              integer
        constraint kook_channel_pk
            primary key autoincrement,
    guild_id        text,
    channel_id      text,
    channel_name    text,
    sub_time        text,
    ip_subscription text,
    show_ip         integer default 0
);''')
        except sqlite3.OperationalError:
            pass
        except Exception as e:
            logger.exception(e, exc_info=True)

    def insert_channel_ip_sub(self, channel: PublicChannel, ip_addr: str):
        try:
            with self.conn() as conn:
                is_db_exist = conn.execute(f"select * from kook_channel "
                                           f"where channel_id = ? and ip_subscription = ?",
                                           (channel.id, ip_addr)).fetchall()
                if any(is_db_exist):
                    logger.info(f"{channel.id, ip_addr} already existed.")
                    return False
                insert_time = time.strftime('%Y-%m-%dT%H:%M:%S')
                insert_content = (channel.guild_id,
                                  channel.id,
                                  channel.name,
                                  insert_time,
                                  ip_addr,
                                  0)
                conn.execute(f"insert into kook_channel values (NULL,?,?,?,?,?,?)", insert_content)
                conn.commit()
                logger.debug(f"channel({channel.id}:{channel.name}) insert info table successfully.")
                return True
        except Exception as e:
            logger.exception(e, exc_info=True)
            return False

    def delete_channel_ip_sub_by_ip(self, channel_id, ip_addr):
        try:
            logger.debug(f"Deleting row by {channel_id}, {ip_addr}...")
            with self.conn() as conn:
                result = conn.execute(f"delete from kook_channel where channel_id = ? and ip_subscription = ?",
                                      (channel_id, ip_addr))
                return result.rowcount
        except Exception as e:
            logger.exception(e, exc_info=True)

    def update_channel_show_ip_option(self, flag, channel_id):
        try:
            logger.debug(f"Updating channel show ip flag by {channel_id}...")
            with self.conn() as conn:
                result = conn.execute(f"update kook_channel set show_ip = ? "
                                      f"where channel_id = ?", (flag, channel_id))
                conn.commit()
                return result.rowcount
        except Exception as e:
            logger.exception(e, exc_info=True)

    def get_all_sub_ip_by_channel_id(self, channel_id):
        try:
            logger.debug(f"Query info by{channel_id}.")
            with self.conn() as conn:
                result = conn.execute(f"select distinct * from kook_channel "
                                      f"where channel_id = ?", (channel_id,)).fetchall()
                return result
        except Exception as e:
            logger.exception(e, exc_info=True)

    def get_all_sub_ip_by_guild_id(self, guild_id):
        try:
            logger.debug(f"Query info by{guild_id}.")
            with self.conn() as conn:
                result = conn.execute(f"select distinct * from kook_channel "
                                      f"where guild_id = ?", (guild_id,)).fetchall()
                return result
        except Exception as e:
            logger.exception(e, exc_info=True)
