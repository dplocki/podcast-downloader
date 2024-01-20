import random
import string


def generate_random_string(length: int = 7) -> str:
    letters = string.ascii_letters
    random_string = "".join(random.choice(letters) for _ in range(length))
    return random_string


def generate_random_sentence(word_count: int) -> str:
    return (
        " ".join(
            generate_random_string(random.randrange(4, 7)) for _ in range(word_count)
        ).capitalize()
        + "."
    )
