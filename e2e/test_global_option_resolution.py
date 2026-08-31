from itertools import chain
from typing import Callable, Dict, List

from e2e.fixures import (
    DEFAULT_CONFIG_NAME,
    FeedBuilder,
    PodcastDirectory,
    PodcastDownloaderRunner,
    feed,
    use_config,
    podcast_directory,
    podcast_downloader,
)
from e2e.random import call_n_times, generate_random_mp3_file


def test_configuration_global_fill_up_gaps_option(
    feed: FeedBuilder,
    use_config: Callable[[Dict], None],
    podcast_downloader: Callable[[List[str]], PodcastDownloaderRunner],
    podcast_directory: PodcastDirectory,
):
    files_downloaded_and_removed = call_n_times(generate_random_mp3_file)
    downloaded_files_before_gap = call_n_times(generate_random_mp3_file)
    files_in_the_gap = call_n_times(generate_random_mp3_file)
    downloaded_files_after_gap = call_n_times(generate_random_mp3_file)
    files_to_download = call_n_times(generate_random_mp3_file)

    for file_name in chain(
        files_downloaded_and_removed,
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
            "fill_up_gaps": True,
            "podcasts": [
                {
                    "path": podcast_directory.path(),
                    "rss_link": feed.get_feed_url(),
                }
            ],
        }
    )

    podcast_downloader.run()

    podcast_directory.is_containing_only(
        [
            file_name.lower()
            for file_name in chain(
                downloaded_files_before_gap,
                files_in_the_gap,
                downloaded_files_after_gap,
                files_to_download,
            )
        ]
    )


def test_configuration_global_download_delay_option(
    feed: FeedBuilder,
    use_config: Callable[[Dict], None],
    podcast_downloader: Callable[[List[str]], PodcastDownloaderRunner],
    podcast_directory: PodcastDirectory,
):
    files_to_download = [generate_random_mp3_file(), generate_random_mp3_file()]
    for file_name in files_to_download:
        feed.add_entry(file_name=file_name)

    use_config(
        {
            "if_directory_empty": "download_all_from_feed",
            "download_delay": 1,
            "podcasts": [
                {
                    "path": podcast_directory.path(),
                    "rss_link": feed.get_feed_url(),
                }
            ],
        }
    )

    podcast_downloader.run()

    podcast_directory.is_containing_only([name.lower() for name in files_to_download])
    assert podcast_downloader.is_containing("The download is sleeping (1 second)")


def test_cli_zero_downloads_limit_overrides_configuration(
    feed: FeedBuilder,
    use_config: Callable[[Dict], None],
    podcast_downloader: PodcastDownloaderRunner,
    podcast_directory: PodcastDirectory,
):
    feed.add_entry(file_name=generate_random_mp3_file())

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

    config_path = podcast_downloader.script_directory / DEFAULT_CONFIG_NAME
    podcast_downloader.run(
        ["--config", str(config_path), "--downloads_limit", "0"]
    )

    podcast_directory.is_containing_only([])
