from dataclasses import dataclass


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