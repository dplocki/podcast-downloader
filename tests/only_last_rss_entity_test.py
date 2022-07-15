import unittest

from podcast_downloader.rss import only_last_entity
from commons import rss_entity_generator


class TestOnlyLastRSSEntity(unittest.TestCase):
    def test_get_only_last_rss_entity(self):
        # Assign
        entity_1, entity_2, entity_3, entity_4, entity_5 = rss_entity_generator(limit=5)

        rss_entities = [entity_1, entity_2, entity_3, entity_4, entity_5]
        expected = [entity_1]

        # Act
        result = list(only_last_entity(rss_entities))

        # Assert
        self.assertSequenceEqual(
            result, expected, "Only the last entity should be return as result"
        )
