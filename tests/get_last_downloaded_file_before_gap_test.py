import unittest

from podcast_downloader.downloaded import get_last_downloaded_file_before_gap


class TestGetLastDownloadedFileBeforeGap(unittest.TestCase):
    def test_should_return_none_for_empty_collections(self):
        # Act
        result = get_last_downloaded_file_before_gap([], [])

        # Assert
        self.assertIsNone(result)
