from cmd import Cmd
import sys

from termcolor import colored

from app.config.settings import get_settings


from app.database.dbactions import db_add_streamer
from app.errors.uivalidations import CliError, CliValidations
from app.sites.chaturbate_streamer import CreateStreamer

config = get_settings()

class Cli(Cmd):
    file = None
    intro = colored("  Type help or ? to list commands.\n", "cyan")
    user_prompt = config.default_cli_prompt
    prompt = colored(f"{user_prompt}-> ", "green")

    def do_get(self, line) -> None:
        if None in (data := CliValidations().check_input(line, self.user_prompt)):
            return None

        if None in (streamer_data := CreateStreamer(data).return_data):
            return None
        
        if not None in db_add_streamer(streamer_data.name_):
            return None

        # CaptureStreamer(streamer_data)

    def do_prompt(self, new_prompt) -> None:
        try:
            CliValidations.prompt(new_prompt)
            self.user_prompt = new_prompt
            self.prompt = f"{colored(f'{self.user_prompt}-> ','green')}"
        except CliError as e:
            print(e.message)

    def do_quit(self, _):
        sys.exit()

    def do_exit(self, _) -> None:
        self.do_quit(self)

    def do_end(self, _) -> None:
        self.do_quit(self)
