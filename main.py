import os
from dataclasses import dataclass
from datetime import datetime

import feedparser


def get_downloaded_files(podcast_directory: str) -> [str]:
    yield from sorted(os.listdir(podcast_directory))


@dataclass
class RSSEntity():
    published_date: datetime
    link: str


def get_raw_rss_entries(rss_link: str) -> list:
    yield from feedparser.parse(rss_link).entries


def build_entry(entry) -> RSSEntity:
    return RSSEntity(entry.published_parsed, entry.links[0].href)


def get_rss_entries(rss_link) -> RSSEntity:
    return (build_entry(entry) for entry in get_raw_rss_entries(rss_link))
