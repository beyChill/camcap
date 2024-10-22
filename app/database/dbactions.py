from collections.abc import Callable, Generator
from contextlib import contextmanager
from logging import getLogger
import os
import sqlite3
from typing import Any, Dict
from datetime import date, datetime, timedelta
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


def db_remove_pid(values: list[tuple[None, int]]):
    sql = "UPDATE chaturbate SET pid=? WHERE pid=?"
    arg = values
    _db_executemany(sql, arg)


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


def stop_capturing(name_):
    sql = "UPDATE chaturbate SET follow=?, pid=? WHERE streamer_name=?"
    args = (None, None, name_)
    if not _write_to_db(sql, args):
        log.error(colored(f"Unable to stop capture for {name_}", "red"))


def block_capture(data):
    name_, *reason = data
    reason = " ".join(reason)

    sql = "UPDATE chaturbate SET block_date=?, follow=?, notes=? WHERE streamer_name=?"
    arg = (date.today(), None, reason, name_)
    if not _write_to_db(sql, arg):
        log.error(colored("Block command failed", "red"))


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


def _db_executemany(sql: str, values: list):
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


def _cap_status(name_):
    return (
        "SELECT follow, block_date FROM chaturbate WHERE streamer_name=?",
        (name_,),
    )


def _get_pid(name_):
    return (
        "SELECT streamer_name, pid FROM chaturbate WHERE streamer_name=?",
        (name_,),
    )


def _get_all_pid():
    sql = "SELECT pid FROM chaturbate WHERE pid IS NOT NULL"
    return sql


def _online_status():
    arg = date.today() - timedelta(days=10000)
    return (
        "SELECT streamer_name, followers FROM chaturbate WHERE (last_broadcast>? or last_broadcast IS NULL) AND follow IS NOT NULL AND pid IS NULL AND block_date IS NULL ORDER BY RANDOM() LIMIT 3",
        (arg,),
    )


def fetchone(cursor) -> sqlite3.Cursor:
    return cursor.fetchone()


def fetchall(cursor) -> sqlite3.Cursor:
    return cursor.fetchall()


QUERY_DICT: Dict[str, Callable] = {
    "chk_pid": _get_pid,
    "all_pid": _get_all_pid,
    "cap_status": _cap_status,
    "online_status": _online_status,
}

CURSOR_DICT: Dict[str, Callable] = {
    "chk_pid": fetchone,
    "all_pid": fetchall,
    "cap_status": fetchone,
    "online_status": fetchall,
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
    if data is None:
        data = []
    return data


# ***********************************
# * general
# ***********************************


def check_pid() -> None:
    """Delete inactive pids"""
    models_with_subprocess = query_db("chk_pid")

    log.info(colored("Validating previous capture activity", "cyan"))
    for name_, pid in models_with_subprocess:

        if pid is not None:
            try:
                os.kill(pid, 0)
            except OSError:
                # remove_pid(pid)
                log.debug("Clearing inactive status for %s", name_)
