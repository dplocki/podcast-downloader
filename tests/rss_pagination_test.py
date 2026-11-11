import unittest
from unittest.mock import call, patch

from podcast_downloader.rss import (
    DEFAULT_MAX_RSS_PAGES,
    RSSPaginationError,
    RSSPaginationLimitExceeded,
    load_feed,
)


class FakeFeed(dict):
    def __init__(self, entries, links=None, href=None):
        super().__init__(feed={"links": links or []})
        if href:
            self["href"] = href
        self.entries = list(entries)


class RssPaginationTest(unittest.TestCase):
    @patch("podcast_downloader.rss.feedparser.parse")
    def test_load_feed_follows_next_links_and_combines_entries(self, parse):
        first_page = FakeFeed(
            ["first"],
            [{"rel": "next", "href": "?page=2"}],
        )
        second_page = FakeFeed(
            ["second"],
            [{"rel": "next", "href": "page3.xml"}],
        )
        third_page = FakeFeed(["third"])
        parse.side_effect = [first_page, second_page, third_page]

        feed = load_feed("https://example.com/show/feed.xml?page=1")

        self.assertIs(feed, first_page)
        self.assertEqual(["first", "second", "third"], feed.entries)
        self.assertEqual(
            [
                call("https://example.com/show/feed.xml?page=1"),
                call("https://example.com/show/feed.xml?page=2"),
                call("https://example.com/show/page3.xml"),
            ],
            parse.call_args_list,
        )

    @patch("podcast_downloader.rss.feedparser.parse")
    def test_load_feed_stops_when_next_link_creates_cycle(self, parse):
        first_page = FakeFeed(
            ["first"],
            [{"rel": "next", "href": "?page=2"}],
        )
        second_page = FakeFeed(
            ["second"],
            [{"rel": "next", "href": "?page=1"}],
        )
        parse.side_effect = [first_page, second_page]

        feed = load_feed("https://example.com/feed?page=1")

        self.assertEqual(["first", "second"], feed.entries)
        self.assertEqual(2, parse.call_count)

    @patch("podcast_downloader.rss.feedparser.parse")
    def test_load_feed_rejects_file_protocol_pagination(self, parse):
        first_page = FakeFeed(
            ["first"],
            [{"rel": "next", "href": "file:///etc/passwd"}],
        )
        parse.return_value = first_page

        with self.assertLogs("podcast_downloader.rss", level="WARNING"):
            feed = load_feed("https://example.com/feed.xml")

        self.assertEqual(["first"], feed.entries)
        parse.assert_called_once_with("https://example.com/feed.xml")

    @patch("podcast_downloader.rss.feedparser.parse")
    def test_feed_with_more_than_fifty_pages_downloads_all_pages(self, parse):
        def make_feed(url):
            number = parse.call_count
            next_links = (
                [{"rel": "next", "href": "?page=" + str(number + 1)}]
                if number < 56
                else []
            )
            return FakeFeed([url], next_links)

        parse.side_effect = make_feed
        feed = load_feed("https://example.com/feed?page=1")

        self.assertEqual(56, parse.call_count)
        self.assertEqual(56, len(feed.entries))
        self.assertGreaterEqual(DEFAULT_MAX_RSS_PAGES, 56)

    @patch("podcast_downloader.rss.feedparser.parse")
    def test_limit_raises_instead_of_returning_incomplete_history(self, parse):
        def make_feed(url):
            number = parse.call_count
            return FakeFeed(
                [url], [{"rel": "next", "href": "?page=" + str(number + 1)}]
            )

        parse.side_effect = make_feed

        with self.assertRaisesRegex(RSSPaginationLimitExceeded, "max_rss_pages=2"):
            load_feed("https://example.com/feed?page=1", max_pages=2)

        self.assertEqual(2, parse.call_count)

    @patch("podcast_downloader.rss.feedparser.parse")
    def test_limit_accepts_exactly_the_last_page(self, parse):
        parse.side_effect = [
            FakeFeed(["first"], [{"rel": "next", "href": "?page=2"}]),
            FakeFeed(["second"]),
        ]

        feed = load_feed("https://example.com/feed?page=1", max_pages=2)
        self.assertEqual(["first", "second"], feed.entries)
        self.assertEqual(2, parse.call_count)

    @patch("podcast_downloader.rss.feedparser.parse")
    def test_limit_accepts_cycle_on_last_allowed_page(self, parse):
        parse.side_effect = [
            FakeFeed(["first"], [{"rel": "next", "href": "?page=2"}]),
            FakeFeed(["second"], [{"rel": "next", "href": "?page=1"}]),
        ]
        feed = load_feed("https://example.com/feed?page=1", max_pages=2)
        self.assertEqual(["first", "second"], feed.entries)

    @patch("podcast_downloader.rss.feedparser.parse")
    def test_failed_next_page_does_not_return_partial_history(self, parse):
        failure = FakeFeed([])
        failure["bozo"] = True
        failure["bozo_exception"] = ValueError("invalid feed")
        parse.side_effect = [
            FakeFeed(["first"], [{"rel": "next", "href": "?page=2"}]),
            failure,
        ]

        with self.assertRaisesRegex(RSSPaginationError, "invalid feed"):
            load_feed("https://example.com/feed?page=1")
        self.assertEqual(2, parse.call_count)

    @patch("podcast_downloader.rss.feedparser.parse")
    def test_invalid_limits_fail_before_fetching(self, parse):
        for invalid in (0, -1, None, True, 1.5, "50"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    load_feed("https://example.com/feed", max_pages=invalid)
        parse.assert_not_called()

    @patch("podcast_downloader.rss.feedparser.parse")
    def test_load_feed_ignores_links_that_are_not_next(self, parse):
        first_page = FakeFeed(
            ["first"],
            [
                {"rel": "self", "href": "https://example.com/feed.xml"},
                {"rel": "next"},
            ],
        )
        parse.return_value = first_page

        feed = load_feed("https://example.com/feed.xml")

        self.assertEqual(["first"], feed.entries)
        self.assertEqual(1, parse.call_count)


if __name__ == "__main__":
    unittest.main()
