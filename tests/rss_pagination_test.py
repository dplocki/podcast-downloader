import unittest
import urllib.request
from unittest.mock import call, patch

from podcast_downloader.rss import (
    DEFAULT_MAX_RSS_PAGES,
    RSSPaginationError,
    RSSPaginationLimitExceeded,
    _SameOriginRedirectHandler,
    _http_origin,
    load_feed,
)


class FakeFeed(dict):
    def __init__(self, entries, links=None, href=None):
        super().__init__(feed={"links": links or []})
        if href:
            self["href"] = href
        self.entries = list(entries)


class RssPaginationTest(unittest.TestCase):
    @patch("podcast_downloader.rss._fetch_paginated_feed")
    @patch("podcast_downloader.rss.feedparser.parse")
    def test_load_feed_follows_next_links_and_combines_entries(self, parse, fetch):
        first = FakeFeed(["first"], [{"rel": "next", "href": "?page=2"}])
        second = FakeFeed(["second"], [{"rel": "next", "href": "page3.xml"}])
        third = FakeFeed(["third"])
        parse.return_value = first
        fetch.side_effect = [second, third]

        url = "https://example.com/show/feed.xml?page=1"
        feed = load_feed(url)

        self.assertIs(feed, first)
        self.assertEqual(["first", "second", "third"], feed.entries)
        parse.assert_called_once_with(url)
        origin = ("https", "example.com", 443)
        self.assertEqual(
            [
                call("https://example.com/show/feed.xml?page=2", origin),
                call("https://example.com/show/page3.xml", origin),
            ],
            fetch.call_args_list,
        )

    @patch("podcast_downloader.rss._fetch_paginated_feed")
    @patch("podcast_downloader.rss.feedparser.parse")
    def test_load_feed_stops_when_next_link_creates_cycle(self, parse, fetch):
        parse.return_value = FakeFeed(
            ["first"], [{"rel": "next", "href": "?page=2"}]
        )
        fetch.return_value = FakeFeed(
            ["second"], [{"rel": "next", "href": "?page=1"}]
        )
        feed = load_feed("https://example.com/feed?page=1")
        self.assertEqual(["first", "second"], feed.entries)
        fetch.assert_called_once()

    @patch("podcast_downloader.rss._fetch_paginated_feed")
    @patch("podcast_downloader.rss.feedparser.parse")
    def test_rejects_unsafe_protocol_in_next_link(self, parse, fetch):
        for target in ("file:///etc/passwd", "ftp://example.com/feed.xml"):
            with self.subTest(target=target):
                parse.return_value = FakeFeed(
                    ["first"], [{"rel": "next", "href": target}]
                )
                with self.assertRaisesRegex(RSSPaginationError, "outside"):
                    load_feed("https://example.com/feed.xml")
                fetch.assert_not_called()

    @patch("podcast_downloader.rss._fetch_paginated_feed")
    @patch("podcast_downloader.rss.feedparser.parse")
    def test_rejects_external_origin_and_hostile_url(self, parse, fetch):
        targets = (
            "https://other.example.com/feed.xml",
            "http://example.com/feed.xml",
            "https://example.com:444/feed.xml",
            "https://example.com@127.0.0.1/feed.xml",
            "//127.0.0.1/internal",
            "https://example.com:bad/feed.xml",
            "https://example.com:443@127.0.0.1/feed.xml",
        )
        for target in targets:
            with self.subTest(target=target):
                parse.return_value = FakeFeed(
                    ["first"], [{"rel": "next", "href": target}]
                )
                with self.assertRaises(RSSPaginationError):
                    load_feed("https://example.com/feed.xml")
                fetch.assert_not_called()

    @patch("podcast_downloader.rss._fetch_paginated_feed")
    @patch("podcast_downloader.rss.feedparser.parse")
    def test_feed_with_more_than_fifty_pages_downloads_all_pages(self, parse, fetch):
        parse.return_value = FakeFeed(
            ["page1"], [{"rel": "next", "href": "?page=2"}]
        )

        def make_feed(url, allowed_origin):
            number = fetch.call_count + 1
            next_links = (
                [{"rel": "next", "href": "?page=" + str(number + 1)}]
                if number < 56
                else []
            )
            return FakeFeed(["page" + str(number)], next_links)

        fetch.side_effect = make_feed
        feed = load_feed("https://example.com/feed?page=1")
        self.assertEqual(55, fetch.call_count)
        self.assertEqual(56, len(feed.entries))
        self.assertGreaterEqual(DEFAULT_MAX_RSS_PAGES, 56)

    @patch("podcast_downloader.rss._fetch_paginated_feed")
    @patch("podcast_downloader.rss.feedparser.parse")
    def test_limit_raises_instead_of_returning_incomplete_history(self, parse, fetch):
        parse.return_value = FakeFeed(
            ["first"], [{"rel": "next", "href": "?page=2"}]
        )
        fetch.return_value = FakeFeed(
            ["second"], [{"rel": "next", "href": "?page=3"}]
        )
        with self.assertRaisesRegex(RSSPaginationLimitExceeded, "max_rss_pages=2"):
            load_feed("https://example.com/feed?page=1", max_pages=2)
        fetch.assert_called_once()

    @patch("podcast_downloader.rss._fetch_paginated_feed")
    @patch("podcast_downloader.rss.feedparser.parse")
    def test_limit_accepts_exactly_the_last_page(self, parse, fetch):
        parse.return_value = FakeFeed(
            ["first"], [{"rel": "next", "href": "?page=2"}]
        )
        fetch.return_value = FakeFeed(["second"])
        feed = load_feed("https://example.com/feed?page=1", max_pages=2)
        self.assertEqual(["first", "second"], feed.entries)

    @patch("podcast_downloader.rss._fetch_paginated_feed")
    @patch("podcast_downloader.rss.feedparser.parse")
    def test_limit_accepts_cycle_on_last_allowed_page(self, parse, fetch):
        parse.return_value = FakeFeed(
            ["first"], [{"rel": "next", "href": "?page=2"}]
        )
        fetch.return_value = FakeFeed(
            ["second"], [{"rel": "next", "href": "?page=1"}]
        )
        feed = load_feed("https://example.com/feed?page=1", max_pages=2)
        self.assertEqual(["first", "second"], feed.entries)

    @patch("podcast_downloader.rss._fetch_paginated_feed")
    @patch("podcast_downloader.rss.feedparser.parse")
    def test_failed_next_page_does_not_return_partial_history(self, parse, fetch):
        parse.return_value = FakeFeed(
            ["first"], [{"rel": "next", "href": "?page=2"}]
        )
        fetch.side_effect = RSSPaginationError("network failure")
        with self.assertRaisesRegex(RSSPaginationError, "network failure"):
            load_feed("https://example.com/feed?page=1")

    @patch("podcast_downloader.rss.feedparser.parse")
    def test_invalid_limits_fail_before_fetching(self, parse):
        for invalid in (0, -1, None, True, 1.5, "50"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    load_feed("https://example.com/feed", max_pages=invalid)
        parse.assert_not_called()

    @patch("podcast_downloader.rss._fetch_paginated_feed")
    @patch("podcast_downloader.rss.feedparser.parse")
    def test_unrelated_links_are_ignored(self, parse, fetch):
        parse.return_value = FakeFeed(
            ["first"], [{"rel": "self", "href": "/feed.xml"}, {"rel": "next"}]
        )
        feed = load_feed("https://example.com/feed.xml")
        self.assertEqual(["first"], feed.entries)
        fetch.assert_not_called()

    def test_origin_normalizes_default_ports_but_not_distinct_ports(self):
        self.assertEqual(
            _http_origin("HTTPS://EXAMPLE.com:443/feed"),
            _http_origin("https://example.com/feed"),
        )
        self.assertNotEqual(
            _http_origin("https://example.com:8443/feed"),
            _http_origin("https://example.com/feed"),
        )
        self.assertIsNone(_http_origin("https://example.com:bad/feed"))
        self.assertIsNone(_http_origin("https://username:token@example.com/feed"))

    def test_cross_origin_redirect_is_blocked_before_request(self):
        handler = _SameOriginRedirectHandler(("https", "example.com", 443))
        request = urllib.request.Request("https://example.com/page2")
        for target in (
            "http://127.0.0.1/internal",
            "https://example.com:444/page3",
            "https://elsewhere.example/page3",
        ):
            with self.subTest(target=target):
                with self.assertRaises(RSSPaginationError):
                    handler.redirect_request(request, None, 302, "Found", {}, target)

    def test_same_origin_redirect_is_permitted(self):
        handler = _SameOriginRedirectHandler(("https", "example.com", 443))
        request = urllib.request.Request("https://example.com/page2")
        redirect = handler.redirect_request(
            request, None, 302, "Found", {},
            "https://example.com:443/page3",
        )
        self.assertEqual("https://example.com:443/page3", redirect.full_url)


if __name__ == "__main__":
    unittest.main()
