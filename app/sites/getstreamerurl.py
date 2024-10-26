from logging import getLogger
import httpx
from httpx import AsyncClient
from app.utils.constants import HEADERS_STREAM_URL, GetStreamerUrl

log = getLogger(__name__)


async def get_streamer_url(name_: str):
    base_url = "https://chaturbate.com/get_edge_hls_url_ajax/"
    params = {"room_slug": name_, "bandwidth": "high"}

    async with AsyncClient(
        headers=HEADERS_STREAM_URL, params=params, http2=True
    ) as client:
        headers = {"Referer": f"https://chaturbate.com/{name_}/"}

        response = await client.post(
            base_url,
            headers=headers,
            data=params,
            timeout=15,
        )

        if response.status_code == 429:
            log.error(
                f"code: {response.status_code} - too many request, try streamer capture at a later time",
            )
            return GetStreamerUrl(None, None, None, response.status_code)

        if response.status_code != 200:
            log.error(
                f"code: {response.status_code} - failed to obtain streaming url",
            )
            return GetStreamerUrl(None, None, None, response.status_code)

        data = response.json()

        url = data["url"]
        if not bool(data["url"]):
            url = None

        return GetStreamerUrl(
            data["success"], url, data["room_status"], response.status_code
        )
