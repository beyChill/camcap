from logging import INFO
from pathlib import Path
from typing import ClassVar, Literal
from pydantic_settings import BaseSettings
from functools import lru_cache
from datetime import datetime

class Settings(BaseSettings):
    db_name: str = "capcam.sqlite3"
    db_config: str = "createtables.sql"
    db_folder: str = "database/db"
    i_download_folder:str="downloads/images"
    v_download_folder:str="downloads/videos"
    parent_dir: Path = Path(__file__).parents[1]
    DB_PATH: Path = Path(parent_dir, db_folder, db_name)
    DB_TABLES: Path = Path(parent_dir, Path(db_folder).parent, db_config)
    IMAGE_DIR: Path = Path(parent_dir, i_download_folder)
    VIDEO_DIR: Path = Path(parent_dir, v_download_folder)
    video_length_seconds: int = 1800
    CAPTURE_LENGTH: str = f"{video_length_seconds}"
    default_cli_prompt: str = "$"
    log_level:Literal[20]=INFO
    datetime:ClassVar=datetime.now().replace(microsecond=0)


@lru_cache()
def get_settings(**kwargs: dict) -> Settings:
    return Settings(**kwargs)


