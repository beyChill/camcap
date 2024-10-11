from dataclasses import dataclass
from string import ascii_letters, digits
from termcolor import colored

from app.config.settings import get_settings
from app.utils.constants import SITENAME, VALIDSITES, Streamer

config = get_settings()


@dataclass(
    slots=True,
    init=False,
    frozen=True,
    repr=False,
    eq=False,
)
class CliError(Exception):
    message: str

    def __init__(self, message: str) -> None:
        object.__setattr__(self, "message", message)


class CliValidations:

    site_slug = None
    site_name = None

    @classmethod
    def input(cls, line: str) -> None:
        err = f"Command missing {colored('model name','red')} and {colored('site abbreviation','red')}"
        if not bool(line.split()):
            raise CliError(err)

    @classmethod
    def name_chars(cls, name_: str) -> None:
        err = f"Model's name, {colored(name_, 'red')} is invalid"
        valid_chars = f"{ascii_letters}{digits}_"
        if not all(chars in valid_chars for chars in name_):
            raise CliError(err)

    @classmethod
    def prompt(cls, prompt) -> None:
        err = f"Unknown cam site: {colored(prompt,'red')}"
        if prompt not in VALIDSITES:
            raise CliError(err)

    @classmethod
    def has_cam_site(cls, prompt: str, rest: list) -> None:
        if prompt == config.default_cli_prompt and not rest:
            err = f"add {colored('cam site', 'red')} to request"
            raise CliError(err)

    @classmethod
    def chk_prompt(cls, prompt: str) -> None:
        if prompt == config.default_cli_prompt:
            return None

        if prompt not in VALIDSITES:
            err = f"Only use alpha characters for site,{colored({prompt},'red')}"
            raise CliError(err)

        cls.site_slug = prompt

    @classmethod
    def chk_user_prompt(cls, rest) -> None:
        if not bool(rest):
            return None

        rest, *_ = rest
        if not bool(rest):
            err = f"add {colored('cam site', 'red')} to request"
            raise CliError(err)

        if rest not in VALIDSITES:
            err = f"The site {colored(rest, 'red')} is invalid"
            raise CliError(err)

        cls.site_slug = rest

    @classmethod
    def cli_error(cls, err) -> None:
        cls.message = err
        print(cls.message)

    def slug_to_site(self) -> None:
        self.site_name = SITENAME.get(self.site_slug)

    def check_input(self, line: str, prompt) -> Streamer:
        try:
            self.input(line)
            name_, *rest = line.split()

            self.name_chars(name_)
            self.has_cam_site(prompt, rest)
            self.chk_prompt(prompt)
            self.chk_user_prompt(rest)
            self.slug_to_site()

            return Streamer(name_, self.site_slug, self.site_name)
        except CliError as e:
            print(e.message)
            return Streamer(None, None, None)
