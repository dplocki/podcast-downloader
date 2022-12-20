from typing import Generator, Tuple
from podcast_downloader.rss import RSSEntity


def build_timestamp(
    year: int, month: int, day: int
) -> Tuple[int, int, int, int, int, int, int, int, int]:
    return (year, month, day, 17, 3, 38, 1, 48, 0)


def rss_entity_generator(
    day: int = 10, file_number: int = 5, limit: int = 5
) -> Generator[RSSEntity, None, None]:
    for index in range(limit):
        yield RSSEntity(
            build_timestamp(2020, 1, day - index),
            "Title",
            "audio/mp3",
            f"http://www.p.com/file{(file_number - index):0>4}.mp3",
        )
