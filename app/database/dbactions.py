from collections.abc import Callable, Generator
from contextlib import contextmanager
from logging import getLogger
import sqlite3
from typing import Any, Dict
from datetime import datetime
from termcolor import colored
from app.config.settings import get_settings
from app.utils.constants import DbAddStreamer, StreamerWithPid


log = getLogger(__name__)

config = get_settings()

DB_PATH = config.DB_PATH
DB_TABLES = config.DB_TABLES


@contextmanager
def connect() -> Generator[sqlite3.Cursor, Any, None]:
    with sqlite3.connect(DB_PATH) as connect:
        connect.execute("PRAGMA synchronous=OFF")
        connect.execute("PRAGMA  journal_mode=WAL")
        connect.execute("PRAGMA temp_store=memory")
        connect.execute("PRAGMA mmap_size=30000000000")
        connect.execute("PRAGMA page_size=32768")
        yield connect.cursor()


def db_init() -> None:
    if not DB_PATH.exists():
        log.info(colored("Creating database folder", "cyan"))
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    try:
        with connect() as cursor:
            with open(DB_TABLES, "r", encoding="utf-8") as file:
                cursor.executescript(file.read())
            log.info(colored("Database is active", "cyan"))

    except sqlite3.OperationalError as error:
        log.error(error)
    return None


# ***********************************
# * WRITE
# ***********************************


def db_update_pid(arg: StreamerWithPid):
    sql = "Update chaturbate SET pid=?, last_capture=?, last_broadcast=? WHERE streamer_name=?"
    args = (arg.pid, config.datetime, config.datetime, arg.streamer_name)
    if not _write_to_db(sql, args):
        log.error("Data write failed: %s ", (colored(f"{arg.streamer_name}", "red")))
        return
    log.info("capturing %s", (colored(arg.streamer_name, "green")))


def db_remove_pid(pid):
    sql = "UPDATE chaturbate SET pid=? WHERE pid=?"
    arg = (None, pid)
    if not _write_to_db(sql, arg):
        log.error(colored("Unable to reset the pid for the streamer", "red"))


def db_add_streamer(name_: str) -> tuple:
    today = datetime.now().replace(microsecond=0)
    sql = f"""INSERT INTO chaturbate (streamer_name, follow) 
        VALUES ( ?, ?) 
        ON CONFLICT (streamer_name) 
        DO UPDATE SET 
        follow='{today}' WHERE follow IS NULL"""
    args = (name_, today)
    write = _write_to_db(sql, args)
    query = query_db("cap_status", name_)

    if not write:
        log.error("Failed to add: %s", (colored(name_, "red")))
    return DbAddStreamer(bool(write), *query)


def num_online(data: int):
    sql = "INSERT INTO num_streamers (num_) VALUES (?)"
    args = (data,)
    write = _write_to_db(sql, args)
    if not write:
        log.error("Failed to add: %s", (colored("online streamers stat", "red")))
    return bool(write)


def _write_to_db(sql, arg) -> bool:
    try:
        with connect() as cursor:
            write = cursor.execute(sql, arg)
    except sqlite3.Error as error:
        print(error)
        log.error(error)
        write = None
    return bool(write)


def db_update_streamers(values: list):
    sql = """INSERT INTO chaturbate (streamer_name, followers, viewers, last_broadcast) 
        VALUES ( ?, ?, ?, ?)
        ON CONFLICT (streamer_name)
        DO UPDATE SET 
        followers=EXCLUDED.followers,
        viewers=EXCLUDED.viewers, 
        last_broadcast=DATETIME(EXCLUDED.last_broadcast, 'unixepoch', 'localtime'),
        most_viewers=MAX(most_viewers, EXCLUDED.viewers)
        """
    try:
        with connect() as cursor:
            write = cursor.executemany(sql, values)
    except sqlite3.Error as error:
        log.error(error)
        write = None
    finally:
        return bool(write)


# ************************************
# * query
# ************************************


def _db_cap_status(name_):
    return (
        "SELECT follow, block_date FROM chaturbate WHERE streamer_name=?",
        (name_,),
    )


def fetchone(cursor) -> sqlite3.Cursor:
    return cursor.fetchone()


QUERY_DICT: Dict[str, Callable] = {
    "cap_status": _db_cap_status,
}

CURSOR_DICT: Dict[str, Callable] = {
    "cap_status": fetchone,
}


def query_db(action: str, *args):

    sql = QUERY_DICT[action](*args)

    try:
        with connect() as cursor:
            if isinstance(sql, tuple):
                sql_query, args = sql
                cursor.execute(sql_query, args)
            if not isinstance(sql, tuple):
                cursor.execute(sql)

            data = CURSOR_DICT[action](cursor)

    except sqlite3.Error as error:
        log.error(error)
        return None
    return data
