import unittest

from main import file_name_to_entry_link_name, RSSEntity, only_new_entites


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


class TestFindNewRSSEntites(unittest.TestCase):

    def test_find_one_rss_entites(self):
        # Assing
        new_one = RSSEntity((2020, 1, 2, 17, 3, 38, 1, 48, 0), 'http://www.p.com/file0002.mp3')
        old_one = RSSEntity((2020, 1, 1, 11, 3, 38, 1, 48, 0), 'http://www.p.com/file0001.mp3')
        rss_entites = [new_one, old_one]
        downloaded = ['[20200101] file0001.mp3']
        expected = [new_one]

        # Act
        result = list(only_new_entites(rss_entites, downloaded))

        # Assert
        self.assertSequenceEqual(result, expected, "A new_one entity should be return as result")


if __name__ == '__main__':
    unittest.main()
