from podcast_downloader.rss import RSSEntityWithDate


def build_timestamp(year: int, month: int, day: int):
    return (year, month, day, 17, 3, 38, 1, 48, 0)


def rss_entity_generator(day: int = 10, file_number: int = 5, limit: int = 5) -> list:
    while limit:
        yield RSSEntityWithDate(
            build_timestamp(2020, 1, day), f"http://www.p.com/file{file_number:0>4}.mp3"
        )

        day -= 1
        file_number -= 1
        limit -= 1
