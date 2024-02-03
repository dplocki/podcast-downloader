from typing import Callable, Dict
from e2e.fixures import (
    FeedBuilder,
    PodcastDirectory,
    run_podcast_downloader,
    # fixures:
    download_destination_directory,
    feed,
    use_config,
    podcast_directory,
)
from e2e.random import generate_random_string


def test_configuration_hierarchy(
    feed: FeedBuilder,
    use_config: Callable[[Dict], None],
    podcast_directory: PodcastDirectory,
):
    # Arrange
    feed.add_random_entries()

    use_config(
        {
            "if_directory_empty": "download_all_from_feed",
            "podcasts": [
                {
                    "name": generate_random_string(),
                    "path": podcast_directory.path(),
                    "rss_link": feed.get_feed_url(),
                    "if_directory_empty": "download_last",
                }
            ],
        }
    )

    # Act
    run_podcast_downloader()

    # Assert
    assert len(podcast_directory.get_files_list()) == 1
