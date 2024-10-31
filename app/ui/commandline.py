import asyncio
import sys
import os
from cmd import Cmd
from logging import getLogger
from signal import SIGTERM
from tabulate import tabulate
from termcolor import colored
from app.config.settings import get_settings
from app.errors.custom_errors import CliErrors
from app.errors.uivalidations import CliValidations
from app.sites.capture_streamer import CaptureStreamer
from app.sites.create_streamer import CreateStreamer
import app.database.dbactions as dbase
from app.sites.getstreamerurl import get_streamer_url
from app.utils.constants import GetStreamerUrl


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

        streamer_data = asyncio.run(get_streamer_url([data.name_]))
        streamer: GetStreamerUrl = streamer_data[0]

        dbase.db_add_streamer(streamer.name_)

        if not None in (dbase.db_get_pid(streamer.name_)):
            return None

        if None in (
            streamer_data := [CreateStreamer(*x).return_data for x in streamer_data]
        ):
            return None

        [CaptureStreamer(x) for x in streamer_data]

        return None

    def do_prompt(self, new_prompt) -> None:
        try:
            CliValidations.prompt(new_prompt)
            self.user_prompt = new_prompt
            self.prompt = f"{colored(f'{self.user_prompt}-> ','green')}"
        except CliErrors as e:
            print(e)

        return None

    def do_block(self, line: str) -> None:
        name_, *rest = CliValidations().input(line)
        block_data = (name_, *rest)

        dbase.block_capture(block_data)

    def do_stop(self, line) -> None:
        if None in (data := CliValidations().check_input(line, self.user_prompt)):
            return None

        if None in (pid := dbase.db_get_pid(data.name_)):
            return None

        name_, pid = pid

        try:
            os.kill(pid, SIGTERM)
        except OSError as error:
            log.error(error)
        finally:
            dbase.stop_capturing(name_)

    def do_unfollow(self, line):
        if None in (data := CliValidations().check_input(line, self.user_prompt)):
            return None

        dbase.db_unfollow(data.name_)

    def do_unf(self, line):
        self.do_unfollow(line)

    def do_cap(self, line) -> None:
        options = {
            "name": "streamer_name",
            "date": "follow",
            "number": "recorded",
        }
        line = line.split()[0]
        value = options[line]

        query = dbase.db_capture(value)

        if query == []:
            print("Presently capturing zero streamers")
            return

        head = ["Streamers", "following", "# Caps"]
        print(
            tabulate(
                query,
                headers=head,
                tablefmt="pretty",
                colalign=("left", "center", "center"),
            )
        )

    def do_offline(self, line) -> None:
        options = {
            "name": "streamer_name",
            "date": "follow",
            "number": "recorded",
        }
        line = line.split()[0]
        value = options[line]

        query = dbase.db_offline(value)

        if query == []:
            print("Following zero offline streamers")
            return

        head = ["Streamers", "following", "# Caps"]
        print(
            tabulate(
                query,
                headers=head,
                tablefmt="pretty",
                colalign=("left", "center", "center"),
            )
        )

    def do_quit(self, _):
        pids = dbase.db_all_pids()

        if len(pids) == 0:
            sys.exit()

        # parmeters for sql
        values: list = [(None, pid) for pid, in pids]

        # list of tuple converted for os.kill process
        ids: list = [pid[0] for pid in pids]

        dbase.db_remove_pid(values)

        try:
            [os.kill(id, SIGTERM) for id in ids]
        except OSError as e:
            if e.errno == 3:
                pass

        sys.exit()

    def do_exit(self, _) -> None:
        self.do_quit(self)

    def do_end(self, _) -> None:
        self.do_quit(self)
