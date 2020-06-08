import os
import urllib
import argparse

from functools import partial
from .utils import log, compose
from .downloaded import get_last_downloaded
from .parameters import merge_parameters_collection, load_configuration_file, parse_argv
from .rss import RSSEntity,\
        build_rss_entity,\
        RSSEntitySimpleName,\
        RSSEntityWithDate,\
        prepare_rss_data_from,\
        only_new_entites

def download_rss_entity_to_path(path, rss_entity: RSSEntity):
    return urllib.request.urlretrieve(
        rss_entity.link,
        os.path.join(path, rss_entity.to_file_name()))

def build_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--downloads_limit",
        required=False,
        type=int,
        help='The maximum number of mp3 files which script will download')

    return parser


if __name__ == '__main__':
    import sys

    DEFAULT_CONFIGURATION = {
        'downloads_limit': sys.maxsize,
        'podcasts': []
    }

    CONFIG_FILE = '~/.podcast_downloader_config.json'
    log('Loading configuration (from file: "{}")', CONFIG_FILE)

    CONFIGURATION = merge_parameters_collection(
        DEFAULT_CONFIGURATION,
        load_configuration_file(os.path.expanduser(CONFIG_FILE)),
        parse_argv(build_parser())
    )

    RSS_SOURCES = CONFIGURATION['podcasts']
    DOWNLOADS_LIMITS = CONFIGURATION['downloads_limit']

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
