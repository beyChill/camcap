import asyncio
from collections.abc import Iterable
import subprocess
from dataclasses import dataclass, field
from io import TextIOWrapper
from logging import DEBUG, getLogger
from pathlib import Path
from subprocess import DEVNULL, Popen
from threading import Thread
from time import sleep, strftime
from termcolor import colored
from app.config.settings import get_settings
from app.database.dbactions import db_cap_status, db_remove_pid, db_update_pid
from app.sites.create_streamer import CreateStreamer
from app.sites.getstreamerurl import get_streamer_url
from app.utils.constants import StreamerData, StreamerWithPid

log = getLogger(__name__)

cli_logging = get_settings().log_level


@dataclass(slots=True)
class CaptureStreamer:
    data: StreamerData
    metadata: list = field(init=False)
    path_: Path = field(init=False)
    file: Path = field(init=False)
    name_: str = field(init=False)
    site: str = field(init=False)
    url: str = field(init=False)
    args_ffmpeg: list = field(default_factory=list)
    pid: int = field(default=0, init=False)
    capturetime: int = field(default=1200, init=False)
    process: Popen[bytes] = field(init=False)

    def __post_init__(self):
        
        self.metadata = self.data.metadata
        self.path_ = self.data.path_.mkdir(parents=True, exist_ok=True)
        self.name_ = self.data.name_
        self.site = self.data.site
        self.url = self.data.url
        self.file = Path(self.data.path_, self.data.file).joinpath()
        self.capturetime = get_settings().CAPTURE_LENGTH
        self.args_ffmpeg = self.ffmpeg_args()
        if self.url:
            self.activate()

    def ffmpeg_args(self):
        args = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            self.url,
            *self.metadata,
            "-t",
            self.capturetime,
            "-c:v",
            "copy",
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            self.file,
        ]
        return args

    def std_out(self) -> int | TextIOWrapper:
        if cli_logging != DEBUG:
            return DEVNULL
        return open(f"{self.path_}/stdout.log", "w+", encoding="utf-8")

    def subprocess_status(self, db_model: StreamerWithPid, process: Popen):
        pid, name_, site = db_model
        pid_list = []
        pid_list.append((None, pid))

        try:
            while True:
                if process.poll() is not None:
                    db_remove_pid(pid_list)
                    log.debug(f"{strftime("%H:%M:%S")}: {colored(f"{name_}-{site} subprocess stopped", "yellow")}")
                    del self
        except Exception:
            pass
        finally:
            sleep(9)
            follow, block = db_cap_status(name_)

            if not bool(follow) or bool(block):
                return None

            data = asyncio.run(get_streamer_url([name_]))

            re_streamer=[CreateStreamer(*x).return_data for x in data if isinstance(x, Iterable)]

            [CaptureStreamer(x) for x in re_streamer if isinstance(x, Iterable)]

    def activate(self):
        process = Popen(
            self.args_ffmpeg,
            stdin=DEVNULL,
            stdout=self.std_out(),
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        pid = process.pid
        db_model = StreamerWithPid(pid, self.name_, self.site)

        db_update_pid(db_model)

        thread = Thread(
            target=self.subprocess_status, args=(db_model, process), daemon=True
        )
        thread.start()
        del self
