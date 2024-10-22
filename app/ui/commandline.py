from cmd import Cmd
from logging import getLogger
import os

from signal import SIGTERM
import sys

from termcolor import colored

from app.config.settings import get_settings


from app.database.dbactions import (
    block_capture,
    db_add_streamer,
    db_remove_pid,
    query_db,
    stop_capturing,
)
from app.errors.uivalidations import CliError, CliValidations
from app.sites.capture_streamer import CaptureStreamer
from app.sites.create_streamer import CreateStreamer

log = getLogger(__name__)
config = get_settings()


class Cli(Cmd):
    file = None
    intro = colored("  Type help or ? to list commands.\n", "cyan")
    user_prompt = config.default_cli_prompt
    prompt = colored(f"{user_prompt}-> ", "green")

    def do_get(self, line) -> None:
        if None in (data := CliValidations().check_input(line, self.user_prompt)):
            return None

        if not None in (pid := query_db("chk_pid", data.name_)):
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

    def do_block(self, line: str) -> None:
        name_, *rest = CliValidations().input(line)
        block_data = (name_, *rest)

        block_capture(block_data)

    def do_stop(self, line):
        if None in (data := CliValidations().check_input(line, self.user_prompt)):
            return None

        if None in (pid := query_db("chk_pid", data.name_)):
            return None

        name_, pid = pid
        try:
            os.kill(pid, SIGTERM)
        except OSError as error:
            log.error(error)
        stop_capturing(name_)

    def do_quit(self, _):
        pid = query_db("all_pid")

        if len(pid) == 0:
            return None

        for id in pid[0]:
            if id < 1000:
                continue
            try:
                db_remove_pid(id)
                os.kill(id, SIGTERM)
            except OSError as e:
                if e.errno == 3:
                    continue
                print(e)
        sys.exit()

    def do_exit(self, _) -> None:
        self.do_quit(self)

    def do_end(self, _) -> None:
        self.do_quit(self)
