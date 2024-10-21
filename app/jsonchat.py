import asyncio
from logging import getLogger
import math
from threading import Thread
import httpx
import pandas as pd
from datetime import datetime
from time import perf_counter, strftime
from httpx import AsyncClient
from random import randint, choice, shuffle
from string import ascii_lowercase

from app.database.dbactions import num_online, db_update_streamers
from app.utils.constants import HEADERS_IMG, USERAGENTS

log = getLogger(__name__)


def random_id(length) -> str:
    letters = ascii_lowercase
    return "a9a9a" + "".join(choice(letters) for _ in range(length))


async def json_scraping() -> None:
    data_columns: list = []
    offset = 0
    page_urls: list[str] = []

    headers = {
        "user-agent": choice(USERAGENTS),
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
    print(strftime("%H:%M:%S"), "- Streamers online:", streamers_online)

    data_frame = pd.json_normalize(response.json(), "rooms")

    data_columns.append(
        data_frame[
            ["username", "num_followers", "num_users", "start_timestamp"]
        ].values.tolist()
    )

    # Number of urls to generate based on 90 streamers per url
    num_urls = math.ceil(streamers_online / 90)

    for _ in range(1, num_urls):
        offset += 90
        page_urls.append(
            f"https://chaturbate.com/api/ts/roomlist/room-list/?genders=f&limit=90&offset={offset}"
        )

    # Sometimes the final predetermined url will no longer exist, causing a crash.
    # Process last url first, randomize the rest.
    page_urls.reverse()
    first_url = page_urls.pop(0)
    shuffle(page_urls)
    page_urls.insert(0, first_url)

    async def get_data(client: AsyncClient, url):
        headers = {
            "User-Agent": choice(USERAGENTS),
            "Cache-Control": "no-cache",
            "Accept-encoding": "gzip, deflate, br, zstd",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
        }

        response = await client.get(url, headers=headers, timeout=35)

        if response.status_code != 200:
            print("code:", response.status_code)
            return [[random_id(10), 0, 0, 971639231]]

        # Zero lenght element means url offset doesn't exist
        if len(response.json()["rooms"]) < 1:
            return [[random_id(10), 0, 0, 971639231]]

        data_frame = pd.json_normalize(response.json(), "rooms")

        data_columns.append(
            data_frame[
                ["username", "num_followers", "num_users", "start_timestamp"]
            ].values.tolist()
        )

        return data_columns

    async def process_urls(i: int, urls: list[str]) -> None:
        async with AsyncClient(headers=HEADERS_IMG, http2=True) as client:
            stat = []

            [stat.append(get_data(client, url)) for url in urls]

            try:
                data_stats = await asyncio.gather(*stat)
            except Exception as e:
                print("Error:", e)

        # test better solution to remove double nested list
        remove_nest = sum(list(data_stats), [])
        remove_next2 = sum(list(remove_nest), [])

        list_to_tuple = [tuple(elem) for elem in remove_next2]

        # write to database
        db_update_streamers(list_to_tuple)

        # delay to prevent triggering rate limit
        # sleep time can be adjusted up / down till limit (response code:429 occurs)
        # error on the side of caution using short delay.
        if i == 0:
            await asyncio.sleep(randint(110, 140))

    # minimize response code 429. Seems chaturbate api rate limit is bassed on site traffic.
    # limit could be 40-60 call
    # If online streamers exceed 7200ish probaby need to rewrite to avoid rate limit
    rate_limit = math.floor(num_urls / 2)

    max_urls = [
        page_urls[x : x + rate_limit] for x in range(0, len(page_urls), rate_limit)
    ]

    try:
        [await process_urls(i, url_batch) for i, url_batch in enumerate(max_urls)]
    except Exception as e:
        for i, url_batch in enumerate(max_urls):
            print(i, len(url_batch))
        print("list comprehension error, process_urls and i iterator")
        print(e)


def exception_handler(loop, context) -> None:
    print(context["exception"])
    print(context["message"])


async def query_streamers():
    while True:
        start = perf_counter()
        await json_scraping()
        # convert to log events
        print("\t", "Processed urls in:", perf_counter() - start, "seconds")
        print("\t", strftime("%H:%M:%S"), "- Json query completed:")

        # Delay allows api rest between queries
        await asyncio.sleep(randint(240, 300))


def start() -> None:
    loop = asyncio.new_event_loop()
    loop.set_exception_handler(exception_handler)
    loop.create_task(query_streamers())
    loop.run_forever()


def run_query_json() -> None:
    thread = Thread(target=start, daemon=True)
    thread.start()
