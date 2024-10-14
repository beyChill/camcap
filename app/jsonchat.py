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

from app.database.dbactions import num_online, update_details
from app.utils.constants import HEADERS_IMG, USERAGENTS

log = getLogger(__name__)

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
    print("models online:", streamers_online)

    data_frame = pd.json_normalize(response.json(), "rooms")

    data_columns.append(
        data_frame[
            ["username", "num_followers", "num_users", "start_timestamp"]
        ].values.tolist()
    )

    page_calc = streamers_online / 90

    pages = math.ceil(page_calc)
    offset = 0
    page_urls: list = []

    for _ in range(1, pages):
        offset += 90
        page_urls.append(
            f"https://chaturbate.com/api/ts/roomlist/room-list/?genders=f&limit=90&offset={offset}"
        )

    async def get_data(client: AsyncClient, url):
        headers = {
            "user-agent": random.choice(USERAGENTS),
            "accept-encoding": "gzip, deflate, br",
            "accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "sec-fetch-dest": "image",
            "sec-fetch-mode": "no-cors",
            "sec-fetch-site": "cross-site",
        }
        response = await client.get(
            url,
            headers=headers,
            timeout=35,
        )

        if not response.headers.get("Content-Type").startswith("application/json"):
            print(response.status_code)
            await asyncio.sleep(90)
            return [None, 0, 0, 0]

        if response.status_code != 200:
            print("code:", response.status_code)
            return [None, 0, 0, 0]

        data_frame = pd.json_normalize(response.json(), "rooms")

        data_columns.append(
            data_frame[
                ["username", "num_followers", "num_users", "start_timestamp"]
            ].values.tolist()
        )

        return data_columns

    async def other(urls: list):
        for url in urls:
            async with AsyncClient(headers=HEADERS_IMG, http2=True) as client:
                stat = []
                stat.append(get_data(client, url))
                try:
                    data_stats = await asyncio.gather(*stat,return_exceptions=True)
                except Exception as e:
                    print("ERRRRRROOOORRR:", e)

        remove_nest = sum(list(data_stats), [])
        remove_next2 = sum(list(remove_nest), [])

        list_to_tuple = [tuple(elem) for elem in remove_next2]
        update_details(list_to_tuple)

    max_urls = [page_urls[x : x + 30] for x in range(0, len(page_urls), 30)]
    for i, url_batch in enumerate(max_urls):
        await other(url_batch)

        if i % len(url_batch) == 0:
            await asyncio.sleep(121.04)

def exception_handler(loop, context):
    # get details of the exception
    exception = context['exception']
    message = context['message']
    # log exception
    print(f'Task failed, msg={message}, exception={exception}')
    print("***** context ****",context)

async def query_streamers():
    while True:
        start = perf_counter()
        await json_scraping()
        # convert for debugging log
        print("Eval time:", perf_counter() - start)
        print(datetime.now())

        await asyncio.sleep(360.05)

def start():
    loop = asyncio.new_event_loop()
    loop.set_exception_handler(exception_handler)
    loop.create_task(query_streamers())
    loop.run_forever()


def run_query_json():
    thread = Thread(target=start, daemon=True)
    thread.start()
