import random
import string
from typing import Callable, List


def generate_random_string(length: int = 7) -> str:
    return "".join(random.choice(string.ascii_letters) for _ in range(length))


def generate_random_sentence(word_count: int) -> str:
    return (
        " ".join(
            generate_random_string(random.randrange(4, 7)) for _ in range(word_count)
        ).capitalize()
        + "."
    )


def generate_random_mp3_file():
    return generate_random_string() + ".mp3"


def call_n_times(generator: Callable[[], str], n: int = None) -> List[str]:
    return [generator() for _ in range(n or random.randint(4, 7))]
