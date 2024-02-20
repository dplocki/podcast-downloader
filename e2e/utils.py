from typing import Callable


def add_prefix(prefix: str, callable: Callable[[], str]) -> Callable[[], str]:
    def internal():
        return prefix + callable()

    return internal
