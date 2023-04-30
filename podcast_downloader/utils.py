from functools import reduce
from datetime import datetime
from logging import Formatter, WARNING, ERROR


class ConsoleOutputFormatter(Formatter):
    COLORS = {
        WARNING: " \033[33mWarning:\033[0m",
        ERROR: " \033[31mError:\033[0m",
    }

    def format(self, record):
        record.msg = (
            record.msg.replace("%s", "\033[97m%s\033[0m").replace(
                "%d", "\033[97m%d\033[0m"
            )
            if record.args
            else record.msg
        )
        level = self.COLORS[record.levelno] if record.levelno in self.COLORS else ""

        return f"[\033[2m{datetime.now():%Y-%m-%d %H:%M:%S}\033[0m]{level} {record.getMessage()}"


def compose(*functions):
    return reduce(lambda f, g: lambda x: f(g(x)), functions)
