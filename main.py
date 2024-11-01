from threading import Thread
from app.database.dbactions import db_init
from app.jsonchat import run_query_json
from app.log.logger import setup_logging
from app.online_status import run_online_status
from app.ui.commandline import Cli


threads = [
    Thread(target=run_query_json, daemon=True),
    Thread(target=run_online_status, daemon=True),
]

if __name__ == "__main__":
    setup_logging()
    db_init()
    for thread in threads:
        thread.start()

    Cli().cmdloop()
