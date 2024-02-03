from itertools import chain
import random
import string
from typing import Callable, Iterable, List


def generate_random_int(start: int = 4, end: int = 7) -> int:
    return random.randrange(start, end)


def generate_random_string(length: int = 7) -> str:
    return "".join(random.choice(string.ascii_letters) for _ in range(length))


def generate_random_sentence(word_count: int) -> str:
    return (
        " ".join(
            generate_random_string(generate_random_int()) for _ in range(word_count)
        ).capitalize()
        + "."
    )


def generate_random_mp3_file() -> str:
    return generate_random_string() + ".mp3"


def generate_random_file(extension: str) -> str:
    return generate_random_string() + extension


def call_n_times(generator: Callable[[], str], n: int = None) -> List[str]:
    return [generator() for _ in range(n or generate_random_int())]


def randomize_iterables(*arguments: Iterable[Iterable]) -> Iterable:
    result = list(chain.from_iterable(arguments))
    random.shuffle(result)

    return result
