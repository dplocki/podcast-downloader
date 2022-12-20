from datetime import datetime
from typing import Tuple
import unittest

from podcast_downloader.rss import RSSEntity, to_name_with_date_name, to_plain_file_name
from tests.commons import build_timestamp


def build_test_link_data(link: str) -> Tuple[datetime.date, str, str]:
    return RSSEntity(build_timestamp(2020, 1, 2), "audio/mp3", "The fancy title", link)


class TestLink2FileName(unittest.TestCase):
    def test_entry_to_simple_file_name(self):
        # Assign
        expected = "file_name.mp3"
        rss_entry = build_test_link_data(
            link="http://www.podcast.com/podcast/something/fIlE_nAme.mp3"
        )

        # Act
        result = to_plain_file_name(rss_entry)

        # Assert
        self.assertEqual(
            result, expected, f'File should be named "{expected}" not "{result}"'
        )

    def test_entry_to_file_name_with_date(self):
        # Assign
        expected = "[20200102] file_name.mp3"
        rss_entry = build_test_link_data(
            link="http://www.podcast.com/podcast/something/fIlE_nAme.mp3"
        )

        # Act
        result = to_name_with_date_name(rss_entry)

        # Assert
        self.assertEqual(
            result, expected, f'File should be named "{expected}" not "{result}"'
        )
