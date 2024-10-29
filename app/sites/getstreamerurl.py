import asyncio
from dataclasses import dataclass, field
import inspect
from logging import getLogger
from time import perf_counter, strftime
from typing import Any, Dict, Self
from httpx import AsyncClient
from termcolor import colored
from app.errors.custom_errors import GetDataError
from app.sites.create_streamer import CreateStreamer
from app.utils.constants import HEADERS_STREAM_URL, GetStreamerUrl, StreamerData

log = getLogger(__name__)


async def get_streamer_url(streamers: list[str]):
    start_ = perf_counter()
    async with AsyncClient(headers=HEADERS_STREAM_URL, http2=True) as client:
        try:
            async with asyncio.TaskGroup() as group:
                results = []
                for name_ in streamers:
                    task = group.create_task(get_data(client, name_))
                    task.add_done_callback(lambda t: results.append(t.result()))
        except:
            pass
    log.debug(
        f"Processed {colored(len(results),"green")} streamers in: {colored(round(perf_counter() - start_,4), 'green')} seconds"
    )

    return results


async def get_data(client: AsyncClient, name_: str):
    # functionName=inspect.getframeinfo(inspect.currentframe()).function

    base_url = "https://chaturbate.com/get_edge_hls_url_ajax/"
    params = {"room_slug": name_, "bandwidth": "high"}
    headers = {"Referer": f"https://chaturbate.com/{name_}/"}
    response = await client.post(
        base_url,
        headers=headers,
        data=params,
        timeout=15,
    )

    data = response.json()

    try:
        if response.status_code == 429:
            raise GetDataError(name_, "429", response.status_code, __loader__.name)
        if response.status_code != 200:
            raise GetDataError(name_, "not200", response.status_code, __loader__.name)
        if not bool(data["success"]):
            raise GetDataError(name_, "notfound", response.status_code, __loader__.name)
    except GetDataError as e:
        print(e)
        return None

    return GetStreamerUrl(
        name_, data["success"], data["url"], data["room_status"], response.status_code
    )
