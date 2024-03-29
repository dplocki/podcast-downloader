from random import shuffle
from typing import Generator
import unittest

from podcast_downloader.downloaded import get_last_downloaded_file_before_gap


class TestGetLastDownloadedFileBeforeGap(unittest.TestCase):
    def test_should_return_none_for_empty_collections(self):
        # Act
        result = get_last_downloaded_file_before_gap([], [])

        # Assert
        self.assertIsNone(result, "On empty directory should be return None")

    def test_should_return_none_for_empty_directory_files(self):
        # Assign
        feed_files = list(generate_podcast_files_episodes(4))

        # Act
        result = get_last_downloaded_file_before_gap(feed_files, [])

        # Assert
        self.assertIsNone(result, "On empty directory should be return None")

    def test_should_return_last_for_nonempty_directory_files(self):
        # Assign
        feed_files = list(generate_podcast_files_episodes(4))

        directory_files = feed_files.copy()

        # Act
        result = get_last_downloaded_file_before_gap(feed_files, directory_files)

        # Assert
        self.assertEqual(
            result, feed_files[-1], "Should return the last file from the feed"
        )

    def test_should_return_last_according_the_feed_order(self):
        # Assign
        feed_files = list(generate_podcast_files_episodes(4))

        directory_files = feed_files[0:-1]
        shuffle(directory_files)
        directory_files = directory_files[:1] + [feed_files[-1]] + directory_files[1:]

        # Act
        result = get_last_downloaded_file_before_gap(feed_files, directory_files)

        # Assert
        self.assertEqual(
            result, feed_files[-1], "Should return the last file from the feed"
        )

    def test_should_return_last_according_the_feed_order_when_feed_is_longer(self):
        # Assign
        feed_files = list(generate_podcast_files_episodes(8))

        directory_files = feed_files[2:-3]
        shuffle(directory_files)
        directory_files = directory_files[:1] + [feed_files[-3]] + directory_files[1:]

        # Act
        result = get_last_downloaded_file_before_gap(feed_files, directory_files)

        # Assert
        self.assertEqual(
            result,
            feed_files[-3],
            "Should return the last file (according to feed) which is downloaded",
        )

    def test_should_return_last_according_the_feed_order_with_gap_between_files(self):
        # Assign
        feed_files = list(generate_podcast_files_episodes(8))

        directory_files = feed_files[2:4] + [feed_files[-2]]
        shuffle(directory_files)
        directory_files.insert(0, feed_files[-4])

        # Act
        result = get_last_downloaded_file_before_gap(feed_files, directory_files)

        # Assert
        self.assertEqual(
            result,
            feed_files[-4],
            "Should return the last file (according to feed) before gap which is downloaded",
        )


def generate_podcast_files_episodes(n: int) -> Generator[str, None, None]:
    for i in range(1, n + 1):
        yield f"podcast_episode_{i}.mp3"
