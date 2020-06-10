import unittest

from podcast_downloader.rss import\
    RSSEntityWithDate,\
    only_new_entites

from commons import build_timestamp


class TestFindNewRSSEntites(unittest.TestCase):

    def test_find_all_new_rss_entites(self):
        # Assign
        new_one_1 = RSSEntityWithDate(build_timestamp(2020, 1, 10), 'http://www.p.com/file0005.mp3')
        new_one_2 = RSSEntityWithDate(build_timestamp(2020, 1, 9), 'http://www.p.com/file0004.mp3')
        old_one_1 = RSSEntityWithDate(build_timestamp(2020, 1, 8), 'http://www.p.com/file0003.mp3')
        old_one_2 = RSSEntityWithDate(build_timestamp(2020, 1, 7), 'http://www.p.com/file0002.mp3')
        old_one_3 = RSSEntityWithDate(build_timestamp(2020, 1, 6), 'http://www.p.com/file0001.mp3')

        rss_entites = [new_one_1, new_one_2, old_one_1, old_one_2, old_one_3]
        last_downloaded_file = '[20200108] file0003.mp3'

        expected = [new_one_1, new_one_2]

        # Act
        result = list(only_new_entites(last_downloaded_file, rss_entites))

        # Assert
        self.assertSequenceEqual(
            result, expected, "A both new entity should be return as result")
