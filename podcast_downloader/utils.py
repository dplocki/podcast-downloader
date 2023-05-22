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

        message = f"[\033[2m{datetime.now():%Y-%m-%d %H:%M:%S}\033[0m]{level} {record.getMessage()}"

        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            if message[-1:] != "\n":
                message = message + "\n"
            message = message + record.exc_text
        if record.stack_info:
            if message[-1:] != "\n":
                message = message + "\n"
            message = message + self.formatStack(record.stack_info)

        return message


def compose(*functions):
    return reduce(lambda f, g: lambda x: f(g(x)), functions)
