from cmd import Cmd
import sys

from termcolor import colored

from app.config.settings import get_settings


from app.database.dbactions import db_add_streamer, query_db
from app.errors.uivalidations import CliError, CliValidations
from app.sites.capture_streamer import CaptureStreamer
from app.sites.create_streamer import CreateStreamer

config = get_settings()


class Cli(Cmd):
    file = None
    intro = colored("  Type help or ? to list commands.\n", "cyan")
    user_prompt = config.default_cli_prompt
    prompt = colored(f"{user_prompt}-> ", "green")

    def do_get(self, line) -> None:
        if None in (data := CliValidations().check_input(line, self.user_prompt)):
            return None

        if not None in (pid := query_db("chk_pid",data.name_)):
            return None

        if None in (streamer_data := CreateStreamer(data).return_data):
            return None

        CaptureStreamer(streamer_data)

        return None

    def do_prompt(self, new_prompt) -> None:
        try:
            CliValidations.prompt(new_prompt)
            self.user_prompt = new_prompt
            self.prompt = f"{colored(f'{self.user_prompt}-> ','green')}"
        except CliError as e:
            print(e.message)

        return None

    def do_quit(self, _):
        sys.exit()

    def do_exit(self, _) -> None:
        self.do_quit(self)

    def do_end(self, _) -> None:
        self.do_quit(self)
