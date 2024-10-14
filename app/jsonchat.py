import asyncio
import math
import pandas as pd
import random
from datetime import datetime
from time import perf_counter
from httpx import AsyncClient
from app.database.dbactions import update_details
from app.utils.constants import HEADERS_IMG, USERAGENTS


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
    async with AsyncClient(headers=HEADERS_IMG, http2=True) as client:
        response = await client.get(
            "https://chaturbate.com/api/ts/roomlist/room-list/?genders=f&limit=90&offset=0",
            headers=headers,
        )

    streamers_online: int = response.json()["total_count"]
    print("models online:", streamers_online)

    data_frame = pd.json_normalize(response.json(), "rooms")

    data_columns.append(
        data_frame[
            ["username", "num_followers", "num_users", "start_timestamp"]
        ].values.tolist()
    )

    page_calc = streamers_online / 90

    pages = math.ceil(page_calc)
    print("pages:", pages)
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
                data_stats = await asyncio.gather(*stat)
        remove_nest = sum(list(data_stats), [])
        remove_next2 = sum(list(remove_nest), [])

        list_to_tuple = [tuple(elem) for elem in remove_next2]
        print("item in gg", len(list_to_tuple))
        update_details(list_to_tuple)

    max_urls = [page_urls[x : x + 38] for x in range(0, len(page_urls), 38)]
    for i, url_batch in enumerate(max_urls):
        await other(url_batch)

        if i % len(url_batch) == 0:
            print("paused:", i)
            await asyncio.sleep(112.04)


async def query_streamers():
    while True:
        start = perf_counter()
        await json_scraping()
        print("Eval time:", perf_counter() - start)
        print(datetime.now())

        await asyncio.sleep(360.05)


if __name__ == "__main__":
    # asyncio.run(query_streamers())

    loop = asyncio.new_event_loop()
    loop.create_task(query_streamers())
    loop.run_forever()
