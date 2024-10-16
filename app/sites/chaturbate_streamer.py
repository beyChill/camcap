from dataclasses import InitVar, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any
from app.config.settings import get_settings
from app.database.dbactions import add_streamer
from app.utils.constants import ModelData, Streamer
from collections.abc import Callable

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
    path_: Path = field(init=False)
    filename: str = field(init=False)
    url: str = field(init=False)
    file_svs: Callable = field(init=False)
    metadata: list = field(init=False)
    return_data: ModelData = field(default=None, init=False)

    def __post_init__(self, streamer_data: Streamer, filesvs=lambda: FileSvs()):
        self.name_, self.site_slug, self.site_name = streamer_data

        

        self.file_svs = filesvs()
        self.url = "http"
        success = True
        if not success:
            del self
            return None

        if self.url is not None:
            self.path_ = self.file_svs.set_video_path(self.name_, self.site_name)
            self.filename = self.file_svs.set_filename(self.name_, self.site_slug)
            self.metadata = self.set_metadata(self.name_, self.site_name)
            self.return_data = ModelData(
                self.name_,
                self.site_name,
                self.url,
                self.path_,
                self.filename,
                self.metadata,
            )

        del self

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

    def return_dat(self) -> ModelData:
        return ModelData(
            self.site_name, self.url, self.path_, self.filename, self.metadata
        )
