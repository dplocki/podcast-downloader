import unittest

from main import file_name_to_entry_link_name, RSSEntity


class TestLink2FileName(unittest.TestCase):

    def test_removing_date_from_downloaded_file(self):
        expected = 'file_name.mp3'
        result = file_name_to_entry_link_name(f'[20190701] {expected}')

        self.assertEqual(result, expected, f'File should be "{expected}" not "{result}"')


    def test_entry_to_file_name(self):
        expected = '[20200102] file_name.mp3'
        rss_entry = RSSEntity(
            (2020, 1, 2, 17, 3, 38, 1, 48, 0),
            'http://www.podcast.com/podcast/something/fIlE_nAme.mp3')

        result = rss_entry.to_file_name()

        self.assertEqual(result, expected, f'File should be named "{expected}" not "{result}"')


if __name__ == '__main__':
    unittest.main()
