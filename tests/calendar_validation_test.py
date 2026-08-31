from time import strptime
import unittest

from podcast_downloader.configuration import (
    configuration_verification,
    get_nth_day,
    parse_day_label,
)


class CalendarValidationTest(unittest.TestCase):
    def test_28th_after_non_leap_february_rolls_to_march(self):
        current_date = strptime("04.03.2023", "%d.%m.%Y")
        expected_date = strptime("01.03.2023", "%d.%m.%Y")

        self.assertEqual(get_nth_day(28, current_date), expected_date)

    def test_28th_after_leap_february_returns_february_29(self):
        current_date = strptime("04.03.2024", "%d.%m.%Y")
        expected_date = strptime("29.02.2024", "%d.%m.%Y")

        self.assertEqual(get_nth_day(28, current_date), expected_date)

    def test_same_day_uses_previous_month(self):
        current_date = strptime("21.08.2026", "%d.%m.%Y")
        expected_date = strptime("22.07.2026", "%d.%m.%Y")

        self.assertEqual(get_nth_day(21, current_date), expected_date)

    def test_ordinal_day_labels_are_supported(self):
        for value, expected in (("21st", 21), ("22nd", 22), ("23rd", 23)):
            with self.subTest(value=value):
                self.assertEqual(expected, parse_day_label(value))

    def test_day_labels_outside_documented_range_are_rejected(self):
        for value in ("0", "29", "31", "29th", "31st"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_day_label(value)

    def test_missing_name_does_not_crash_configuration_validation(self):
        valid, error = configuration_verification(
            {"podcasts": [{"rss_link": "https://example.com/feed.xml"}]}
        )

        self.assertFalse(valid)
        self.assertIn("<unnamed>", error)
        self.assertIn("path", error)


if __name__ == "__main__":
    unittest.main()
