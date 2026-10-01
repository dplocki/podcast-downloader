from typing import Callable, Dict

from pytest_httpserver import HTTPServer

from e2e.fixures import (
    FeedBuilder,
    PodcastDirectory,
    PodcastDownloaderRunner,
    download_destination_directory,
    feed,
    podcast_directory,
    podcast_downloader,
    use_config,
)
from e2e.random import generate_random_string


def test_explicit_empty_podcast_headers_do_not_inherit_global_headers(
    feed: FeedBuilder,
    use_config: Callable[[Dict], None],
    podcast_downloader: PodcastDownloaderRunner,
    podcast_directory: PodcastDirectory,
    httpserver: HTTPServer,
):
    global_header_name = "X-Podcast-Downloader-Test"
    global_header_value = generate_random_string()

    feed.add_random_entries()
    rss_link = feed.get_feed_url()

    use_config(
        {
            "http_headers": {global_header_name: global_header_value},
            "podcasts": [
                {
                    "http_headers": {},
                    "path": podcast_directory.path(),
                    "rss_link": rss_link,
                }
            ],
        }
    )

    podcast_downloader.run()

    feed_requests = [
        log[0]
        for log in httpserver.log
        if log[0].path == FeedBuilder.FEED_RSS_FILE_NAME
    ]

    assert feed_requests
    assert all(request.headers.get(global_header_name) is None for request in feed_requests)
