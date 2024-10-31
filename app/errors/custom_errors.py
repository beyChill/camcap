from dataclasses import dataclass, field
from time import strftime
from typing import Dict

from termcolor import colored


@dataclass(
    slots=True,
    init=False,
    frozen=True,
    repr=False,
    eq=False,
)
class CaptureError(Exception):
    msg: str

    def __init__(self, msg) -> None:
        object.__setattr__(self, "msg", msg)

@dataclass(slots=True)
class GetDataError(Exception):
    name_: str
    key_: str
    code: int
    loader: str
    pre_text: str = field(init=False)
    ERROR_RESPONSE: Dict = field(init=False)

    def __post_init__(self):
        self.pre_text = f"{colored("[FAIL] " + strftime("%H:%M:%S") ,'red')}: (Code: {self.code}) module: {self.loader} \n\t"
        self.ERROR_RESPONSE = {
            "429": self.pre_text + f"Chaturbate {colored('API overun','red')} with too many request",
            "not200": self.pre_text + f"Unable to retrieve stream data for {colored(self.name_,'red')}",
            "notfound": self.pre_text + f"{colored(self.name_,'red')} is not a Chaturbate Streamer",
        }

    def __str__(self):
        data = self.ERROR_RESPONSE.get(self.key_)
        return data
    
@dataclass(slots=True)
class CliErrors(Exception):
    name_: str
    key_: str
    hint: str
    pre_text: str = field(init=False)
    ERROR_RESPONSE: Dict = field(init=False)

    def __post_init__(self):
        self.pre_text = f"{colored("[FAIL] " + strftime("%H:%M:%S") ,'red')}: Assistance: {self.hint} \n\t"
        self.ERROR_RESPONSE = {
            "input":self.pre_text + f"Command missing {colored('model name','red')} and {colored('site abbreviation','red')}",
            "chars": self.pre_text + f"Model's name, {colored(self.name_, 'red')} is invalid",
            "site_prompt": self.pre_text + f"Unknown streaming site: {colored(self.name_,'red')}",
            "no_site":self.pre_text + f"add {colored('streamer site', 'red')} to command",
            "chars_site":self.pre_text + f"Only use alpha characters for site,{colored({self.name_},'red')}"
        }

    def __str__(self):
        error = self.ERROR_RESPONSE.get(self.key_)
        return error