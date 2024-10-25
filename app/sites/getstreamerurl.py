from logging import getLogger
import httpx
from app.utils.constants import HEADERS_STREAM_URL, GetStreamerUrl

log = getLogger(__name__)


async def get_streamer_url(name_: str):
    params = {"room_slug": name_, "bandwidth": "high"}
    url = "https://chaturbate.com/get_edge_hls_url_ajax/"
    async with httpx.AsyncClient(
        headers=HEADERS_STREAM_URL, params=params, http2=True
    ) as client:
        headers = {"Referer": f"https://chaturbate.com/{name_}/"}

        response = await client.post(
            url,
            headers=headers,
            data=params,
            timeout=15,
        )
        if response.status_code != 200:
            log.error(
                "code:",
                response.status_code,
                "- too many request, try streamer capture at a later time",
            )
            return GetStreamerUrl(None, None, None, response.status_code)

        data = response.json()

        url = data["url"]
        if not bool(data["url"]):
            url = None

        return GetStreamerUrl(
            data["success"], url, data["room_status"], response.status_code
        )
