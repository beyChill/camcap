import asyncio
from logging import getLogger
import math
from threading import Thread
import httpx
import pandas as pd
import random
from datetime import datetime
from time import perf_counter
from httpx import AsyncClient
import random, string

from app.database.dbactions import num_online, db_update_streamers
from app.utils.constants import HEADERS_IMG, USERAGENTS

log = getLogger(__name__)


def random_id(length):
    letters = string.ascii_lowercase
    return "a9a9a" + "".join(random.choice(letters) for i in range(length))


async def json_scraping():
    data_columns: list = []
    headers = {
        "user-agent": random.choice(USERAGENTS),
        "accept-encoding": "gzip, deflate, br",
        "accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "sec-fetch-dest": "image",
        "sec-fetch-mode": "no-cors",
        "sec-fetch-site": "cross-site",
    }
    async with httpx.AsyncClient(headers=HEADERS_IMG, http2=True) as client:
        response = await client.get(
            "https://chaturbate.com/api/ts/roomlist/room-list/?genders=f&limit=90&offset=0",
            headers=headers,
        )

    streamers_online: int = response.json()["total_count"]
    num_online(streamers_online)
    print("Streamers online:", streamers_online, datetime.now())

    data_frame = pd.json_normalize(response.json(), "rooms")

    data_columns.append(
        data_frame[
            ["username", "num_followers", "num_users", "start_timestamp"]
        ].values.tolist()
    )

    # Number of urls to generate based on 90 streamers per url
    # Sometimes the final predetermined url will no longer exist, causing a crash.
    # Reversing urls in list helps.
    num_urls = math.ceil(streamers_online / 90)

    offset = 0
    page_urls: list[str] = []

    for _ in range(1, num_urls):
        offset += 90
        page_urls.append(
            f"https://chaturbate.com/api/ts/roomlist/room-list/?genders=f&limit=90&offset={offset}"
        )
        page_urls.reverse()

    async def get_data(client: AsyncClient, url):
        headers = {
            "User-Agent": random.choice(USERAGENTS),
            "Cache-Control": "no-cache",
            "Accept-encoding": "gzip, deflate, br, zstd",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
        }

        response = await client.get(url, headers=headers, timeout=25)

        if response.status_code == 429:
            print("code:", response.status_code, datetime.now())
            return [[random_id(10), 0, 0, 971639231]]

        if response.status_code != 200:
            print("code:", response.status_code, "- not 200")
            return [[random_id(10), 0, 0, 971639231]]

        # json will element will have lenght of zero when url doesn't match chaturbate api offerings
        if len(response.json()["rooms"]) < 1:
            return [[random_id(10), 0, 0, 971639231]]

        data_frame = pd.json_normalize(response.json(), "rooms")

        data_columns.append(
            data_frame[
                ["username", "num_followers", "num_users", "start_timestamp"]
            ].values.tolist()
        )

        return data_columns

    async def process_urls(urls: list[str]) -> None:
        async with AsyncClient(headers=HEADERS_IMG, http2=True) as client:
            stat = []
            for url in urls:
                stat.append(get_data(client, url))

            try:
                data_stats = await asyncio.gather(*stat)
            except Exception as e:
                print(url)
                print("Error:", e)

        # test better solution to remove double nested list
        remove_nest = sum(list(data_stats), [])
        remove_next2 = sum(list(remove_nest), [])

        list_to_tuple = [tuple(elem) for elem in remove_next2]

        # write to database
        db_update_streamers(list_to_tuple)

    # minimize response code 429. Seems chaturbate api rate limit is bassed on site traffic.
    # limit could be 40-60 call
    rate_limit = math.floor(num_urls / 2)
    max_urls = [
        page_urls[x : x + rate_limit] for x in range(0, len(page_urls), rate_limit)
    ]

    for i, url_batch in enumerate(max_urls):
        await process_urls(url_batch)

        # delay to prevent triggering rate limit
        # sleep time can be adjusted up / down till limit (response code:429 is reached)
        if i == 0:
            await asyncio.sleep(110.04)


def exception_handler(loop, context):
    print(context["exception"])
    print(context["message"])


async def query_streamers():
    while True:
        start = perf_counter()
        await json_scraping()
        # convert to log events
        # print("Eval time:", perf_counter() - start)
        # print(datetime.now())

        await asyncio.sleep(360.05)


def start():
    loop = asyncio.new_event_loop()
    loop.set_exception_handler(exception_handler)
    loop.create_task(query_streamers())
    loop.run_forever()


def run_query_json():
    thread = Thread(target=start, daemon=True)
    thread.start()
