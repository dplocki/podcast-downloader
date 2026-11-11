import unittest
from unittest.mock import call, patch

from podcast_downloader.rss import MAX_RSS_PAGES, load_feed


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
    def test_load_feed_limits_pagination_to_fifty_pages(self, parse):
        def make_feed(url):
            return FakeFeed(
                [url],
                [{"rel": "next", "href": "?page=" + str(parse.call_count + 1)}],
            )

        parse.side_effect = make_feed

        with self.assertLogs("podcast_downloader.rss", level="WARNING") as logs:
            feed = load_feed("https://example.com/feed?page=1")

        self.assertEqual(MAX_RSS_PAGES, parse.call_count)
        self.assertEqual(MAX_RSS_PAGES, len(feed.entries))
        self.assertTrue(any("pagination stopped" in line for line in logs.output))

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
