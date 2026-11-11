import unittest

from podcast_downloader.configuration import (
    CONFIG_MAX_RSS_PAGES,
    configuration_verification,
)


class RssPaginationConfigurationTest(unittest.TestCase):
    def setUp(self):
        self.podcast = {
            "name": "Example",
            "rss_link": "https://example.com/feed.xml",
            "path": "/tmp/podcasts",
        }

    def test_global_limit_accepts_positive_integer(self):
        for count in (1, 50, 56, 1000, 10000):
            with self.subTest(count=count):
                result = configuration_verification(
                    {"podcasts": [self.podcast], CONFIG_MAX_RSS_PAGES: count}
                )
                self.assertEqual((True, None), result)

    def test_per_podcast_limit_accepts_positive_integer(self):
        self.podcast[CONFIG_MAX_RSS_PAGES] = 1500
        self.assertEqual(
            (True, None),
            configuration_verification({"podcasts": [self.podcast]}),
        )

    def test_invalid_limits_are_rejected(self):
        for invalid in (0, -10, None, True, 1.5, "1000"):
            with self.subTest(invalid=invalid):
                self.assertFalse(
                    configuration_verification(
                        {"podcasts": [self.podcast], CONFIG_MAX_RSS_PAGES: invalid}
                    )[0]
                )
                self.assertFalse(
                    configuration_verification(
                        {"podcasts": [dict(self.podcast, max_rss_pages=invalid)]}
                    )[0]
                )


if __name__ == "__main__":
    unittest.main()
