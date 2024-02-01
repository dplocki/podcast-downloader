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
from e2e.random import call_n_times, generate_random_mp3_file, generate_random_string
from typing import Callable, Dict


def test_default_behavior_on_empty_podcast_directory(
    feed: FeedBuilder,
    use_config: Callable[[Dict], None],
    podcast_directory: PodcastDirectory,
):
    # Arrange
    last_file_name = generate_random_mp3_file()

    feed.add_random_entries()
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
    podcast_directory.is_containing_only([last_file_name.lower()])


def test_default_behavior_on_nonempty_podcast_directory(
    feed: FeedBuilder,
    use_config: Callable[[Dict], None],
    podcast_directory: PodcastDirectory,
):
    # Arrange
    podcasts_files = call_n_times(generate_random_mp3_file)
    expected_downloaded_files = list(file_name.lower() for file_name in podcasts_files)

    feed.add_random_entries()
    for file_name in podcasts_files:
        feed.add_entry(file_name=file_name)

    podcast_directory.add_file(podcasts_files[0])

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
    podcast_directory.is_containing_only(expected_downloaded_files)


def test_download_all_from_feed_behavior(
    feed: FeedBuilder,
    use_config: Callable[[Dict], None],
    podcast_directory: PodcastDirectory,
):
    # Arrange
    podcasts_files = call_n_times(generate_random_mp3_file)
    expected_downloaded_files = list(file_name.lower() for file_name in podcasts_files)

    for file_name in podcasts_files:
        feed.add_entry(file_name=file_name)

    use_config(
        {
            "if_directory_empty": "download_all_from_feed",
            "podcasts": [
                {
                    "name": generate_random_string(),
                    "path": podcast_directory.path(),
                    "rss_link": feed.get_feed_url(),
                }
            ],
        }
    )

    # Act
    run_podcast_downloader()

    # Assert
    podcast_directory.is_containing_only(expected_downloaded_files)


def test_download_last_from_feed_behavior(
    feed: FeedBuilder,
    use_config: Callable[[Dict], None],
    podcast_directory: PodcastDirectory,
):
    # Arrange
    podcasts_files = call_n_times(generate_random_mp3_file)
    expected_downloaded_files = list(file_name.lower() for file_name in podcasts_files)
    last_podcast_file = expected_downloaded_files[-1]

    for file_name in podcasts_files:
        feed.add_entry(file_name=file_name)

    use_config(
        {
            "if_directory_empty": "download_last",
            "podcasts": [
                {
                    "name": generate_random_string(),
                    "path": podcast_directory.path(),
                    "rss_link": feed.get_feed_url(),
                }
            ],
        }
    )

    # Act
    run_podcast_downloader()

    # Assert
    podcast_directory.is_containing_only([last_podcast_file])
