import time
from dataclasses import dataclass
from functools import partial
from itertools import takewhile, islice
from typing import Callable, Generator, Iterator, List

import feedparser


@dataclass
class RSSEntity:
    published_date: time.struct_time
    type: str
    link: str


def to_plain_file_name(entity: RSSEntity) -> str:
    filename = entity.link.rpartition("/")[-1].lower()
    if filename.find("?") > 0:
        filename = filename.rpartition("?")[0]

    return filename


def to_name_with_date_name(entity: RSSEntity) -> str:
    podcast_name = to_plain_file_name(entity)
    return f'[{time.strftime("%Y%m%d", entity.published_date)}] {podcast_name}'


def get_raw_rss_entries_from_web(
    rss_link: str,
) -> Generator[feedparser.FeedParserDict, None, None]:
    yield from feedparser.parse(rss_link).entries


def flatten_rss_links_data(
    source: Generator[feedparser.FeedParserDict, None, None]
) -> Generator[RSSEntity, None, None]:
    return (
        RSSEntity(rss_entry.published_parsed, link.type, link.href)
        for rss_entry in source
        for link in rss_entry.links
    )


def build_only_allowed_filter_for_link_data(
    allowed_types: List[str],
) -> Callable[[RSSEntity], bool]:
    return lambda link_data: link_data.type in allowed_types


def build_only_new_entities(
    to_name_function: Callable[[RSSEntity], str]
) -> Callable[[str, List[RSSEntity]], Generator[RSSEntity, None, None]]:
    return lambda from_file, raw_rss_entries: takewhile(
        lambda rss_entity: to_name_function(rss_entity) != from_file, raw_rss_entries
    )


def only_last_entity(raw_rss_entries: Iterator[RSSEntity]) -> Iterator[RSSEntity]:
    return islice(raw_rss_entries, 1)


def is_entity_newer(from_date: time.struct_time, entity: RSSEntity) -> bool:
    return entity.published_date[:3] >= from_date[:3]


def only_entities_from_date(from_date: time.struct_time) -> Callable[[RSSEntity], bool]:
    return partial(filter, partial(is_entity_newer, from_date))
