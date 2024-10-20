from logging import getLogger
from random import choice

import httpx


from app.utils.constants import HEADERS, USERAGENTS, GetStreamerUrl

log = getLogger(__name__)


async def get_streamer_url(name_: str):
    params = {"room_slug": name_, "bandwidth": "high"}
    url = "https://chaturbate.com/get_edge_hls_url_ajax/"
    async with httpx.AsyncClient(headers=HEADERS, params=params, http2=True) as client:
        headers = {
            "User-Agent": choice(USERAGENTS),
            "Cache-Control": "no-cache",
            "Accept-encoding": "gzip, deflate, br, zstd",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Referer": f"https://chaturbate.com/{name_}/",
        }

        response = await client.post(
            url,
            headers=headers,
            data=params,
            timeout=15,
        )
        if response.status_code != 200:
            print(response.status_code)
            print(
                "code:", response.status_code, "- try streamer capture at a later time"
            )
            return GetStreamerUrl(None, None, None)

        data = response.json()

        url = data["url"]
        if not bool(data["url"]):
            url = None

        return GetStreamerUrl(data["success"], url, data["room_status"])
