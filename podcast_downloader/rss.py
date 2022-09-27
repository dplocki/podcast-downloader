from datetime import datetime
import time
from dataclasses import dataclass
from functools import partial
from itertools import takewhile, islice
from typing import Callable, Generator, List

import feedparser


SECONDS_IN_DAY = 24 * 60 * 60


@dataclass
class RSSEntity:
    published_date: time.struct_time
    type: str
    link: str


@dataclass
class RSSEntitySimpleName(RSSEntity):
    def to_file_name(self) -> str:
        filename = self.link.rpartition("/")[-1].lower()
        if filename.find("?") > 0:
            filename = filename.rpartition("?")[0]
        return filename


@dataclass
class RSSEntityWithDate(RSSEntity):
    def to_file_name(self) -> str:
        podcast_name = RSSEntitySimpleName.to_file_name(self)
        return f'[{time.strftime("%Y%m%d", self.published_date)}] {podcast_name}'


def get_raw_rss_entries_from_web(
    rss_link: str,
) -> Generator[feedparser.FeedParserDict, None, None]:
    yield from feedparser.parse(rss_link).entries


def build_flatten_rss_links_data(
    constructor: Callable[[datetime.date, str, str], RSSEntity]
) -> Callable[[], Generator[RSSEntity, None, None]]:

    return lambda source: (
        constructor(rss_entry.published_parsed, link.type, link.href)
        for rss_entry in source
        for link in rss_entry.links
    )


def build_only_allowed_filter_for_link_data(
    allowed_types: List[str],
) -> Callable[[RSSEntity], bool]:
    return lambda link_data: link_data.type in allowed_types


def only_new_entities(
    from_file: str, raw_rss_entries: List[RSSEntity]
) -> List[RSSEntity]:
    return takewhile(
        lambda rss_entity: rss_entity.to_file_name() != from_file, raw_rss_entries
    )


def only_last_entity(raw_rss_entries: List[RSSEntity]) -> List[RSSEntity]:
    return islice(raw_rss_entries, 1)


def is_entity_newer(from_date: time.struct_time, entity: RSSEntity):
    return entity.published_date[:3] >= from_date[:3]


def get_n_age_date(day_number: int, from_date: time.struct_time):
    return time.localtime(time.mktime(from_date) - day_number * SECONDS_IN_DAY)


def only_entities_from_date(from_date: time.struct_time):
    return partial(filter, partial(is_entity_newer, from_date))
