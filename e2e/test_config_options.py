from functools import partial
from itertools import chain
from typing import Callable, Dict
from e2e.fixures import (
    FeedBuilder,
    MultipleFeedBuilder,
    MultiplePodcastDirectory,
    PodcastDirectory,
    run_podcast_downloader,
    # fixures:
    download_destination_directory,
    feed,
    feed_builder_manager,
    use_config,
    podcast_directory,
    podcast_directory_manager,
)
from e2e.random import (
    call_n_times,
    generate_random_file,
    generate_random_int,
    generate_random_mp3_file,
    generate_random_string,
    randomize_iterables,
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
    avi_files = call_n_times(partial(generate_random_file, ".avi"))
    mp3_files = call_n_times(generate_random_mp3_file)
    all_files = randomize_iterables(
        ((file_name, "movie/mpeg") for file_name in avi_files),
        ((file_name, None) for file_name in mp3_files),
    )

    for file_name, file_type in all_files:
        feed.add_entry(file_name=file_name, file_type=file_type)

    use_config(
        {
            "if_directory_empty": "download_all_from_feed",
            "podcasts": [
                {
                    "podcast_extensions": {".avi": "movie/mpeg"},
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
    # Arrange
    mp3_files_date = call_n_times(generate_random_mp3_file)

    for file_name in mp3_files_date:
        feed.add_entry(file_name=file_name)

    use_config(
        {
            "if_directory_empty": "download_all_from_feed",
            "podcasts": [
                {
                    "file_name_template": "%file_name%_terminus_est_%file_extension%",
                    "path": podcast_directory.path(),
                    "rss_link": feed.get_feed_url(),
                }
            ],
        }
    )

    # Act
    run_podcast_downloader()

    # Assert
    podcast_directory.is_containing_only(
        [
            file_name.lower().replace(".", "_terminus_est_")
            for file_name in mp3_files_date
        ]
    )


def test_configuration_downloads_limit_option(
    feed_builder_manager: MultipleFeedBuilder,
    use_config: Callable[[Dict], None],
    podcast_directory_manager: MultiplePodcastDirectory,
):
    # Arrange
    first_entries = generate_random_int()
    limit = first_entries + generate_random_int(2, 3)

    for _ in range(first_entries):
        feed_builder_manager.first_feed.add_entry(file_name=generate_random_mp3_file())

    for _ in range(generate_random_int()):
        feed_builder_manager.second_feed.add_entry(file_name=generate_random_mp3_file())

    use_config(
        {
            "if_directory_empty": "download_all_from_feed",
            "downloads_limit": limit,
            "podcasts": [
                {
                    "path": podcast_directory_manager.get_first_directory(),
                    "rss_link": feed_builder_manager.first_feed.get_feed_url(),
                },
                {
                    "path": podcast_directory_manager.get_second_directory(),
                    "rss_link": feed_builder_manager.second_feed.get_feed_url(),
                },
            ],
        }
    )

    # Act
    run_podcast_downloader()

    # Assert
    downloaded_files_count = sum(
        1 for _ in podcast_directory_manager.get_first_directory_files()
    ) + sum(1 for _ in podcast_directory_manager.get_second_directory_files())

    assert (
        downloaded_files_count == limit
    ), f"Excepted the download files number ({downloaded_files_count}) to equal to limit ({limit})"


def test_configuration_http_headers_option(
    feed: FeedBuilder,
    use_config: Callable[[Dict], None],
    podcast_directory_manager: MultiplePodcastDirectory,
):
    # Arrange
    request_user_agent = generate_random_string()
    feed.set_request_headers({"User-Agent": request_user_agent})
    feed.add_random_entries()
    rss_link = feed.get_feed_url()

    use_config(
        {
            "podcasts": [
                {
                    "http_headers": {"User-Agent": request_user_agent},
                    "path": podcast_directory_manager.get_first_directory(),
                    "rss_link": rss_link,
                },
                {
                    "path": podcast_directory_manager.get_second_directory(),
                    "rss_link": rss_link,
                },
            ],
        }
    )

    # Act
    run_podcast_downloader()

    # Assert
    assert (
        len(list(podcast_directory_manager.get_first_directory_files())) > 0
    ), "User-Agent should allow the download"
    assert (
        len(list(podcast_directory_manager.get_second_directory_files())) == 0
    ), "User-Agent should not allow the download"


def test_configuration_fill_up_gaps_option(
    feed: FeedBuilder,
    use_config: Callable[[Dict], None],
    podcast_directory: PodcastDirectory,
):
    # Arrange
    files_earliest_downloaded = call_n_times(generate_random_mp3_file)
    downloaded_files_before_gap = call_n_times(generate_random_mp3_file)
    the_gap_begin_file = generate_random_mp3_file()
    files_in_the_gap = call_n_times(generate_random_mp3_file)
    the_gap_end_file = generate_random_mp3_file()
    downloaded_files_after_gap = call_n_times(generate_random_mp3_file)
    files_to_download = call_n_times(generate_random_mp3_file)

    for file_name in chain(
        files_earliest_downloaded,
        downloaded_files_before_gap,
        [the_gap_begin_file],
        files_in_the_gap,
        [the_gap_end_file],
        downloaded_files_after_gap,
        files_to_download,
    ):
        feed.add_entry(file_name)

    for file_name in chain(
        downloaded_files_before_gap,
        [the_gap_begin_file, the_gap_end_file],
        downloaded_files_after_gap,
    ):
        podcast_directory.add_file(file_name)

    use_config(
        {
            "podcasts": [
                {
                    "path": podcast_directory.path(),
                    "rss_link": feed.get_feed_url(),
                    "fill_up_gaps": True,
                }
            ],
        }
    )

    # Act
    run_podcast_downloader()

    # Assert
    podcast_directory.is_containing_only(
        [
            file_name.lower()
            for file_name in chain(
                downloaded_files_before_gap,
                [the_gap_begin_file],
                files_in_the_gap,
                [the_gap_end_file],
                downloaded_files_after_gap,
                files_to_download,
            )
        ]
    )
