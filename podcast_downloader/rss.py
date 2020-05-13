import time
from dataclasses import dataclass
from functools import partial
from itertools import takewhile

import feedparser
from .utils import compose


@dataclass
class RSSEntity():
    published_date: time.struct_time
    link: str

@dataclass
class RSSEntitySimpleName(RSSEntity):

    def to_file_name(self) -> str:
        return self.link.rpartition('/')[-1].lower()

@dataclass
class RSSEntityWithDate(RSSEntity):

    def to_file_name(self) -> str:
        podcast_name = RSSEntitySimpleName.to_file_name(self)
        return f'[{time.strftime("%Y%m%d", self.published_date)}] {podcast_name}'

def build_rss_entity(constructor, strip_rss_entry):
    return constructor(strip_rss_entry[0], strip_rss_entry[1][0].href)

def get_raw_rss_entries_from_web(rss_link: str) -> list:
    yield from feedparser.parse(rss_link).entries

def is_audio(link: {}) -> bool:
    return link.type == 'audio/mpeg'

def only_audio(links: [{}]) -> bool:
    return filter(is_audio, links)

def strip_data(raw_rss_entry: {}) -> ():
    return (raw_rss_entry.published_parsed, list(only_audio(raw_rss_entry.links)))

def has_entry_podcast_link(strip_rss_entry: {}) -> bool:
    return len(strip_rss_entry[1]) > 0

prepare_rss_data_from = compose( # pylint: disable=invalid-name#it's a function
    partial(filter, has_entry_podcast_link),
    partial(map, strip_data),
    get_raw_rss_entries_from_web)

def only_new_entites(from_file: str, raw_rss_entries: [RSSEntity]) -> [RSSEntity]:
    return takewhile(lambda rss_entity: rss_entity.to_file_name() != from_file, raw_rss_entries)
