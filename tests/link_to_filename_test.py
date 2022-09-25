import unittest

from podcast_downloader.rss import RSSEntitySimpleName, RSSEntityWithDate
from tests.commons import build_timestamp


class TestLink2FileName(unittest.TestCase):
    def test_entry_to_simple_file_name(self):
        # Assign
        expected = "file_name.mp3"
        rss_entry = RSSEntitySimpleName(
            build_timestamp(2020, 1, 2),
            "audio/mp3",
            "http://www.podcast.com/podcast/something/fIlE_nAme.mp3",
        )

        # Act
        result = rss_entry.to_file_name()

        # Assert
        self.assertEqual(
            result, expected, f'File should be named "{expected}" not "{result}"'
        )

    def test_entry_to_file_name_with_date(self):
        # Assign
        expected = "[20200102] file_name.mp3"
        rss_entry = RSSEntityWithDate(
            build_timestamp(2020, 1, 2),
            "audio/mp3",
            "http://www.podcast.com/podcast/something/fIlE_nAme.mp3",
        )

        # Act
        result = rss_entry.to_file_name()

        # Assert
        self.assertEqual(
            result, expected, f'File should be named "{expected}" not "{result}"'
        )
