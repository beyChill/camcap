import asyncio
from datetime import timedelta
from logging import getLogger
from random import uniform
from threading import Thread
from time import perf_counter, strftime
from httpx import AsyncClient
from tabulate import tabulate
from termcolor import colored
from app.database.dbactions import db_follow_offline, db_followed, db_recorded
from app.sites.capture_streamer import CaptureStreamer
from app.sites.create_streamer import CreateStreamer
from app.utils.constants import HEADERS_IMG, Streamer

log = getLogger(__name__)


def make_streamer(data):
    if None in (streamer_data := CreateStreamer(data).return_data):
        return None

    CaptureStreamer(streamer_data)


def start_cap(streamer_init):
    [make_streamer(data) for data in streamer_init]


def streamer_grouping(followed: list):
    # Using 90 to match site queries per page.
    # caution is best approach to avoid 429s.
    group_limit = 90

    streamer_groups = [
        followed[x : x + group_limit] for x in range(0, len(followed), group_limit)
    ]
    return streamer_groups


async def get_data(client: AsyncClient, name_: str):
    headers = {"path": f"/stream?room={name_}"}

    response = await client.get(
        f"https://jpeg.live.mmcdn.com/stream?room={name_}",
        headers=headers,
        timeout=35,
    )

    return (response.status_code, name_)


async def process_streamers(streamer_groups: list):
    start_ = perf_counter()

    async with AsyncClient(headers=HEADERS_IMG, http2=True) as client:
        async with asyncio.TaskGroup() as group:
            results = []

            for i, streamers in enumerate(streamer_groups):
                for streamer in streamers:
                    task = group.create_task(get_data(client, streamer))
                    task.add_done_callback(lambda t: results.append(t.result()))

                # Haven't hit rate limit, however a pause is considerate approach
                # if i < len(streamer_groups):
                #     await asyncio.sleep(round(uniform(2, 4), 1))

    log.debug(
        f"Processed {colored(len(results), "green")} streamers in: {colored(round(perf_counter() - start_, 4), 'green')} seconds"
    )
    return results


def sort_streamers(is_online: list[tuple[int, str]]):
    online: list = []
    offline: list = []

    for results in is_online:
        status_code, name_ = results
        if status_code == 200:
            online.append((name_))
        if status_code >= 201:
            offline.append((name_))

    return (online, offline)


def online_tables(online):
    # CLI table
    if (active_streamers := db_recorded(online)) is None:
        print("none online")
        return None

    active_streamers.sort(key=lambda tup: tup[1], reverse=True)

    print(f"Followed streamers online: {colored(len(active_streamers),'green')}")
    head = ["Streamers", "# Caps"]
    print(
        tabulate(
            active_streamers,
            headers=head,
            tablefmt="pretty",
            colalign=("left", "center"),
        )
    )
    print()
    return active_streamers


def offline_tables(offline):
    if (offline_streamers := db_follow_offline(offline)) is None:
        print("none online")
        return None

    offline_streamers.sort(key=lambda tup: tup[1], reverse=False)

    print(f"Followed streamers offline: {colored(len(offline_streamers),'green')}")
    head = ["Streamers", "Last Seen", "# Caps"]
    print(
        tabulate(
            offline_streamers,
            headers=head,
            tablefmt="pretty",
            colalign=("left", "left", "center"),
        )
    )
    print()
    return offline_streamers


async def get_online_streamers() -> None:

    if (followed := db_followed()) == []:
        log.info(colored("Zero streamers are designated for capture", "yellow"))
        return None

    streamer_groups = streamer_grouping(followed)

    is_online = await process_streamers(streamer_groups)
    online, offline = sort_streamers(is_online)

    offline_streamers = offline_tables(offline)

    if len(online) > 0:
        active_streamers = online_tables(online)
        streamer_init = [
            Streamer(streamer_name, "CB", "Chaturbate")
            for streamer_name, *_ in active_streamers
        ]

        # CreateStreamer class (create_streamer.py) uses asyncio.run
        # calling with a seperate class to avoid async loop errors
        thread = Thread(
            target=start_cap,
            args=(streamer_init,),
            daemon=True,
        )
        thread.start()
        # thread.join()

    await asyncio.sleep(0.03)

    return None


async def query_online():
    while True:
        start = perf_counter()
        result = await get_online_streamers()
        # if not bool(result):
        #     pass
        log.info(
            f"{strftime("%H:%M:%S")}: Streamer check completed: {colored(round((perf_counter() - start), 4), "green")} seconds"
        )

        delay_ = uniform(290.05, 345.7)
        _, minutes, seconds = str(timedelta(seconds=delay_)).split(":")
        seconds = round(float(seconds))
        log.info(f"Next streamer check: {minutes}min {seconds}sec")
        await asyncio.sleep(delay_)


def run_online_status():
    loop = asyncio.new_event_loop()
    loop.create_task(query_online())
    loop.run_forever()


if __name__ == "__main__":
    run_online_status()
