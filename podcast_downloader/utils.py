from functools import reduce
from datetime import datetime


def mark_parameters_in_message(message: str, *parameters) -> str:
    return (
        message.replace("{}", "\033[97m{}\033[0m").format(*parameters)
        if parameters
        else message
    )


def log(message, *parameters):
    print(
        f"[\033[2m{datetime.now():%Y-%m-%d %H:%M:%S}\033[0m] {mark_parameters_in_message(message, *parameters)}"
    )


def warning(message, *parameters):
    print(
        f"[\033[2m{datetime.now():%Y-%m-%d %H:%M:%S}\033[0m] \033[33mWarning:\033[0m {mark_parameters_in_message(message, *parameters)}"
    )


def compose(*functions):
    return reduce(lambda f, g: lambda x: f(g(x)), functions)
