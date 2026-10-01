import io
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from podcast_downloader.rss import (
    FEED_TIMEOUT_SECONDS,
    flatten_rss_links_data,
    get_feed_title_from_feed,
    load_feed,
)


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class RssResilienceTest(unittest.TestCase):
    def test_malformed_entry_does_not_hide_following_valid_entry(self):
        valid_date = time.gmtime()
        entries = [
            {
                "title": "Missing date",
                "links": [
                    {
                        "type": "audio/mpeg",
                        "href": "https://example.com/bad.mp3",
                    }
                ],
            },
            {
                "title": "Valid episode",
                "published_parsed": valid_date,
                "links": [
                    {
                        "type": "audio/mpeg",
                        "href": "https://example.com/good.mp3",
                    }
                ],
            },
        ]

        result = list(flatten_rss_links_data(iter(entries)))

        self.assertEqual(1, len(result))
        self.assertEqual("Valid episode", result[0].title)
        self.assertEqual("https://example.com/good.mp3", result[0].link)

    def test_updated_date_is_used_when_published_date_is_missing(self):
        updated_date = time.gmtime()
        entries = [
            {
                "updated_parsed": updated_date,
                "links": [
                    {
                        "type": "audio/mpeg",
                        "href": "https://example.com/ep.mp3",
                    }
                ],
            }
        ]

        result = list(flatten_rss_links_data(iter(entries)))

        self.assertEqual(1, len(result))
        self.assertEqual(updated_date, result[0].published_date)
        self.assertEqual("", result[0].title)

    def test_links_without_type_or_href_are_skipped(self):
        entries = [
            {
                "published_parsed": time.gmtime(),
                "links": [
                    {"href": "https://example.com/no-type.mp3"},
                    {"type": "audio/mpeg"},
                ],
            }
        ]

        self.assertEqual([], list(flatten_rss_links_data(iter(entries))))

    def test_ascending_entries_are_reversed(self):
        older = time.strptime("2026-08-01", "%Y-%m-%d")
        newer = time.strptime("2026-08-02", "%Y-%m-%d")
        entries = [
            {
                "title": "Older",
                "published_parsed": older,
                "links": [
                    {
                        "type": "audio/mpeg",
                        "href": "https://example.com/old.mp3",
                    }
                ],
            },
            {
                "title": "Newer",
                "published_parsed": newer,
                "links": [
                    {
                        "type": "audio/mpeg",
                        "href": "https://example.com/new.mp3",
                    }
                ],
            },
        ]

        result = list(flatten_rss_links_data(iter(entries)))

        self.assertEqual(["Newer", "Older"], [entry.title for entry in result])

    def test_descending_entries_keep_their_order_including_ties(self):
        newest = time.strptime("2026-08-03", "%Y-%m-%d")
        tied = time.strptime("2026-08-02", "%Y-%m-%d")
        entries = [
            {
                "title": "Newest",
                "published_parsed": newest,
                "links": [
                    {
                        "type": "audio/mpeg",
                        "href": "https://example.com/new.mp3",
                    }
                ],
            },
            {
                "title": "First tied",
                "published_parsed": tied,
                "links": [
                    {
                        "type": "audio/mpeg",
                        "href": "https://example.com/first.mp3",
                    }
                ],
            },
            {
                "title": "Second tied",
                "published_parsed": tied,
                "links": [
                    {
                        "type": "audio/mpeg",
                        "href": "https://example.com/second.mp3",
                    }
                ],
            },
        ]

        result = list(flatten_rss_links_data(iter(entries)))

        self.assertEqual(
            ["Newest", "First tied", "Second tied"], [entry.title for entry in result]
        )

    def test_descending_feed_with_recent_bottom_entry_is_not_reversed(self):
        entries = []
        for title, date in (
            ("Episode 10", "2026-08-10"),
            ("Episode 9", "2026-08-09"),
            ("Episode 8", "2026-08-08"),
            ("Trailer", "2026-08-20"),
        ):
            entries.append(
                {
                    "title": title,
                    "published_parsed": time.strptime(date, "%Y-%m-%d"),
                    "links": [
                        {
                            "type": "audio/mpeg",
                            "href": f"https://example.com/{title}.mp3",
                        }
                    ],
                }
            )

        result = list(flatten_rss_links_data(iter(entries)))

        self.assertEqual(
            ["Episode 10", "Episode 9", "Episode 8", "Trailer"],
            [entry.title for entry in result],
        )

    def test_missing_feed_title_returns_empty_string(self):
        feed = {"feed": {}}

        class Feed(dict):
            @property
            def feed(self):
                return self["feed"]

        self.assertEqual("", get_feed_title_from_feed(Feed(feed)))

    def test_feed_download_uses_timeout_and_configured_headers(self):
        xml = (
            b"<?xml version='1.0'?><rss version='2.0'><channel>"
            b"<title>Test</title></channel></rss>"
        )
        headers = {"User-Agent": "custom-agent", "Authorization": "Bearer test"}

        with patch(
            "podcast_downloader.rss.urllib.request.urlopen",
            return_value=Response(xml),
        ) as urlopen:
            feed = load_feed("https://example.com/feed.xml", headers)

        self.assertEqual("Test", feed.feed.title)
        self.assertEqual(FEED_TIMEOUT_SECONDS, urlopen.call_args.kwargs["timeout"])
        request = urlopen.call_args.args[0]
        self.assertEqual("custom-agent", request.get_header("User-agent"))
        self.assertEqual("Bearer test", request.get_header("Authorization"))

    def test_explicit_empty_headers_are_preserved(self):
        xml = (
            b"<?xml version='1.0'?><rss version='2.0'><channel>"
            b"<title>Test</title></channel></rss>"
        )

        with patch(
            "podcast_downloader.rss.urllib.request.urlopen",
            return_value=Response(xml),
        ) as urlopen:
            feed = load_feed("https://example.com/feed.xml", {})

        self.assertEqual("Test", feed.feed.title)
        request = urlopen.call_args.args[0]
        self.assertIsNone(request.get_header("User-agent"))

    def test_local_feed_path_remains_supported(self):
        xml = (
            "<?xml version='1.0'?><rss version='2.0'><channel>"
            "<title>Local</title></channel></rss>"
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "feed.xml"
            path.write_text(xml, encoding="utf-8")
            feed = load_feed(str(path))

        self.assertEqual("Local", feed.feed.title)

    def test_feed_network_error_becomes_bozo_feed(self):
        with patch(
            "podcast_downloader.rss.urllib.request.urlopen",
            side_effect=TimeoutError("timeout"),
        ):
            feed = load_feed("https://example.com/feed.xml")

        self.assertTrue(feed.bozo)
        self.assertEqual([], feed.entries)
        self.assertIsInstance(feed.bozo_exception, TimeoutError)


if __name__ == "__main__":
    unittest.main()
