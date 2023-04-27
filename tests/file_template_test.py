import datetime
from typing import Tuple
import unittest
from podcast_downloader.rss import (
    RSSEntity,
    file_template_to_file_name,
    limit_file_name,
    link_to_extension,
    link_to_file_name,
    str_to_filename,
)

from tests.commons import build_timestamp


def build_test_link_data(
    link: str = None, title: str = None
) -> Tuple[datetime.date, str, str]:
    link = link or "http://www.podcast.com/podcast/something/abc.mp3"
    title = title or "The fancy title"

    return RSSEntity(build_timestamp(2020, 1, 2), title, "audio/mp3", link)


class TestFileTemplateToFileNameConverter(unittest.TestCase):
    def test_link_to_file_name(self):
        # Assign
        test_parameters = [
            ("http://www.podcast.com/direct_file.txt", "direct_file"),
            ("http://www.podcast.com/podcast/something/fIlE_nAme.mp3", "file_name"),
            (
                "http://www.podcast.com/podcast/something/Different_fIlE_nAme.mp3?asasasmkas&sdds",
                "different_file_name",
            ),
            (
                "http://www.podcast.com/podcast/something/multiple.dots.mp3",
                "multiple.dots",
            ),
            (
                "http://www.podcast.com/podcast/something/multiple.dots.mp3?with&parameter",
                "multiple.dots",
            ),
            (
                "http://www.podcast.com/podcast/something/normal_name.mp3?/with/tricky/parameter",
                "normal_name",
            ),
        ]

        for url, expected_file_name in test_parameters:
            # Act
            result = link_to_file_name(url)

            # Assert
            self.assertEqual(
                result,
                expected_file_name,
                f'File should be named "{expected_file_name}" not "{result}"',
            )

    def test_link_to_extension(self):
        # Assign
        test_parameters = [
            ("http://www.podcast.com/direct_file.txt", "txt"),
            ("http://www.podcast.com/podcast/something/fIlE_nAme.mP3", "mp3"),
            (
                "http://www.podcast.com/podcast/something/Different_fIlE_nAme.mp3?asasasmkas&sdds",
                "mp3",
            ),
            ("http://www.podcast.com/podcast/something/multiple.dots.mp3", "mp3"),
            (
                "http://www.podcast.com/podcast/something/multiple.dots.avi?with&parameter",
                "avi",
            ),
            (
                "http://www.podcast.com/podcast/something/normal_name.mp3?/with/tricky/para.meter",
                "mp3",
            ),
        ]

        for url, expected_file_name in test_parameters:
            # Act
            result = link_to_extension(url)

            # Assert
            self.assertEqual(
                result,
                expected_file_name,
                f'File extension should be named "{expected_file_name}" not "{result}"',
            )

    def test_str_to_filename(self):
        test_parameters = [
            ("Ala ma kota", "Ala ma kota"),
            (" abcdefg hijk ", "abcdefg hijk"),
            (
                'AEE 226: How to "80/20" Your English to Make More Friends with italki Teacher Nick Vance',
                'AEE 226  How to "80 20" Your English to Make More Friends with italki Teacher Nick Vance',
            ),
            (
                "【Audio Book/朗読】『浦島太郎（うらしまたろう） 』Urashima Taro /Japanese folktales",
                "【Audio Book 朗読】『浦島太郎(うらしまたろう) 』Urashima Taro  Japanese folktales",
            ),
        ]

        for entry_title, expected_file_name in test_parameters:
            # Act
            result = str_to_filename(entry_title)

            # Assert
            self.assertEqual(
                result,
                expected_file_name,
                f'File should be named "{expected_file_name}" not "{result}"',
            )

    def test_file_template_to_file_name(self):
        test_parameters = [
            (
                build_test_link_data(
                    link="http://www.podcast.com/podcast/something/fIlE_nAme.mp3"
                ),
                "%file_name%.%file_extension%",
                "file_name.mp3",
            ),
            (
                build_test_link_data(
                    link="http://www.podcast.com/podcast/something/fIlE_nAme.mp3"
                ),
                "[%publish_date%] %file_name%.%file_extension%",
                "[20200102] file_name.mp3",
            ),
            (
                build_test_link_data(
                    link="http://www.podcast.com/podcast/something/fIlE_nAme.mp3"
                ),
                "%title%.%file_extension%",
                "The fancy title.mp3",
            ),
            (
                build_test_link_data(
                    link="http://www.podcast.com/podcast/something/fIlE_nAme.mp3",
                    title="The fancy title",
                ),
                "[%publish_date%] %title%.%file_extension%",
                "[20200102] The fancy title.mp3",
            ),
            (
                build_test_link_data(
                    link="http://www.podcast.com/podcast/something/fIlE_nAme.mp3",
                    title="   abc/def   ",
                ),
                "[%publish_date%] %title%.%file_extension%",
                "[20200102] abc def.mp3",
            ),
        ]

        for rss_entry, template_file_name, expected_file_name in test_parameters:
            # Act
            result = file_template_to_file_name(template_file_name, rss_entry)

            # Assert
            self.assertEqual(
                result,
                expected_file_name,
                f'File should be named "{expected_file_name}" not "{result}"',
            )

    def test_limit_file_name(self):
        test_parameters = [
            (30, "123456789012345.mp3", "123456789012345.mp3"),
            (10, "123456789012345.mp3", "123456.mp3"),
            (10, "123456789012345.ab", "1234567.ab"),
            (30, "123456789012", "123456789012"),
            (10, "1234567890", "1234567890"),
            (10, "123456789012345", "1234567890"),
            (5, "1234.mp3", "1.mp3"),
        ]

        for maximum_length, given_file_name, expected_file_name in test_parameters:
            # Act
            result = limit_file_name(maximum_length, given_file_name)

            # Assert
            self.assertEqual(
                result,
                expected_file_name,
                f'File should be named "{expected_file_name}" not "{result}"',
            )
