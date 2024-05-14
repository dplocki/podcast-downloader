import datetime
from itertools import chain
from e2e.fixures import (
    FeedBuilder,
    PodcastDirectory,
    PodcastDownloaderRunner,
    # fixures:
    download_destination_directory,
    feed,
    use_config,
    podcast_directory,
    podcast_downloader,
)
from e2e.random import (
    call_n_times,
    generate_random_int,
    generate_random_mp3_file,
    generate_random_string,
)
from typing import Callable, Dict, List


def test_default_behavior_on_empty_podcast_directory(
    feed: FeedBuilder,
    use_config: Callable[[Dict], None],
    podcast_downloader: Callable[[List[str]], PodcastDownloaderRunner],
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
                    "path": podcast_directory.path(),
                    "rss_link": feed.get_feed_url(),
                }
            ]
        }
    )

    # Act
    podcast_downloader.run()

    # Assert
    podcast_directory.is_containing_only([last_file_name.lower()])


def test_default_behavior_on_nonempty_podcast_directory(
    feed: FeedBuilder,
    use_config: Callable[[Dict], None],
    podcast_downloader: Callable[[List[str]], PodcastDownloaderRunner],
    podcast_directory: PodcastDirectory,
):
    # Arrange
    podcasts_files = call_n_times(generate_random_mp3_file)
    expected_downloaded_files = list(map(str.lower, podcasts_files))

    feed.add_random_entries()
    for file_name in podcasts_files:
        feed.add_entry(file_name=file_name)

    podcast_directory.add_file(podcasts_files[0])

    use_config(
        {
            "podcasts": [
                {
                    "path": podcast_directory.path(),
                    "rss_link": feed.get_feed_url(),
                }
            ]
        }
    )

    # Act
    podcast_downloader.run()

    # Assert
    podcast_directory.is_containing_only(expected_downloaded_files)


def test_default_behavior_fill_up_gaps(
    feed: FeedBuilder,
    use_config: Callable[[Dict], None],
    podcast_downloader: Callable[[List[str]], PodcastDownloaderRunner],
    podcast_directory: PodcastDirectory,
):
    # Arrange
    files_earliest_downloaded = call_n_times(generate_random_mp3_file)
    downloaded_files_before_gap = call_n_times(generate_random_mp3_file)
    files_in_the_gap = call_n_times(generate_random_mp3_file)
    downloaded_files_after_gap = call_n_times(generate_random_mp3_file)
    files_to_download = call_n_times(generate_random_mp3_file)

    for file_name in chain(
        files_earliest_downloaded,
        downloaded_files_before_gap,
        files_in_the_gap,
        downloaded_files_after_gap,
        files_to_download,
    ):
        feed.add_entry(file_name)

    for file_name in chain(
        downloaded_files_before_gap,
        downloaded_files_after_gap,
    ):
        podcast_directory.add_file(file_name)

    use_config(
        {
            "podcasts": [
                {
                    "path": podcast_directory.path(),
                    "rss_link": feed.get_feed_url(),
                }
            ],
        }
    )

    # Act
    podcast_downloader.run()

    # Assert
    podcast_directory.is_containing_only(
        [
            file_name.lower()
            for file_name in chain(
                downloaded_files_before_gap,
                downloaded_files_after_gap,
                files_to_download,
            )
        ]
    )


def test_download_all_from_feed_behavior(
    feed: FeedBuilder,
    use_config: Callable[[Dict], None],
    podcast_downloader: Callable[[List[str]], PodcastDownloaderRunner],
    podcast_directory: PodcastDirectory,
):
    # Arrange
    podcasts_files = call_n_times(generate_random_mp3_file)
    expected_downloaded_files = list(map(str.lower, podcasts_files))

    for file_name in podcasts_files:
        feed.add_entry(file_name=file_name)

    use_config(
        {
            "if_directory_empty": "download_all_from_feed",
            "podcasts": [
                {
                    "path": podcast_directory.path(),
                    "rss_link": feed.get_feed_url(),
                }
            ],
        }
    )

    # Act
    podcast_downloader.run()

    # Assert
    podcast_directory.is_containing_only(expected_downloaded_files)


