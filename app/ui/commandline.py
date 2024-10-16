from cmd import Cmd
import sys

from termcolor import colored

from app.config.settings import get_settings
# from app.database.dbactions import add_model
from app.errors.uivalidations import CliError, CliValidations
from app.sites.chaturbate_streamer import CreateStreamer
# from app.sites.chaturbate_streamer import aa


config = get_settings()


class Cli(Cmd):
    file = None
    intro = colored("  Type help or ? to list commands.\n", "cyan")
    user_prompt = config.default_cli_prompt
    prompt = colored(f"{user_prompt}-> ", "green")

    def do_get(self, line) -> None:
        if (data := CliValidations().check_input(line, self.user_prompt)) is None:
            return None
        
        n=CreateStreamer(data.name_,data.site_slug, data.site).return_data
        print(n.name_)
        print(n.url)
        print(n.file)
        print(n.path_)
        print(n.site)

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
