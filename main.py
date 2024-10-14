from threading import Thread
from app.database.dbactions import db_init
from app.log.logger import setup_logging
from app.ui.commandline import Cli



def start():
    import app.jsonchat

if __name__ == "__main__":
    # setup_logging()
    db_init()

    thread = Thread(target=start, daemon=True)
    thread.start()

    Cli().cmdloop()