def test_download_last_from_feed_behavior(
    feed: FeedBuilder,
    use_config: Callable[[Dict], None],
    podcast_downloader: Callable[[List[str]], PodcastDownloaderRunner],
    podcast_directory: PodcastDirectory,
):
    # Arrange
    podcasts_files = call_n_times(generate_random_mp3_file)
    expected_downloaded_files = list(map(str.lower, podcasts_files))
    last_podcast_file = expected_downloaded_files[-1]

    for file_name in podcasts_files:
        feed.add_entry(file_name=file_name)

    use_config(
        {
            "if_directory_empty": "download_last",
            "podcasts": [
                {
                    "path": podcast_directory.path(),
                    "rss_link": feed.get_feed_url(),
                }
            ],
        }
    )

    # Act
    podcast_downloader.run()

    # Assert
    podcast_directory.is_containing_only([last_podcast_file])


def test_download_from_n_days_from_feed_behavior(
    feed: FeedBuilder,
    use_config: Callable[[Dict], None],
    podcast_downloader: Callable[[List[str]], PodcastDownloaderRunner],
    podcast_directory: PodcastDirectory,
):
    # Arrange
    n_days_number = generate_random_int()

    metadata = []
    previous = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
    for _ in range(generate_random_int(7, 13)):
        metadata.append((generate_random_mp3_file(), previous))
        previous -= datetime.timedelta(days=1)

    metadata.reverse()

    for file_name, file_publish_data in metadata:
        feed.add_entry(file_name=file_name, published_date=file_publish_data)

    use_config(
        {
            "if_directory_empty": f"download_from_{n_days_number}_days",
            "podcasts": [
                {
                    "path": podcast_directory.path(),
                    "rss_link": feed.get_feed_url(),
                }
            ],
        }
    )

    # Act
    podcast_downloader.run()

    # Assert
    podcast_directory.is_containing_only(
        [m[0].lower() for m in metadata[-n_days_number:]]
    )


def test_download_last_n_episodes_behavior(
    feed: FeedBuilder,
    use_config: Callable[[Dict], None],
    podcast_downloader: Callable[[List[str]], PodcastDownloaderRunner],
    podcast_directory: PodcastDirectory,
):
    # Arrange
    n = generate_random_int(3, 6)
    podcasts_files = call_n_times(generate_random_mp3_file, generate_random_int(10, 15))
    expected_downloaded_files = list(map(str.lower, podcasts_files[-n:]))

    for file_name in podcasts_files:
        feed.add_entry(file_name=file_name)

    use_config(
        {
            "podcasts": [
                {
                    "if_directory_empty": f"download_last_{n}_episodes",
                    "path": podcast_directory.path(),
                    "rss_link": feed.get_feed_url(),
                }
            ],
        }
    )

    # Act
    podcast_downloader.run()

    # Assert
    podcast_directory.is_containing_only(expected_downloaded_files)


def test_download_since_last_run(
    feed: FeedBuilder,
    use_config: Callable[[Dict], None],
    podcast_downloader: Callable[[List[str]], PodcastDownloaderRunner],
    podcast_directory: PodcastDirectory,
):
    # Arrange
    expected_number_of_episode = generate_random_int(2, 5)
    metadata = []
    previous = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
    for _ in range(generate_random_int(7, 13)):
        metadata.append((generate_random_mp3_file(), previous))
        previous -= datetime.timedelta(days=1)

    metadata.reverse()

    expected_episode = [name for name, _ in metadata[:expected_number_of_episode]]

    last_run_date = metadata[expected_number_of_episode][1]
    last_run_date -= datetime.timedelta(hours=1)

    use_config(
        {
            "last_run_mark_file_path": "totem.json",
            "podcasts": [
                {
                    "if_directory_empty": "download_since_last_run",
                    "path": podcast_directory.path(),
                    "rss_link": feed.get_feed_url(),
                }
            ],
        }
    )

    # Act
    podcast_downloader.run()

    # Assert
    podcast_directory.is_containing_only(expected_episode)