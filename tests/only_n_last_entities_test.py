import unittest

from podcast_downloader.rss import only_last_n_entities
from commons import rss_entity_generator


class TestOnlyNLastRSSEntity(unittest.TestCase):
    def test_get_only_last_n_rss_entities_happy_path(self):
        # Assign
        entity_1, entity_2, entity_3, entity_4, entity_5 = rss_entity_generator(limit=5)

        rss_entities = [entity_1, entity_2, entity_3, entity_4, entity_5]
        expected = [entity_1, entity_2]

        # Act
        result = list(only_last_n_entities(2, rss_entities))

        # Assert
        self.assertSequenceEqual(
            result, expected, "Only the last entity should be return as result"
        )

    def test_get_only_last_n_rss_entities_less_than_required(self):
        # Assign
        entity_1 = rss_entity_generator(limit=1)

        rss_entities = [entity_1]
        expected = [entity_1]

        # Act
        result = list(only_last_n_entities(2, rss_entities))

        # Assert
        self.assertSequenceEqual(
            result, expected, "Only the last entity should be return as result"
        )
