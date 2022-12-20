import datetime
from typing import Tuple
import unittest
from podcast_downloader.rss import RSSEntity, file_template_to_file_name, link_to_file_name

from tests.commons import build_timestamp


def build_test_link_data(link: str, ) -> Tuple[datetime.date, str, str]:
    return RSSEntity(
            build_timestamp(2020, 1, 2),
            "The fancy title",
            "audio/mp3",
            link)


class TestFileTemplateToFileNameConverter(unittest.TestCase):

    def test_link_to_file_name(self):
        test_parameters = [
            ('http://www.podcast.com/direct_file.txt', 'direct_file'),
            ('http://www.podcast.com/podcast/something/fIlE_nAme.mp3', 'file_name'),
            ('http://www.podcast.com/podcast/something/Different_fIlE_nAme.mp3?asasasmkas&sdds', 'different_file_name'),
            ('http://www.podcast.com/podcast/something/multiple.dots.mp3', 'multiple.dots'),
            ('http://www.podcast.com/podcast/something/multiple.dots.mp3?with&parameter', 'multiple.dots'),
            ('http://www.podcast.com/podcast/something/normal_name.mp3?/with/tricky/parameter', 'normal_name'),
        ]

        for url, expected_file_name in test_parameters:
            result = link_to_file_name(url)

            # Assert
            self.assertEqual(
                result, expected_file_name, f'File should be named "{expected_file_name}" not "{result}"'
            )            
