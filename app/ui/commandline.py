from cmd import Cmd
import sys

from termcolor import colored

from app.config.settings import get_settings
from app.database.dbactions import add_model
from app.errors.uivalidations import CliError, CliValidations


config = get_settings()


class Cli(Cmd):
    file = None
    intro = colored("  Type help or ? to list commands.\n", "cyan")
    user_prompt = config.default_cli_prompt
    prompt = colored(f"{user_prompt}-> ", "green")

    def do_get(self, line) -> None:
        if (data := CliValidations().check_input(line, self.user_prompt)) is None:
            print('inside:',data)
            return None
        print("if:",data)

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
