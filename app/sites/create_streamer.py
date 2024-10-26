import asyncio
from dataclasses import InitVar, dataclass, field
from datetime import date, datetime
from logging import getLogger
from pathlib import Path
from time import strftime

from termcolor import colored
from app.config.settings import get_settings
from app.database.dbactions import db_add_streamer
from app.sites.getstreamerurl import get_streamer_url
from app.utils.constants import StreamerData, Streamer
from collections.abc import Callable


log = getLogger(__name__)
config = get_settings()


@dataclass(slots=True)
class FileSvs:

    def set_video_path(self, name_, site, dir=config.VIDEO_DIR) -> Path:
        save_dir = Path(dir, site, name_).joinpath()
        return save_dir

    def set_filename(self, name_: str, slug: str) -> str:
        now = datetime.now()
        slug = slug.upper()
        return f'{name_} [{slug}] {str(now.strftime("(%Y-%m-%d) %H%M%S"))}.mkv'


@dataclass(slots=True, eq=False)
class CreateStreamer:
    streamer_data: InitVar[Streamer]
    name_: str = field(init=False)
    site_slug: str = field(init=False)
    site_name: str = field(init=False)
    path_: Path = field(default=None, init=False)
    filename: str = field(default=None, init=False)
    url: str = field(default=None, init=False)
    file_svs: Callable = field(init=False)
    metadata: list = field(default=None, init=False)
    return_data: StreamerData = field(default=None, init=False)
    success: bool = field(default=None, init=False)
    room_status: str = field(default=None, init=False)
    status_code: int = field(default=None, init=False)

    def __post_init__(
        self, streamer_data: Streamer, filesvs=lambda: FileSvs()
    ) -> StreamerData | None:
        self.name_, self.site_slug, self.site_name = streamer_data

        self.file_svs = filesvs()

        asyncio.run(self.get_url())

        if not bool(self.success) and self.status_code != 429:
            log.error(f"{self.name_} is not a {self.site_name} streamer")
            return self.return_dat()

        db_add_streamer(self.name_)

        if not bool(self.url) and self.status_code == 200:
            log.info(colored(f"{strftime("%H:%M:%S")}: {self.name_} is {self.room_status}","yellow"))

        self.path_ = self.file_svs.set_video_path(self.name_, self.site_name)
        self.filename = self.file_svs.set_filename(self.name_, self.site_slug)
        self.metadata = self.set_metadata(self.name_, self.site_name)
        self.return_dat()

        del self

    async def get_url(self):
        response = await get_streamer_url(self.name_)
        self.success = response.success
        self.url = response.url
        self.room_status = response.room_status
        self.status_code = response.status_code

    def set_metadata(self, name_, site) -> list:
        metadata = []
        today_ = date.today()
        today_str = str(today_)

        meta = {
            "title": f"{name_} Live - {today_str}",
            "author": f"{name_}",
            "album_artist": f"{name_}",
            "publisher": f"{site}",
            "description": f"{name_} live cam performance on {today_}",
            "genre": "webcam",
            "copyright": "Creative Commons",
            "album": f"{name_} {site}",
            "date": f"{today_}",
            "year": f"{today_str}",
            "service_provider": "python3",
            "encoder": "x265",
        }

        # format for ffmpeg use
        for key, value in meta.items():
            metadata.extend(["-metadata", f"{key}={value}"])
        return metadata

    def return_dat(self) -> StreamerData:
        self.return_data = StreamerData(
            self.name_,
            self.site_name,
            self.url,
            self.path_,
            self.filename,
            self.metadata,
            self.success,
        )
