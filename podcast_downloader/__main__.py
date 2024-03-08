import os
from typing import Callable, Dict, Iterable, List, Tuple
import urllib
import argparse
import re
import time
import sys

from functools import partial
from . import configuration

from podcast_downloader.configuration import (
    configuration_verification,
    get_label_to_date,
    get_n_age_date,
    parse_day_label,
)
from .utils import ConsoleOutputFormatter, compose
from .downloaded import (
    get_downloaded_files,
    get_extensions_checker,
    get_last_downloaded_file_before_gap,
)
from .parameters import merge_parameters_collection, load_configuration_file, parse_argv
from .rss import (
    RSSEntity,
    build_only_allowed_filter_for_link_data,
    build_only_new_entities,
    file_template_to_file_name,
    flatten_rss_links_data,
    get_feed_title_from_feed,
    get_raw_rss_entries_from_feed,
    limit_file_name,
    load_feed,
    only_entities_from_date,
    only_last_n_entities,
)


def download_rss_entity_to_path(
    headers: List[Tuple[str, str]],
    to_file_name_function: Callable[[RSSEntity], str],
    path: str,
    rss_entity: RSSEntity,
):
    path_to_file = os.path.join(path, to_file_name_function(rss_entity))

    try:
        request = urllib.request.Request(rss_entity.link, headers=headers)

        with urllib.request.urlopen(request) as response:
            with open(path_to_file, "wb") as file:
                file.write(response.read())

    except Exception:
        logger.exception(
            'The podcast file "%s" could not be saved to disk "%s" due to the following error',
            rss_entity.link,
            path_to_file,
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
        return partial(only_last_n_entities, 1)

    if configuration_value == "download_all_from_feed":
        return lambda source: source

    local_time = time.localtime()

    from_n_day_match = re.match(r"^download_from_(\d+)_days$", configuration_value)
    if from_n_day_match:
        from_date = get_n_age_date(int(from_n_day_match[1]), local_time)
        return only_entities_from_date(from_date)

    last_n_episodes = re.match(r"^download_last_(\d+)_episodes", configuration_value)
    if last_n_episodes:
        download_limit = int(last_n_episodes[1])
        return partial(only_last_n_entities, download_limit)

    from_nth_day_match = re.match(r"^download_from_(.*)", configuration_value)
    if from_nth_day_match:
        day_label = parse_day_label(from_nth_day_match[1])

        return only_entities_from_date(get_label_to_date(day_label)(local_time))

    raise Exception(f"The value the '{configuration_value}' is not recognizable")


def is_windows_running():
    return sys.platform == "win32"


def get_system_file_name_limit(sub_configuration: Dict[str, str]) -> int:
    # on Windows, the file name is limited to 260 characters including the path to it
    return 255 if is_windows_running() else 260 - len(sub_configuration["path"]) - 1


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

        logger.warning(
            'The option %s is deprecated, please replace use of it with the %s option: "%s"',
            configuration.CONFIG_PODCASTS_REQUIRE_DATE,
            configuration.CONFIG_FILE_NAME_TEMPLATE,
            default_file_name_template_with_date,
        )

    return partial(file_template_to_file_name, configuration_value)


if __name__ == "__main__":
    import sys
    from logging import getLogger, StreamHandler, INFO

    logger = getLogger(__name__)
    logger.setLevel(INFO)
    stdout_handler = StreamHandler(stream=sys.stdout)
    stdout_handler.setFormatter(ConsoleOutputFormatter())
    logger.addHandler(stdout_handler)

    DEFAULT_CONFIGURATION = {
        configuration.CONFIG_DOWNLOADS_LIMIT: sys.maxsize,
        configuration.CONFIG_IF_DIRECTORY_EMPTY: "download_last",
        configuration.CONFIG_PODCAST_EXTENSIONS: {".mp3": "audio/mpeg"},
        configuration.CONFIG_FILE_NAME_TEMPLATE: "%file_name%.%file_extension%",
        configuration.CONFIG_HTTP_HEADER: {"User-Agent": "podcast-downloader"},
        configuration.CONFIG_FILL_UP_GAPS: False,
        configuration.CONFIG_PODCASTS: [],
    }

    CONFIG_FILE = "~/.podcast_downloader_config.json"
    logger.info('Loading configuration (from file: "%s")', CONFIG_FILE)

    CONFIGURATION = merge_parameters_collection(
        DEFAULT_CONFIGURATION,
        load_configuration_file(os.path.expanduser(CONFIG_FILE)),
        parse_argv(build_parser()),
    )

    is_valid, error = configuration_verification(CONFIGURATION)
    if not is_valid:
        logger.info("There is a problem with configuration file: %s", error)
        exit(1)

    RSS_SOURCES = CONFIGURATION[configuration.CONFIG_PODCASTS]
    DOWNLOADS_LIMITS = CONFIGURATION[configuration.CONFIG_DOWNLOADS_LIMIT]

    for rss_source in RSS_SOURCES:
        file_length_limit = get_system_file_name_limit(rss_source)
        rss_source_name = rss_source.get(configuration.CONFIG_PODCASTS_NAME, None)
        rss_source_path = os.path.expanduser(
            rss_source[configuration.CONFIG_PODCASTS_PATH]
        )
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
        rss_https_header = merge_parameters_collection(
            CONFIGURATION[configuration.CONFIG_HTTP_HEADER],
            rss_source.get(configuration.CONFIG_HTTP_HEADER, {}),
        )
        rss_fill_up_gaps = rss_source.get(
            CONFIGURATION[configuration.CONFIG_FILL_UP_GAPS],
            rss_source.get(configuration.CONFIG_FILL_UP_GAPS, False),
        )

        if rss_disable:
            logger.info('Skipping the "%s"', rss_source_name)
            continue

        try:
            feed = load_feed(rss_source_link)
            if not rss_source_name:
                rss_source_name = get_feed_title_from_feed(feed)

        except error:
            logger.error(f"Error while checking the link: '{rss_source_link}': {error}")
            continue

        logger.info('Checking "%s"', rss_source_name)

        to_name_function = configuration_to_function_rss_to_name(
            rss_file_name_template_value, rss_source
        )

        on_directory_empty = configuration_to_function_on_empty_directory(
            rss_if_directory_empty
        )

        downloaded_files = list(
            get_downloaded_files(
                get_extensions_checker(rss_podcast_extensions), rss_source_path
            )
        )

        allow_link_types = list(set(rss_podcast_extensions.values()))

        all_feed_entries = compose(
            list,
            partial(filter, build_only_allowed_filter_for_link_data(allow_link_types)),
            flatten_rss_links_data,
            get_raw_rss_entries_from_feed,
        )(feed)

        to_real_podcast_file_name = compose(
            partial(limit_file_name, file_length_limit), to_name_function
        )

        all_feed_files = list(map(to_real_podcast_file_name, all_feed_entries))[::-1]
        downloaded_files = [feed for feed in all_feed_files if feed in downloaded_files]

        last_downloaded_file = None
        if downloaded_files:
            if rss_fill_up_gaps:
                last_downloaded_file = get_last_downloaded_file_before_gap(
                    all_feed_files, downloaded_files
                )
            else:
                last_downloaded_file = downloaded_files[-1]

            download_limiter_function = partial(
                build_only_new_entities(to_name_function), last_downloaded_file
            )
        else:
            download_limiter_function = on_directory_empty

        missing_files_links = compose(list, download_limiter_function)(all_feed_entries)

        logger.info('Last downloaded file "%s"', last_downloaded_file or "<none>")

        if missing_files_links:
            download_podcast = partial(
                download_rss_entity_to_path,
                rss_https_header,
                to_real_podcast_file_name,
            )

            for rss_entry in reversed(missing_files_links):
                wanted_podcast_file_name = to_name_function(rss_entry)
                if wanted_podcast_file_name in downloaded_files:
                    continue

                if DOWNLOADS_LIMITS == 0:
                    continue

                if len(wanted_podcast_file_name) > file_length_limit:
                    logger.info(
                        'Your system cannot support the full podcast file name "%s". The name will be shortened',
                        wanted_podcast_file_name,
                    )

                logger.info(
                    '%s: Downloading file: "%s" saved as "%s"',
                    rss_source_name,
                    rss_entry.link,
                    to_real_podcast_file_name(rss_entry),
                )

                download_podcast(rss_source_path, rss_entry)
                DOWNLOADS_LIMITS -= 1
        else:
            logger.info("%s: Nothing new", rss_source_name)

    logger.info("Finished")
