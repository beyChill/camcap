from app.database.dbactions import db_init
from app.jsonchat import run_query_json
from app.log.logger import setup_logging
from app.ui.commandline import Cli


if __name__ == "__main__":
    setup_logging()
    db_init()
    run_query_json()

    Cli().cmdloop()
