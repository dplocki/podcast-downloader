import os
import time
import itertools
import urllib
import json

from datetime import datetime
from functools import partial
from dataclasses import dataclass

import feedparser


# Logger

def log(msg, paramaters=None):
    if paramaters:
        paramaters = paramaters if isinstance(paramaters, list) else [paramaters]
        message = msg.replace('{}', '\033[97m{}\033[0m').format(*paramaters)
    else:
        message = msg

    print(f'[\033[2m{datetime.now():%Y-%m-%d %H:%M:%S}\033[0m] {message}')


# Downloaded directory

def file_name_to_entry_link_name(link: str) -> str:
    return link[11:]


def get_last_downloaded(podcast_directory: str):

    def get_downloaded_files(podcast_directory: str) -> [str]:
        return (file
                for file in sorted(os.listdir(podcast_directory), reverse=True)
                if file.endswith('.mp3') and os.path.isfile(os.path.join(podcast_directory, file)))

    return next(get_downloaded_files(podcast_directory))


# RSS

@dataclass
class RSSEntity():
    published_date: time.struct_time
    link: str

    def to_file_name(self) -> str:
        podcast_name = self.link.rpartition('/')[-1]
        return f'[{time.strftime("%Y%m%d", self.published_date)}] {podcast_name.lower()}'


def get_raw_rss_entries_from_web(rss_link: str) -> list:
    yield from feedparser.parse(rss_link).entries


def get_rss_entities(get_raw_rss_entries):

    def strip_data(raw_rss_entry: {}) -> ():

        def only_audio(link):
            return link.type == 'audio/mpeg'

        return (raw_rss_entry.published_parsed, list(filter(only_audio, raw_rss_entry.links)))

    def has_entry_podcast_link(strip_rss_entry: {}) -> bool:
        return len(strip_rss_entry[1]) > 0

    def build_rss_entity(strip_rss_entry: {}) -> RSSEntity:
        return RSSEntity(strip_rss_entry[0], strip_rss_entry[1][0].href)

    return map(
        build_rss_entity,
        filter(
            has_entry_podcast_link,
            map(
                strip_data,
                get_raw_rss_entries())))


# Main script

def only_new_entites(get_raw_rss_entries, get_last_downloaded_file) -> [RSSEntity]:
    last_downloaded_file = get_last_downloaded_file()

    return itertools.takewhile(
        lambda rss_entity: rss_entity.to_file_name() != last_downloaded_file,
        get_raw_rss_entries())


def build_to_download_list(podcast_directory: str, rss_link: str):
    get_last_downloaded_file = partial(get_last_downloaded, podcast_directory)
    get_all_rss_entities = partial(
        get_rss_entities,
        partial(get_raw_rss_entries_from_web, rss_link))

    return only_new_entites(get_all_rss_entities, get_last_downloaded_file)


def download_new_entries(rss_link: str, path: str):
    result = reversed(list(build_to_download_list(path, rss_link)))
    for link in result:
        urllib.request.urlretrieve(link, path)


with open('config.json') as json_file:
    CONFIG = json.load(json_file)

    for rss_source in CONFIG:
        download_new_entries(rss_source['rss_link'], rss_source['path'])
