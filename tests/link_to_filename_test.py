import unittest

from podcast_downloader.rss import\
    RSSEntitySimpleName,\
    RSSEntityWithDate


class TestLink2FileName(unittest.TestCase):

    def test_entry_to_simple_file_name(self):
        expected = 'file_name.mp3'
        rss_entry = RSSEntitySimpleName(
            (2020, 1, 2, 17, 3, 38, 1, 48, 0),
            'http://www.podcast.com/podcast/something/fIlE_nAme.mp3')

        result = rss_entry.to_file_name()

        self.assertEqual(result, expected, f'File should be named "{expected}" not "{result}"')

    def test_entry_to_file_name_with_date(self):
        expected = '[20200102] file_name.mp3'
        rss_entry = RSSEntityWithDate(
            (2020, 1, 2, 17, 3, 38, 1, 48, 0),
            'http://www.podcast.com/podcast/something/fIlE_nAme.mp3')

        result = rss_entry.to_file_name()

        self.assertEqual(result, expected, f'File should be named "{expected}" not "{result}"')
