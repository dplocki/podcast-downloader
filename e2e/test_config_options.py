import random
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
from e2e.random import (
    generate_random_file,
    generate_random_int,
    generate_random_mp3_file,
    generate_random_string,
)


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


def test_configuration_podcast_extensions_option(
    feed: FeedBuilder,
    use_config: Callable[[Dict], None],
    podcast_directory: PodcastDirectory,
):
    # Arrange
    avi_files = [generate_random_file(".avi") for _ in range(generate_random_int())]
    mp3_files = [generate_random_mp3_file() for _ in range(generate_random_int())]
    all_files = [(file_name, "movie/mpeg") for file_name in avi_files] + [
        (file_name, None) for file_name in mp3_files
    ]
    random.shuffle(all_files)

    for file_name, file_type in all_files:
        feed.add_entry(file_name=file_name, file_type=file_type)

    use_config(
        {
            "if_directory_empty": "download_all_from_feed",
            "podcasts": [
                {
                    "podcast_extensions": {".avi": "movie/mpeg"},
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
    podcast_directory.is_containing_only([file_name.lower() for file_name in avi_files])


def test_configuration_file_name_template_option(
    feed: FeedBuilder,
    use_config: Callable[[Dict], None],
    podcast_directory: PodcastDirectory,
):
    mp3_files_date = [generate_random_mp3_file() for _ in range(generate_random_int())]

    for file_name in mp3_files_date:
        feed.add_entry(file_name=file_name)

    use_config(
        {
            "if_directory_empty": "download_all_from_feed",
            "podcasts": [
                {
                    "file_name_template": "%file_name%_terminus_est_%file_extension%",
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
    podcast_directory.is_containing_only([file_name.lower().replace('.', '_terminus_est_') for file_name in mp3_files_date])
