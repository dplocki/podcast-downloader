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


def test_default_behavior_on_empty_podcast_directory(
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
    podcast_directory.is_containing_only([last_file_name])


def test_default_behavior_on_nonempty_podcast_directory(
    feed: FeedBuilder,
    use_config: Callable[[Dict], None],
    podcast_directory: PodcastDirectory,
):
    # Arrange
    podcast_a_file = generate_random_string() + ".mp3"
    podcast_b_file = generate_random_string() + ".mp3"
    podcast_c_file = generate_random_string() + ".mp3"

    feed.add_entry()
    feed.add_entry()
    feed.add_entry()
    feed.add_entry(file_name=podcast_a_file)
    feed.add_entry(file_name=podcast_b_file)
    feed.add_entry(file_name=podcast_c_file)

    podcast_directory.add_file(podcast_a_file)

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
    podcast_directory.is_containing_only(
        [podcast_a_file, podcast_b_file, podcast_c_file]
    )
