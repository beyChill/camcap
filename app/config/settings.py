from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    db_name: str = "capcam.sqlite3"
    db_config: str = "createtables.sql"
    db_folder: str = "database/db"
    video_folder: str = "cam_captures"
    parent_dir: Path = Path(__file__).parents[1]
    DB_PATH: Path = Path(parent_dir, db_folder, db_name)
    DB_TABLES: Path = Path(parent_dir, Path(db_folder).parent, db_config)
    VIDEO_DIR: Path = Path(parent_dir, video_folder)
    video_length_seconds: int = 1800
    CAPTURE_LENGTH: str = f"{video_length_seconds}"
    log_level: str = "DEBUG"
    default_cli_prompt: str = "$"


@lru_cache()
def get_settings(**kwargs: dict) -> Settings:
    return Settings(**kwargs)


print(get_settings().parent_dir)
