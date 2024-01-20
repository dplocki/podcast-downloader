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
from typing import Callable, Dict


def test_default_behavior_on_empty_directory(
    feed: FeedBuilder,
    use_config: Callable[[Dict], None],
    podcast_directory: PodcastDirectory,
):
    # Arrange
    last_file_name = generate_random_string() + ".mp3"

    feed.add_entry()
    feed.add_entry()
    feed.add_entry(file_name=last_file_name)

    use_config(
        {
            "podcasts": [
                {
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
    podcast_directory.is_containing(last_file_name.lower())
    podcast_directory.is_containing_single_file()
