import os
import urllib
import argparse
import re
import time

from functools import partial
from . import configuration

from podcast_downloader.configuration import configuration_verification
from .utils import log, compose
from .downloaded import get_extensions_checker, get_last_downloaded
from .parameters import merge_parameters_collection, load_configuration_file, parse_argv
from .rss import (
    RSSEntity,
    build_flatten_rss_links_data,
    build_only_allowed_filter_for_link_data,
    RSSEntitySimpleName,
    RSSEntityWithDate,
    get_raw_rss_entries_from_web,
    only_new_entities,
    only_last_entity,
    get_n_age_date,
    only_entities_from_date,
)


def download_rss_entity_to_path(path, rss_entity: RSSEntity):
    return urllib.request.urlretrieve(
        rss_entity.link, os.path.join(path, rss_entity.to_file_name())
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--downloads_limit",
        required=False,
        type=int,
        help="The maximum number of mp3 files which script will download",
    )

    parser.add_argument(
        "--if_directory_empty",
        required=False,
        type=str,
        help="The general approach on empty directory",
    )

    return parser


def configuration_to_function(config: dict):
    configuration_value = config[configuration.CONFIG_IF_DIRECTORY_EMPTY]

    if configuration_value == "download_last":
        return only_last_entity

    from_n_day_match = re.match(r"^download_from_(\d+)_days$", configuration_value)
    if from_n_day_match:
        from_date = get_n_age_date(int(from_n_day_match[1]), time.localtime())
        return only_entities_from_date(from_date)

    raise Exception(f"The value the '{configuration_value}' is not recognizable")


if __name__ == "__main__":
    import sys

    DEFAULT_CONFIGURATION = {
        configuration.CONFIG_DOWNLOADS_LIMIT: sys.maxsize,
        configuration.CONFIG_IF_DIRECTORY_EMPTY: "download_last",
        configuration.CONFIG_PODCAST_EXTENSIONS: {".mp3": "audio/mpeg"},
        configuration.CONFIG_PODCASTS: [],
    }

    CONFIG_FILE = "~/.podcast_downloader_config.json"
    log('Loading configuration (from file: "{}")', CONFIG_FILE)

    CONFIGURATION = merge_parameters_collection(
        DEFAULT_CONFIGURATION,
        load_configuration_file(os.path.expanduser(CONFIG_FILE)),
        parse_argv(build_parser()),
    )

    is_valid, error = configuration_verification(CONFIGURATION)
    if not is_valid:
        log("There is a problem with configuration file: {}", error)
        exit(1)

    RSS_SOURCES = CONFIGURATION[configuration.CONFIG_PODCASTS]
    DOWNLOADS_LIMITS = CONFIGURATION[configuration.CONFIG_DOWNLOADS_LIMIT]

    on_directory_empty = configuration_to_function(CONFIGURATION)

    for rss_source in RSS_SOURCES:
        rss_source_name = rss_source[configuration.CONFIG_PODCASTS_NAME]
        rss_source_path = rss_source[configuration.CONFIG_PODCASTS_PATH]
        rss_source_link = rss_source[configuration.CONFIG_PODCASTS_RSS_LINK]
        rss_require_date = rss_source.get(
            configuration.CONFIG_PODCASTS_REQUIRE_DATE, False
        )
        rss_disable = rss_source.get(configuration.CONFIG_PODCASTS_DISABLE, False)
        rss_podcast_extensions = rss_source.get(
            configuration.CONFIG_PODCAST_EXTENSIONS,
            CONFIGURATION[configuration.CONFIG_PODCAST_EXTENSIONS],
        )

        if rss_disable:
            log('Skipping the "{}"', rss_source_name)
            continue

        log('Checking "{}"', rss_source_name)

        last_downloaded_file = get_last_downloaded(
            get_extensions_checker(rss_podcast_extensions), rss_source_path
        )

        log('Last downloaded file "{}"', last_downloaded_file or "<none>")

        download_limiter_function = (
            partial(only_new_entities, last_downloaded_file)
            if last_downloaded_file
            else on_directory_empty
        )

        allow_link_types = list(set(rss_podcast_extensions.values()))
        missing_files_links = compose(
            list,
            download_limiter_function,
            partial(filter, build_only_allowed_filter_for_link_data(allow_link_types)),
            build_flatten_rss_links_data(
                RSSEntityWithDate if rss_require_date else RSSEntitySimpleName
            ),
            get_raw_rss_entries_from_web,
        )(rss_source_link)

        if missing_files_links:
            for rss_entry in reversed(missing_files_links):
                if DOWNLOADS_LIMITS == 0:
                    continue

                log('{}: Downloading file: "{}"', rss_source_name, rss_entry.link)
                download_rss_entity_to_path(rss_source_path, rss_entry)
                DOWNLOADS_LIMITS -= 1
        else:
            log("{}: Nothing new", rss_source_name)

        log("-" * 30)

    log("Finished")
