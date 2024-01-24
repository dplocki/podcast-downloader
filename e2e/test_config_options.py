from typing import Callable, Dict
from e2e.fixures import (
    FeedBuilder,
    PodcastDirectory,
    run_podcast_downloader,
    # fixures:
    feed,
    use_config,
    podcast_directory,
    download_destination_directory,
)
from e2e.random import generate_random_string


def test_configuration_ignore_option(
    feed: FeedBuilder,
    use_config: Callable[[Dict], None],
    podcast_directory: PodcastDirectory,
):
    # Arrange
    feed.add_random_entries()

    use_config(
        {
            "podcasts": [
                {
                    "disable": True,
                    "name": generate_random_string(),
                    "path": podcast_directory.path(),
                    "rss_link": feed.get_feed_url(),
                }
            ]
        }
    )

    # Act
    run_podcast_downloader()

    # Assert
    podcast_directory.is_containing_only([])
