from functools import reduce
from datetime import datetime


def log(message, *paramaters):
    msg = message.replace('{}', '\033[97m{}\033[0m').format(*paramaters) if paramaters else message
    print(f'[\033[2m{datetime.now():%Y-%m-%d %H:%M:%S}\033[0m] {msg}')


def compose(*functions):
    return reduce(lambda f, g: lambda x: f(g(x)), functions)
