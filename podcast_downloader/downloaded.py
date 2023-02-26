import os

from functools import partial
from typing import Callable, List


def get_extensions_checker(extensions: List[str]) -> Callable[[str], bool]:
    return lambda file_name: any(
        file_name.endswith(extension) for extension in extensions
    )


def is_file(directory_path: str, file_name: str) -> bool:
    return os.path.isfile(os.path.join(directory_path, file_name))


def get_files_from(directory_path: str) -> List[str]:
    sort_key_function = lambda file_name: os.path.getctime(
        os.path.join(directory_path, file_name)
    )
    return sorted(os.listdir(directory_path), key=sort_key_function, reverse=True)


def get_downloaded_files(
    podcast_files_filter: Callable[[str], bool], podcast_directory: str
) -> List[str]:
    is_directory_file = partial(is_file, podcast_directory)

    return (
        file
        for file in get_files_from(podcast_directory)
        if podcast_files_filter(file) and is_directory_file(file)
    )
