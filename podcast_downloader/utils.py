from functools import reduce
from logging import Formatter, WARNING, ERROR


class ConsoleOutputFormatter(Formatter):
    COLORS = {
        WARNING: "\033[33mWarning:\033[0m",
        ERROR: "\033[31mError:\033[0m",
    }

    def __init__(self) -> None:
        super().__init__("[\033[2m%(asctime)s\033[0m] %(message)s", "%Y-%m-%d %H:%M:%S")

    def format(self, record):
        if record.args:
            record.msg = record.msg.replace("%s", "\033[97m%s\033[0m").replace(
                "%d", "\033[97m%d\033[0m"
            )

        if record.levelno in self.COLORS:
            record.msg = f"{self.COLORS[record.levelno]} {record.msg}"

        return super().format(record)


def compose(*functions):
    return reduce(lambda f, g: lambda x: f(g(x)), functions)
