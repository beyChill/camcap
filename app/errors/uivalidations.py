from string import ascii_letters, digits
from app.config.settings import get_settings
from app.errors.custom_errors import CliErrors
from app.utils.constants import SITENAME, VALIDSITES, Streamer

config = get_settings()


class CliValidations:

    site_slug: str
    site_name: str

    @classmethod
    def input(cls, line: str) -> None:
        if not bool(line.split()):
            raise CliErrors("", "input", "get candy cb")
        return line.split()

    @classmethod
    def name_chars(cls, name_: str) -> None:
        valid_chars = f"{ascii_letters}{digits}_"
        if not all(chars in valid_chars for chars in name_):
            raise CliErrors(name_, "chars", "only use letters and numbers")

    @classmethod
    def prompt(cls, prompt) -> None:
        if prompt not in VALIDSITES:
            raise CliErrors(prompt, "site_prompt", f"sites {VALIDSITES}")

    @classmethod
    def has_cam_site(cls, prompt: str, rest: list) -> None:
        if prompt == config.default_cli_prompt and not rest:
            raise CliErrors(None, "no_site", f"sites {VALIDSITES}")

    @classmethod
    def chk_prompt(cls, prompt: str) -> None:
        if prompt == config.default_cli_prompt:
            return None

        if prompt not in VALIDSITES:
            raise CliErrors(prompt, "chars_prompt", f"sites {VALIDSITES}")

        cls.site_slug = prompt

    @classmethod
    def chk_user_prompt(cls, rest) -> None:
        if not bool(rest):
            return None

        rest, *_ = rest

        if not bool(rest):
            raise CliErrors(None, "no_site", f"sites {VALIDSITES}")

        if rest not in VALIDSITES:
            raise CliErrors(rest, "site_prompt", f"sites {VALIDSITES}")

        cls.site_slug = rest

    def slug_to_site(self)  -> None:
        self.site_name = SITENAME.get(self.site_slug)

    def check_input(self, line: str, prompt) -> Streamer:
        try:

            name_, *rest = self.input(line)

            self.name_chars(name_)
            self.has_cam_site(prompt, rest)
            self.chk_prompt(prompt)
            self.chk_user_prompt(rest)
            self.slug_to_site()

            return Streamer(name_, self.site_slug, self.site_name)
        except CliErrors as e:
            print(e)
            return Streamer(None, None, None)
