from typing import Callable, Dict

from e2e.fixures import (
    MultipleFeedBuilder,
    MultiplePodcastDirectory,
    PodcastDownloaderRunner,
    feed_builder_manager,
    podcast_directory_manager,
    podcast_downloader,
    use_config,
)
from e2e.random import generate_random_mp3_file


def test_missing_last_run_marker_only_skips_affected_podcast(
    feed_builder_manager: MultipleFeedBuilder,
    use_config: Callable[[Dict], None],
    podcast_downloader: PodcastDownloaderRunner,
    podcast_directory_manager: MultiplePodcastDirectory,
):
    second_podcast_file = generate_random_mp3_file()

    feed_builder_manager.first_feed.add_random_entries()
    feed_builder_manager.second_feed.add_entry(file_name=second_podcast_file)

    use_config(
        {
            "podcasts": [
                {
                    "name": "invalid",
                    "if_directory_empty": "download_since_last_run",
                    "path": podcast_directory_manager.get_first_directory(),
                    "rss_link": feed_builder_manager.first_feed.get_feed_url(),
                },
                {
                    "name": "valid",
                    "if_directory_empty": "download_last",
                    "path": podcast_directory_manager.get_second_directory(),
                    "rss_link": feed_builder_manager.second_feed.get_feed_url(),
                },
            ]
        }
    )

    runner = podcast_downloader.run()

    assert runner.is_containing("Invalid if_directory_empty value")
    assert runner.is_highlighted_in_outcome("download_since_last_run")
    assert list(podcast_directory_manager.get_first_directory_files()) == []
    assert {
        file.name for file in podcast_directory_manager.get_second_directory_files()
    } == {second_podcast_file.lower()}
