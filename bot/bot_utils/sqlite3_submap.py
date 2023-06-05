import logging
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

from khl import PublicChannel

SQL = Path() / "data" / "server.db"

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DatabaseUserSub(object):
    ID: int
    sub_from_guild_id: str
    sub_from_channel_id: str
    sub_from_channel_name: str
    user_id: str
    sub_time: str
    sub_map_name: str


class KookUserSubSql(object):
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
            conn.execute('''create table user_sub
(
    ID           integer
        constraint user_sub_pk
            primary key autoincrement,
    sub_from_guild_id     text,
    sub_from_channel_id   text,
    sub_from_channel_name text,
    user_id      text,
    sub_time     text,
    sub_map_name text
);''')
        except sqlite3.OperationalError:
            pass
        except Exception as e:
            logger.exception(e, exc_info=True)

    def insert_user_sub_map(self, channel: PublicChannel, user_id: str, sub_map_name: str):
        try:
            with self.conn() as conn:
                is_db_exist = conn.execute(f"select * from user_sub "
                                           f"where user_id = ? and sub_map_name = ?",
                                           (user_id, sub_map_name)).fetchall()
                if any(is_db_exist):
                    logger.info(f"{user_id, sub_map_name} already existed.")
                    return False
                insert_time = time.strftime('%Y-%m-%dT%H:%M:%S')
                insert_content = (channel.guild_id,
                                  channel.id,
                                  channel.name,
                                  user_id,
                                  insert_time,
                                  sub_map_name)
                conn.execute(f"insert into user_sub values (NULL,?,?,?,?,?,?)", insert_content)
                conn.commit()
                logger.debug(f"user sub ({user_id}:{sub_map_name}) insert info table successfully.")
                return True
        except Exception as e:
            logger.exception(e, exc_info=True)
            return False

    def delete_user_sub_map(self, user_id: str, sub_map_name: str):
        try:
            logger.debug(f"Deleting row by {user_id}, {sub_map_name}...")
            with self.conn() as conn:
                result = conn.execute(f"delete from user_sub where user_id = ? and sub_map_name = ?",
                                      (user_id, sub_map_name))
                conn.commit()
                conn.execute(f"VACUUM")
                return result.rowcount
        except Exception as e:
            logger.exception(e, exc_info=True)

    def get_user_list_by_sub_map(self, sub_map_name: str):
        try:
            logger.debug(f"Query info by{sub_map_name}.")
            with self.conn() as conn:
                result = conn.execute(f"select distinct * from user_sub "
                                      f"where sub_map_name like ? collate nocase", (sub_map_name,)).fetchall()
                return result
        except Exception as e:
            logger.exception(e, exc_info=True)

    def get_all_user_sub_map_by_user_id(self, user_id: str):
        try:
            logger.debug(f"Query info by{user_id}.")
            with self.conn() as conn:
                result = conn.execute(f"select distinct * from user_sub "
                                      f"where user_id = ?", (user_id,)).fetchall()
                return result
        except Exception as e:
            logger.exception(e, exc_info=True)


@dataclass(frozen=True)
class DatabaseServerTrack(object):
    ID: str
    add_time: str
    ip_and_port: str
    server_name: str
    last_map_name: str


class ServerTrackSql(object):
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
            conn.execute('''create table server_track
(
    ID           integer
        constraint server_track_pk
            primary key autoincrement,
    add_time     text,
    ip_and_port text,
    server_name text,
    last_map_name text default 'map_name'
);''')
        except sqlite3.OperationalError:
            pass
        except Exception as e:
            logger.exception(e, exc_info=True)

    def insert_server_track(self, ip_and_port: str, server_name: str):
        try:
            with self.conn() as conn:
                is_db_exist = conn.execute(f"select * from server_track "
                                           f"where ip_and_port = ? and server_name = ?",
                                           (ip_and_port, server_name)).fetchall()
                if any(is_db_exist):
                    logger.info(f"{ip_and_port, server_name} already existed.")
                    return False
                insert_time = time.strftime('%Y-%m-%dT%H:%M:%S')
                insert_content = (insert_time,
                                  ip_and_port,
                                  server_name,
                                  "map_name")
                conn.execute(f"insert into server_track values (NULL,?,?,?,?)", insert_content)
                conn.commit()
                logger.debug(f"server track ({ip_and_port}:{server_name}) insert info table successfully.")
                return True
        except Exception as e:
            logger.exception(e, exc_info=True)
            return False

    def delete_server_track(self, ip_and_port: str):
        try:
            logger.debug(f"Deleting row by {ip_and_port}...")
            with self.conn() as conn:
                result = conn.execute(f"delete from server_track where ip_and_port = ?",
                                      (ip_and_port,))
                conn.commit()
                conn.execute(f"VACUUM")
                return result.rowcount
        except Exception as e:
            logger.exception(e, exc_info=True)

    def get_all_server_track(self) -> list[DatabaseServerTrack]:
        try:
            logger.debug(f"Query all track info.")
            with self.conn() as conn:
                result_rows = conn.execute(f"select distinct * from server_track").fetchall()
                result = []
                if any(result_rows):
                    for row in result_rows:
                        result.append(DatabaseServerTrack(*row))
                return result
        except Exception as e:
            logger.exception(e, exc_info=True)

    def get_track_info_by_ip_and_port(self, ip_and_port: str) -> DatabaseServerTrack:
        try:
            logger.debug(f"Query all track info.")
            with self.conn() as conn:
                result_row = conn.execute(f"select distinct * from server_track "
                                          f"where ip_and_port like ?", (ip_and_port,)).fetchone()
                result = DatabaseServerTrack(*result_row)
                return result
        except Exception as e:
            logger.exception(e, exc_info=True)

    def update_track_info_by_ip_and_port(self, ip_and_port: str, map_name: str):
        try:
            logger.debug(f"Updating {ip_and_port} last push map by {map_name}...")
            with self.conn() as conn:
                result = conn.execute(f"update server_track set last_map_name = ? "
                                      f"where ip_and_port = ?",
                                      (map_name, ip_and_port))
                conn.commit()
                logger.debug(f"Successfully update {result.rowcount} row")
                return result.rowcount
        except Exception as e:
            logger.exception(e, exc_info=True)
