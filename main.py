import os
import time
from dataclasses import dataclass

import feedparser


def get_downloaded_files(podcast_directory: str) -> [str]:
    return (file
            for file in sorted(os.listdir(podcast_directory), reverse=True)
            if file.endswith('.mp3') and os.path.isfile(os.path.join(podcast_directory, file)))


def file_name_to_entry_link_name(link: str) -> str:
    return link[11:]


@dataclass
class RSSEntity():
    published_date: time.struct_time
    link: str

    def to_file_name(self) -> str:
        podcast_name = self.link.rpartition('/')[-1]
        return f'[{time.strftime("%Y%m%d", self.published_date)}] {podcast_name.lower()}'


def get_raw_rss_entries(rss_link: str) -> list:
    yield from feedparser.parse(rss_link).entries


def repacked_rss_entries(rss_entries: []) -> []:

    def extract_podcast_files(entry) -> []:
        return filter(lambda l: l.type == 'audio/mpeg', entry.links)

    return (
        (rss_entry.published_parsed, extract_podcast_files(rss_entry))
        for rss_entry in rss_entries
    )


def only_podcast_entries(rss_entries: []) -> [RSSEntity]:
    return (
        RSSEntity(published_date, links[0].href)
        for published_date, links in
        ((published_date, list(links)) for published_date, links in rss_entries)
        if len(links) > 0
    )
