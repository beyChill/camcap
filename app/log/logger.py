import atexit
import json
import logging.config
import logging.handlers
from pathlib import Path


def setup_logging():
    logger_config = Path("app/log/logger_config.json")
    with open(logger_config, "r", encoding="utf-8") as f:
        config = json.load(f)

    logging.config.dictConfig(config)
    for handler_name in logging.getHandlerNames():
        handler = logging.getHandlerByName(handler_name)
        if isinstance(handler, logging.handlers.QueueHandler):
            handler.listener.start()  # type: ignore
            atexit.register(handler.listener.stop)  # type: ignore

