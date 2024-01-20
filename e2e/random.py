import random
import string


def generate_random_string(length: int = 7) -> str:
    return "".join(random.choice(string.ascii_letters) for _ in range(length))


def generate_random_sentence(word_count: int) -> str:
    return (
        " ".join(
            generate_random_string(random.randrange(4, 7)) for _ in range(word_count)
        ).capitalize()
        + "."
    )
