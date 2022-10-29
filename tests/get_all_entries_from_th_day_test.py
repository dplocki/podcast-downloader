import unittest

from podcast_downloader.configuration import (
    WEEK_DAYS,
    get_label_to_date,
    get_nth_day,
    get_week_day,
    parse_day_label,
)


class TestGetNthDay(unittest.TestCase):
    def test_parse_day_label_correct_values(self):
        test_parameters = {
            "Monday": "Monday",
            "mon": "Monday",
            "wednesday": "Wednesday",
            "fRIDay": "Friday",
            "saturday": "Saturday",
            "1st": 1,
            "2nd": 2,
            "3rd": 3,
            "4th": 4,
            "6": 6,
            "25th": 25,
        }

        for test_value, expected_value in test_parameters.items():
            result = parse_day_label(test_value)
            self.assertEqual(result, expected_value, "Day of week incorrect recognised")

    def test_parse_day_label_incorrect_values(self):
        self.assertRaises(Exception, parse_day_label, "abcde")

    def test_get_label_to_date_correct_values(self):
        for week_day in WEEK_DAYS:
            result = get_label_to_date(week_day)
            self.assertEqual(result, get_week_day)

        for day_number in range(1, 32):
            result = get_label_to_date(day_number)
            self.assertEqual(result, get_nth_day)
