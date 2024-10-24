import asyncio
from datetime import datetime
from logging import getLogger
from random import choice, uniform
from threading import Thread
from time import perf_counter, strftime
from httpx import AsyncClient
from tabulate import tabulate
from termcolor import colored
from app.database.dbactions import query_db
from app.sites.capture_streamer import CaptureStreamer
from app.sites.create_streamer import CreateStreamer
from app.utils.constants import HEADERS_IMG, USERAGENTS, Streamer

log = getLogger(__name__)


def make_streamer(data):
    if None in (streamer_data := CreateStreamer(data).return_data):
        return None

    CaptureStreamer(streamer_data)


def start_cap(streamer_init):
    for data in streamer_init:
        make_streamer(data)


async def get_data(
    client: AsyncClient, url: str, name_: str, followers: int
) -> tuple[int, str, int]:
    headers = {
        "user-agent": choice(USERAGENTS),
        "path": f"/stream?room={name_}",
        "accept-encoding": "gzip, deflate, br",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "sec-fetch-dest": "image",
        "sec-fetch-mode": "no-cors",
        "sec-fetch-site": "cross-site",
    }
    response = await client.get(
        url,
        headers=headers,
        timeout=35,
    )

    return (response.status_code, name_, followers)


async def get_online_streamers():
    if (offline := query_db("online_status")) == []:
        print("Zero streamers are desinated for capture.")
        return False

    online = []
    not_online = []
    url_responses_count = 0

    # Using 90 to match site queries per page.
    # CDN can handle much more but caution is best approach.
    urls_per_batch = 90

    chunks = [
        offline[x : x + urls_per_batch] for x in range(0, len(offline), urls_per_batch)
    ]

    async with AsyncClient(headers=HEADERS_IMG) as client:
        for _, streamer_data in enumerate(chunks):
            stat = []
            for _, streamer_info in enumerate(streamer_data):
                name_, followers = streamer_info
                stat.append(
                    get_data(
                        client,
                        f"https://jpeg.live.mmcdn.com/stream?room={name_}",
                        name_,
                        followers,
                    )
                )
            if len(offline) > urls_per_batch:
                # Haven't hit rate limit, however a pause is considerate approach
                await asyncio.sleep(round(uniform(2, 4), 1))

            url_responses = await asyncio.gather(*stat)
        url_responses_count += len(url_responses)
        for results in url_responses:
            status_code, name_, followers = results

            if status_code == 200:
                online.append((name_, followers))

            if status_code >= 201:
                not_online.append((name_, followers))

    # CLI table formatting
    head = ["Name", "followers"]

    if len(online) > 0:
        online.sort(key=lambda tup: tup[1], reverse=True)
        print(tabulate(online, headers=head, tablefmt="pretty"))

    streamer_init = [
        Streamer(streamer_name, "CB", "Chaturbate") for streamer_name, *_ in online
    ]

    print(f"Following {url_responses_count} streamers")
    print(f"Starting capture for {len(online)} streamers")

    # CreateStreamer class (create_streamer.py) uses asyncio.run
    # calling with a seperate class to avoid async loop errors
    if len(streamer_init) > 0:
        thread = Thread(
            target=start_cap,
            args=(streamer_init,),
            daemon=True,
        )
        thread.start()
        thread.join()

    await asyncio.sleep(0.03)

    return True


async def query_online():
    while True:
        start = perf_counter()
        result = await get_online_streamers()
        if not bool(result):
            break
        log.info(f"{strftime("%H:%M:%S")}: Online status completed in {colored(round((perf_counter() - start), 4),"green")} seconds")
        await asyncio.sleep(uniform(290.05,345.7))


def run_online_status():
    loop = asyncio.new_event_loop()
    loop.create_task(query_online())
    loop.run_forever()
