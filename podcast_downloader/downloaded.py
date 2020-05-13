import os

from functools import partial


def only_mp3(file_name: str) -> bool:
    return file_name.endswith('.mp3')

def is_file(directory_path: str, file_name: str) -> bool:
    return os.path.isfile(os.path.join(directory_path, file_name))

def get_files_from(directory_path: str):
    return sorted(os.listdir(directory_path), reverse=True)

def get_downloaded_files(podcast_directory: str) -> [str]:
    is_directory_file = partial(is_file, podcast_directory)

    return (file
            for file in get_files_from(podcast_directory)
            if only_mp3(file) and is_directory_file(file))

def get_last_downloaded(podcast_directory: str):
    return next(get_downloaded_files(podcast_directory))
