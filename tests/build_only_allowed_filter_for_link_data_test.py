from datetime import datetime
from typing import Tuple
import unittest

from podcast_downloader.rss import build_only_allowed_filter_for_link_data


def build_test_link_data(type: str) -> Tuple[datetime.date, str, str]:
    return (None, type, None)


class TestBuildOnlyAllowedFilterForLinkData(unittest.TestCase):
    def test_build_rss_entries_filter(self):
        allowed_types = ["a", "b"]
        result_filter = build_only_allowed_filter_for_link_data(allowed_types)

        self.assertTrue(
            result_filter(build_test_link_data("a")),
            "The type 'a' is on the allowed list",
        )
        self.assertTrue(
            result_filter(build_test_link_data("b")),
            "The type 'b' is on the allowed list",
        )
        self.assertFalse(
            result_filter(build_test_link_data("ab")),
            "The type 'ab' is not on the allowed list",
        )
        self.assertFalse(
            result_filter(build_test_link_data("c")),
            "The type 'c' is not on the allowed list",
        )
