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
    value: str
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
        data = self.ERROR_RESPONSE[self.value]
        return data