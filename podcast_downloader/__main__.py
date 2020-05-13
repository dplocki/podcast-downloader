import os
import urllib
import json

from functools import partial
from .utils import log, compose
from .downloaded import get_last_downloaded
from .rss import RSSEntity,\
        build_rss_entity,\
        RSSEntitySimpleName,\
        RSSEntityWithDate,\
        prepare_rss_data_from,\
        only_new_entites


def load_configuration_file(file_path):
    with open(file_path) as json_file:
        return json.load(json_file)

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

    log('Finished')
