import os
from typing import Callable, Dict, Iterable
import urllib
import argparse
import re
import time

from functools import partial
from . import configuration

from podcast_downloader.configuration import (
    configuration_verification,
    get_label_to_date,
    get_n_age_date,
    parse_day_label,
)
from .utils import log, compose, warning
from .downloaded import get_extensions_checker, get_last_downloaded
from .parameters import merge_parameters_collection, load_configuration_file, parse_argv
from .rss import (
    RSSEntity,
    build_only_allowed_filter_for_link_data,
    build_only_new_entities,
    file_template_to_file_name,
    flatten_rss_links_data,
    get_raw_rss_entries_from_web,
    only_last_entity,
    only_entities_from_date,
)


def download_rss_entity_to_path(
    to_file_name_function: Callable[[RSSEntity], str], path: str, rss_entity: RSSEntity
):
    return urllib.request.urlretrieve(
        rss_entity.link, os.path.join(path, to_file_name_function(rss_entity))
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


def configuration_to_function_on_empty_directory(
    configuration_value: str,
) -> Callable[[Iterable[RSSEntity]], Iterable[RSSEntity]]:
    if configuration_value == "download_last":
        return only_last_entity

    if configuration_value == "download_all_from_feed":
        return lambda source: source

    local_time = time.localtime()

    from_n_day_match = re.match(r"^download_from_(\d+)_days$", configuration_value)
    if from_n_day_match:
        from_date = get_n_age_date(int(from_n_day_match[1]), local_time)
        return only_entities_from_date(from_date)

    from_nth_day_match = re.match(r"^download_from_(.*)", configuration_value)
    if from_nth_day_match:
        day_label = parse_day_label(from_nth_day_match[1])

        return only_entities_from_date(get_label_to_date(day_label)(local_time))

    raise Exception(f"The value the '{configuration_value}' is not recognizable")


def configuration_to_function_rss_to_name(
    configuration_value: str, sub_configuration: Dict[str, str]
) -> Callable[[RSSEntity], str]:
    if (
        configuration.CONFIG_PODCASTS_REQUIRE_DATE in sub_configuration
        and configuration.CONFIG_FILE_NAME_TEMPLATE not in sub_configuration
    ):
        default_file_name_template_with_date = (
            "[%publish_date%] %file_name%.%file_extension%"
        )

        if sub_configuration[configuration.CONFIG_PODCASTS_REQUIRE_DATE]:
            configuration_value = default_file_name_template_with_date

        warning(
            'The option {} is deprecated, please replace use of it with the {} option: "{}"',
            configuration.CONFIG_PODCASTS_REQUIRE_DATE,
            configuration.CONFIG_FILE_NAME_TEMPLATE,
            default_file_name_template_with_date,
        )

    return partial(file_template_to_file_name, configuration_value)


if __name__ == "__main__":
    import sys

    DEFAULT_CONFIGURATION = {
        configuration.CONFIG_DOWNLOADS_LIMIT: sys.maxsize,
        configuration.CONFIG_IF_DIRECTORY_EMPTY: "download_last",
        configuration.CONFIG_PODCAST_EXTENSIONS: {".mp3": "audio/mpeg"},
        configuration.CONFIG_FILE_NAME_TEMPLATE: "%file_name%.%file_extension%",
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

    for rss_source in RSS_SOURCES:
        rss_source_name = rss_source[configuration.CONFIG_PODCASTS_NAME]
        rss_source_path = rss_source[configuration.CONFIG_PODCASTS_PATH]
        rss_source_link = rss_source[configuration.CONFIG_PODCASTS_RSS_LINK]
        rss_disable = rss_source.get(configuration.CONFIG_PODCASTS_DISABLE, False)
        rss_file_name_template_value = rss_source.get(
            configuration.CONFIG_FILE_NAME_TEMPLATE,
            CONFIGURATION[configuration.CONFIG_FILE_NAME_TEMPLATE],
        )
        rss_if_directory_empty = rss_source.get(
            configuration.CONFIG_IF_DIRECTORY_EMPTY,
            CONFIGURATION[configuration.CONFIG_IF_DIRECTORY_EMPTY],
        )
        rss_podcast_extensions = rss_source.get(
            configuration.CONFIG_PODCAST_EXTENSIONS,
            CONFIGURATION[configuration.CONFIG_PODCAST_EXTENSIONS],
        )

        if rss_disable:
            log('Skipping the "{}"', rss_source_name)
            continue

        log('Checking "{}"', rss_source_name)

        to_name_function = configuration_to_function_rss_to_name(
            rss_file_name_template_value, rss_source
        )
        on_directory_empty = configuration_to_function_on_empty_directory(
            rss_if_directory_empty
        )
        last_downloaded_file = get_last_downloaded(
            get_extensions_checker(rss_podcast_extensions), rss_source_path
        )

        download_limiter_function = (
            partial(build_only_new_entities(to_name_function), last_downloaded_file)
            if last_downloaded_file
            else on_directory_empty
        )

        allow_link_types = list(set(rss_podcast_extensions.values()))
        missing_files_links = compose(
            list,
            download_limiter_function,
            partial(filter, build_only_allowed_filter_for_link_data(allow_link_types)),
            flatten_rss_links_data,
            get_raw_rss_entries_from_web,
        )(rss_source_link)

        log('Last downloaded file "{}"', last_downloaded_file or "<none>")

        if missing_files_links:
            download_files = partial(download_rss_entity_to_path, to_name_function)

            for rss_entry in reversed(missing_files_links):
                if DOWNLOADS_LIMITS == 0:
                    continue

                log(
                    '{}: Downloading file: "{}" saved as "{}"',
                    rss_source_name,
                    rss_entry.link,
                    to_name_function(rss_entry),
                )

                download_files(rss_source_path, rss_entry)
                DOWNLOADS_LIMITS -= 1
        else:
            log("{}: Nothing new", rss_source_name)

        log("-" * 30)

    log("Finished")
