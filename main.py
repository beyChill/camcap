from app.database.dbactions import db_init
from app.log.logger import setup_logging
from app.ui.commandline import Cli
import sys


if __name__ == "__main__":
    setup_logging()
    db_init()
    Cli().cmdloop()
