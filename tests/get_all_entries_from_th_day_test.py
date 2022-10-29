import unittest

from podcast_downloader.configuration import parse_day_label


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
