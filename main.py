import os
import time
import itertools
import urllib
import json

from datetime import datetime
from functools import partial, reduce
from dataclasses import dataclass

import feedparser

# Utils

def compose(*functions):
    return reduce(lambda f, g: lambda x: f(g(x)), functions)


# Logger

def log(message, *paramaters):
    msg = message.replace('{}', '\033[97m{}\033[0m').format(*paramaters) if paramaters else message
    print(f'[\033[2m{datetime.now():%Y-%m-%d %H:%M:%S}\033[0m] {msg}')


# Configuration

def load_configuration_file(file_path):
    with open(file_path) as json_file:
        return json.load(json_file)


# Downloaded directory

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


# RSS

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

prepare_rss_data_from = compose(
    partial(filter, has_entry_podcast_link),
    partial(map, strip_data),
    get_raw_rss_entries_from_web)


# Main script

def only_new_entites(last_downloaded_file: str, raw_rss_entries: [RSSEntity]) -> [RSSEntity]:
    return itertools.takewhile(
        lambda rss_entity: rss_entity.to_file_name() != last_downloaded_file,
        raw_rss_entries)

def download_rss_entity_to_path(path, rss_entity: RSSEntity):
    return urllib.request.urlretrieve(
        rss_entity.link,
        os.path.join(path, rss_entity.to_file_name()))

if __name__ == '__main__':
    import sys

    CONFIG_FILE = 'config.json'
    log('Loading configuration (from file: "{}")', CONFIG_FILE)
    CONFIG = load_configuration_file(CONFIG_FILE)

    DOWNLOADS_LIMITS = int(sys.argv[2]) \
        if len(sys.argv) > 2 and sys.argv[1] == '--downloads_limit' and sys.argv[2].isalnum() \
        else sys.maxsize

    for rss_source in CONFIG:
        rss_source_name = rss_source['name']
        rss_source_path = rss_source['path']
        rss_source_link = rss_source['rss_link']
        rss_require_date = rss_source.get('require_date', False)
        rss_disable = rss_source.get('disable', False)

        if rss_disable:
            log('Skipping the "{}"', rss_source_name)
            continue

        log('Checking "{}"', rss_source_name)

        last_downloaded_file = get_last_downloaded(rss_source_path)
        log('Last downloaded file "{}"', last_downloaded_file)

        rss_entiy_builder = partial(
            build_rss_entity,
            RSSEntityWithDate if rss_require_date else RSSEntitySimpleName)

        missing_files_links = compose(
            list,
            partial(only_new_entites, last_downloaded_file),
            partial(map, rss_entiy_builder),
            prepare_rss_data_from
        )(rss_source_link)

        if missing_files_links:
            for rss_entry in reversed(missing_files_links):
                if DOWNLOADS_LIMITS == 0:
                    continue

                log('{}: Downloading file: "{}"', rss_source_name, rss_entry.link)
                download_rss_entity_to_path(rss_source_path, rss_entry)
                DOWNLOADS_LIMITS -= 1
        else:
            log('{}: Nothing new', rss_source_name)

        log('-' * 30)

    log('Script finished')
