import unittest

from time import strftime
from copy import deepcopy
from podcast_downloader.configuration import get_n_age_date
from podcast_downloader.rss import (
    is_entity_newer,
    only_entities_from_date,
)
from commons import rss_entity_generator, build_timestamp

class TestAllEntitiesFromNDays(unittest.TestCase):
    def test_of_filter_function(self):
        # Assign
        entity_future, entity_same_day, entity_older = rss_entity_generator(
            day=10, limit=3
        )

        entity_same_day_1 = deepcopy(entity_same_day)
        entity_same_day_1.published_date = (2020, 1, 9, 1, 10, 0)

        entity_same_day_2 = deepcopy(entity_same_day)
        entity_same_day_2.published_date = (2020, 1, 9, 23, 10, 0)

        date = build_timestamp(2020, 1, 9)

        # Act and Assert
        self.assertFalse(
            is_entity_newer(date, entity_older), "Older entity should be filter out"
        )
        self.assertTrue(
            is_entity_newer(date, entity_same_day_1),
            "Same day entity (early hour) should be accepted",
        )
        self.assertTrue(
            is_entity_newer(date, entity_same_day_2),
            "Same day entity (late hour) should be accepted",
        )
        self.assertTrue(
            is_entity_newer(date, entity_future), "Newer entity should be accepted"
        )

    def test_of_get_n_age_date(self):
        self.assertEqual(
            strftime("%d %b %Y", get_n_age_date(3, build_timestamp(2020, 1, 1))),
            strftime("%d %b %Y", build_timestamp(2019, 12, 29)),
            "Date wasn't calculate correctly",
        )

    def test_should_return_empty_collection(self):
        entity_1, entity_2, entity_3, entity_4, entity_5 = rss_entity_generator(
            day=10, limit=5
        )
        entities = [entity_1, entity_2, entity_3, entity_4, entity_5]
        from_date = build_timestamp(2020, 1, 11)

        results = list(only_entities_from_date(from_date)(entities))

        self.assertSequenceEqual(
            results,
            [],
            "The 'from date' was after all entities, the result should be empty",
        )

    def test_should_return_filtered_collection(self):
        entity_1, entity_2, entity_3, entity_4, entity_5 = rss_entity_generator(
            day=10, limit=5
        )
        entities = [entity_1, entity_2, entity_3, entity_4, entity_5]
        expected = [entity_1, entity_2]
        from_date = build_timestamp(2020, 1, 9)

        results = list(only_entities_from_date(from_date)(entities))

        self.assertSequenceEqual(
            results, expected, "The 'from date' was before two entities"
        )
