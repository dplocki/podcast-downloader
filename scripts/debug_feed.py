from functools import partial
import os
from podcast_downloader.__main__ import get_system_file_name_limit
from podcast_downloader.downloaded import get_downloaded_files, get_extensions_checker
from podcast_downloader.parameters import load_configuration_file
from podcast_downloader.rss import (
    build_only_allowed_filter_for_link_data,
    build_only_new_entities,
    file_template_to_file_name,
    flatten_rss_links_data,
    get_raw_rss_entries_from_feed,
    limit_file_name,
    load_feed,
)
from podcast_downloader.utils import compose


config = load_configuration_file("a.json")
podcast_config = config["podcasts"][0]
rss_source_link = podcast_config["rss_link"]
feed = load_feed(rss_source_link)

rss_podcast_extensions = podcast_config.get(
    "podcast_extensions", {".mp3": "audio/mpeg"}
)
rss_podcast_file_name_template = podcast_config.get(
    "file_name_template", "%file_name%.%file_extension%"
)
rss_source_path = os.path.expanduser(podcast_config["path"])


allow_link_types = list(set(rss_podcast_extensions.values()))

all_feed_entries = compose(
    list,
    partial(filter, build_only_allowed_filter_for_link_data(allow_link_types)),
    flatten_rss_links_data,
    get_raw_rss_entries_from_feed,
)(feed)

downloaded_files = list(
    get_downloaded_files(
        get_extensions_checker(rss_podcast_extensions), rss_source_path
    )
)

to_name_function = partial(file_template_to_file_name, rss_podcast_file_name_template)
file_length_limit = get_system_file_name_limit(podcast_config)
to_real_podcast_file_name = compose(
    partial(limit_file_name, file_length_limit), to_name_function
)

all_feed_files = list(map(to_real_podcast_file_name, all_feed_entries))[::-1]
only_files_from_feed_sorted = [
    feed for feed in all_feed_files if feed in downloaded_files
]
last_downloaded_file = only_files_from_feed_sorted[-1]

download_limiter_function = partial(
    build_only_new_entities(to_name_function), last_downloaded_file
)

missing_files_links = compose(list, download_limiter_function)(all_feed_entries)

for feed in all_feed_entries:
    feed_file = to_real_podcast_file_name(feed)

    status = (
        "to-download"
        if feed_file in missing_files_links
        else ("downloaded" if feed_file in only_files_from_feed_sorted else "ignored")
    )

    print(feed.title + "\t" + feed_file + "\t" + status)
