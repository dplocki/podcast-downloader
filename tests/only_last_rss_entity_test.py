import unittest

from podcast_downloader.rss import\
    RSSEntityWithDate,\
    only_last_entity

from commons import build_timestamp


class TestOnlyLastRSSEntity(unittest.TestCase):

    def test_get_only_last_rss_entity(self):
        # Assign
        entity_1 = RSSEntityWithDate(build_timestamp(2020, 1, 10), 'http://www.p.com/file0005.mp3')
        entity_2 = RSSEntityWithDate(build_timestamp(2020, 1, 9), 'http://www.p.com/file0004.mp3')
        entity_3 = RSSEntityWithDate(build_timestamp(2020, 1, 8), 'http://www.p.com/file0003.mp3')
        entity_4 = RSSEntityWithDate(build_timestamp(2020, 1, 7), 'http://www.p.com/file0002.mp3')
        entity_5 = RSSEntityWithDate(build_timestamp(2020, 1, 6), 'http://www.p.com/file0001.mp3')

        rss_entites = [entity_1, entity_2, entity_3, entity_4, entity_5]
        expected = [entity_1]

        # Act
        result = list(only_last_entity(rss_entites))

        # Assert
        self.assertSequenceEqual(
            result, expected, "Only the last entity should be return as result")
