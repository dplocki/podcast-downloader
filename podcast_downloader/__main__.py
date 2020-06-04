import os
import urllib
import json
import argparse

from functools import partial
from .utils import log, compose
from .downloaded import get_last_downloaded
from .rss import RSSEntity,\
        build_rss_entity,\
        RSSEntitySimpleName,\
        RSSEntityWithDate,\
        prepare_rss_data_from,\
        only_new_entites

def parse_argv(args=None):
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--downloads_limit",
        required=False,
        type=int,
        help='The maximum number of mp3 files which script will download')

    return parser.parse_args(args)

def load_configuration_file(file_path):
    if not os.path.isfile(file_path):
        raise Exception(f'Cannot read from configuration file "{file_path}"')

    with open(file_path) as json_file:
        return json.load(json_file)

def set_dafault_values(collection: dict, default_collection: dict) -> dict:
    return {
        key: (collection[key]
              if key in collection
              else default_collection[key])
        for key, value in default_collection.items()
    }

def download_rss_entity_to_path(path, rss_entity: RSSEntity):
    return urllib.request.urlretrieve(
        rss_entity.link,
        os.path.join(path, rss_entity.to_file_name()))

if __name__ == '__main__':
    import sys

    ARGS = parse_argv()
    CONFIG_FILE = '~/.podcast_downloader_config.json'
    log('Loading configuration (from file: "{}")', CONFIG_FILE)

    CONFIGURATION = set_dafault_values(
        load_configuration_file(os.path.expanduser(CONFIG_FILE)),
        {
            'downloads_limit': sys.maxsize,
            'podcasts': []
        })

    RSS_SOURCES = CONFIGURATION['podcasts']
    DOWNLOADS_LIMITS = ARGS.downloads_limit \
        if ARGS.downloads_limit \
        else CONFIGURATION['downloads_limit'] or sys.maxsize

    for rss_source in RSS_SOURCES:
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

    log('Finished')
