from functools import partial
import os
from podcast_downloader.downloaded import get_downloaded_files, get_extensions_checker
from podcast_downloader.parameters import load_configuration_file
from podcast_downloader.rss import build_only_allowed_filter_for_link_data, flatten_rss_links_data, get_raw_rss_entries_from_feed, load_feed
from podcast_downloader.utils import compose


config = load_configuration_file("a.json")
podcast_config = config["podcasts"][0]
rss_source_link = podcast_config["rss_link"]
feed = load_feed(rss_source_link)


rss_podcast_extensions = podcast_config.get("podcast_extensions", {".mp3": "audio/mpeg"})
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

print(all_feed_entries, downloaded_files)
