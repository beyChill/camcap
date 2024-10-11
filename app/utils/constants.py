from pathlib import Path
import sys
from typing import NamedTuple

from app.config.settings import get_settings


class Streamer(NamedTuple):
    name_: str
    site_slug: str
    site: str


VALIDSITES = {"cb", "mfc", "sc"}

SITENAME = {
    "cb": "Chaturbate",
    "mfc": "MyFreeCams",
    "sc": "StripChat",
}

USERAGENTS = (
    "Dalvik/2.1.0 (Linux; U; Android 10; MI CC 9e MIUI/V12.0.3.0.QFMCNXM)",
    "Mozilla/5.0 (Linux; Android 8.0.0; SM-G935V) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10.0; YT7260B Build/PPR1.180610.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.0.3904.96 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 7.0; TECNO IN5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.80 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 6.0.1; SM-A500FU) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.99 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 7.0; SM-J330F Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/64.0.3282.137 Mobile Safari/537.36 Viber/13.1.0.4",
    "Mozilla/5.0 (Linux; Android 10; CPH2035) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.114 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 4.4.2; BASCO L400 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/30.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; X11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.63 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; V2035) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-G975F Build/QP1A.190711.020) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 7.0; d-01J) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.99 Safari/537.36",
    "Mozilla/5.0 (Linux; U; Android 9; zh-CN; ASK-AL00x Build/HONORASK-AL00x) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/78.0.3904.108 UCBrowser/13.0.1.1081 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; vivo 1819 Build/P00610; wv) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.84 Mobile Safari/537.36 VivoBrowser/6.5.0.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_8 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) GSA/180.0.400278405 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 14_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/87.0.4280.77 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) GSA/187.0.410885375 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 8.0.0; SM-G930S) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; M2007J17G Build/RKQ1.200826.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/87.0.4280.141 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 8.1.0; moto e5 play) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SOV38) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; Moto X4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; Redmi Note 8 Pro Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.120 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 8.1.0; LML212VL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.127 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; Redmi Note 8T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Mobile Safari/537.36 EdgA/95.0.1020.48",
    "Mozilla/5.0 (Linux; Android 9; LM-T600) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.93 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; E6910) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.74 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; SM-G991W) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.62 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 8.1.0; Redmi Note 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.105 Mobile Safari/537.36 OPR/63.1.3216.58602",
    "Mozilla/5.0 (Linux; Android 8.1.0; vivo 1803 Build/O11019; wv) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.84 Mobile Safari/537.36 VivoBrowser/6.8.0.1",
    "Mozilla/5.0 (Linux; Android 10; RMX1992) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.181 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0 YaBrowser/20.4.4.168.10 Mobile/15E148 Safari/604.1",
    "com.google.GoogleMobile/57.0.0 iPhone/13.4.1 hw/iPhone8_2",
    "Mozilla/5.0 (Linux; Android 9; SM-G965U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Mobile Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 6.0; MYA-L11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.127 Mobile Safari/537.36 (Ecosia android@85.0.4183.127)",
    "Mozilla/5.0 (Linux; Android 9; Mi MIX 3 5G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; begonia) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.101 Mobile Safari/537.36",
    "Lupa/6 CFNetwork/1240.0.4 Darwin/20.5.0",
)

HEADERS = {
    "authority": "chaturbate.com",
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "Accept-Encoding": "gzip, compress;q=0.7, identity;q=0.5, *;q=0.3",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    "x-requested-with": "XMLHttpRequest",
}

HEADERS_IMG = {
    "authority": "thumb.live.mmcdn.com",
    "method": "GET",
    "accept-language": "en-US,en;q=0.9",
    "accept-encoding": "gzip, deflate, br",
    "scheme": "https",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Linux",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}

referers = (
    "https://www.google.com",
    "https://www.yahoo.com",
    "https://www.bing.com",
    "https://www.zillow.com",
    "https://www.craigslist.org",
    "https://www.indeed.com",
    "http://vector.us",
    "http://www.similicio.us",
    "https://www.google.ca",
    "https://www.indeed.com",
    "https://www.bing.com",
    "https://www.realtor.ca",
    "https://duckduckgo.com/",
)

default_sites = [
    ("CB", "Chaturbate"),
    ("MFC", "MyFreeCams"),
]

default_config = [
    ("download_parent_dir", "downloads"),
    ("debug", False),
    ("resolution", 1080),
    ("resolutionPreference", "closest"),
]

TABLES = {
    "sites": default_sites,
    "config": default_config,
}
