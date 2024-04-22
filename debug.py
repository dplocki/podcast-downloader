import os
from podcast_downloader.downloaded import get_downloaded_files, get_extensions_checker
from podcast_downloader.parameters import load_configuration_file
from podcast_downloader.rss import load_feed


config = load_configuration_file("a.json")
podcast_config = config["podcasts"][0]
rss_source_link = podcast_config["rss_link"]
feed = load_feed(rss_source_link)


rss_podcast_extensions = podcast_config.get("podcast_extensions", ".mp3")
rss_source_path = os.path.expanduser(podcast_config["path"])

downloaded_files = list(
    get_downloaded_files(
        get_extensions_checker(rss_podcast_extensions), rss_source_path
    )
)

print(feed, downloaded_files)
