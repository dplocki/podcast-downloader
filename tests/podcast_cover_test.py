import os
import tempfile
import urllib.request
import unittest
from unittest.mock import MagicMock, call, patch

import feedparser

from podcast_downloader.cover import (
    COVER_DOWNLOAD_CHUNK_SIZE,
    COVER_TIMEOUT_SECONDS,
    MAX_COVER_BYTES,
    _CoverRedirectHandler,
    _cover_request_headers,
    _open_cover_request,
    download_podcast_cover,
    find_existing_podcast_cover,
    get_podcast_cover_extension,
    get_podcast_cover_url,
)


class PodcastCoverTest(unittest.TestCase):
    def test_get_cover_url_from_feed_image(self):
        feed = feedparser.FeedParserDict(
            feed=feedparser.FeedParserDict(
                image=feedparser.FeedParserDict(href="https://example.com/cover.jpg")
            )
        )

        self.assertEqual(
            "https://example.com/cover.jpg", get_podcast_cover_url(feed)
        )

    def test_get_cover_extension_ignores_query_string(self):
        self.assertEqual(
            ".jpg",
            get_podcast_cover_extension(
                "https://example.com/cover.jpg?width=1500&height=1500"
            ),
        )

    def test_get_cover_extension_uses_content_type_when_url_has_no_extension(self):
        self.assertEqual(
            ".png",
            get_podcast_cover_extension(
                "https://example.com/artwork", "image/png; charset=binary"
            ),
        )

    def test_get_cover_extension_accepts_common_content_type_aliases(self):
        aliases = {
            "image/jpg": ".jpg",
            "image/pjpeg": ".jpg",
            "image/x-png": ".png",
        }

        for content_type, expected_extension in aliases.items():
            with self.subTest(content_type=content_type):
                self.assertEqual(
                    expected_extension,
                    get_podcast_cover_extension(
                        "https://example.com/artwork", content_type
                    ),
                )

    def test_existing_cover_is_detected_regardless_of_extension(self):
        with tempfile.TemporaryDirectory() as directory:
            cover_path = os.path.join(directory, "cover.bmp")
            with open(cover_path, "wb") as cover_file:
                cover_file.write(b"cover")

            self.assertEqual(cover_path, find_existing_podcast_cover(directory))

    def test_partial_cover_is_not_treated_as_existing_cover(self):
        with tempfile.TemporaryDirectory() as directory:
            partial_cover_path = os.path.join(directory, "cover.jpg.part")
            with open(partial_cover_path, "wb") as cover_file:
                cover_file.write(b"partial")

            self.assertIsNone(find_existing_podcast_cover(directory))

    @patch("podcast_downloader.cover._open_cover_request")
    def test_cover_is_streamed_to_disk_in_chunks(self, urlopen):
        response = MagicMock()
        response.headers.get.return_value = "image/jpeg"
        response.read.side_effect = [b"first", b"second", b""]
        urlopen.return_value.__enter__.return_value = response

        feed = feedparser.FeedParserDict(
            feed=feedparser.FeedParserDict(
                image=feedparser.FeedParserDict(href="https://example.com/cover.jpg")
            )
        )

        with tempfile.TemporaryDirectory() as directory:
            cover_path = download_podcast_cover({}, directory, feed)

            with open(cover_path, "rb") as cover_file:
                self.assertEqual(b"firstsecond", cover_file.read())

            self.assertEqual(
                [call(COVER_DOWNLOAD_CHUNK_SIZE)] * 3,
                response.read.call_args_list,
            )

    @patch("podcast_downloader.cover._open_cover_request")
    def test_failed_download_does_not_leave_partial_cover(self, urlopen):
        response = MagicMock()
        response.headers.get.return_value = "image/jpeg"
        response.read.side_effect = OSError("connection interrupted")
        urlopen.return_value.__enter__.return_value = response

        feed = feedparser.FeedParserDict(
            feed=feedparser.FeedParserDict(
                image=feedparser.FeedParserDict(href="https://example.com/cover.jpg")
            )
        )

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(OSError):
                download_podcast_cover({}, directory, feed)

            self.assertIsNone(find_existing_podcast_cover(directory))
            self.assertFalse(os.path.exists(os.path.join(directory, "cover.jpg.part")))


class CoverSecurityTest(unittest.TestCase):
    def test_headers_remain_only_on_same_origin(self):
        secrets = {
            "Authorization": "Bearer artwork-secret",
            "Cookie": "session=private",
            "X-Private": "private",
        }
        keep = _cover_request_headers(
            "https://example.org/rss.xml",
            "https://EXAMPLE.org:443/cover.jpg",
            secrets,
        )
        self.assertEqual(secrets, keep)

        for cover in (
            "https://cdn.example.org/cover.jpg",
            "http://example.org/cover.jpg",
            "https://example.org:444/cover.jpg",
        ):
            with self.subTest(cover=cover):
                self.assertEqual(
                    {"User-Agent": "podcast-downloader"},
                    _cover_request_headers(
                        "https://example.org/rss.xml", cover, secrets
                    ),
                )

    def test_url_with_embedded_credentials_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            _cover_request_headers(
                "https://example.org/rss.xml",
                "https://user:secret@example.org/cover.jpg",
                {"Authorization": "secret"},
            )

    def test_cross_origin_redirect_drops_feed_credentials(self):
        handler = _CoverRedirectHandler()
        request = urllib.request.Request(
            "https://example.org/cover.jpg",
            headers={
                "Authorization": "Bearer artwork-secret",
                "X-Private": "private",
            },
        )
        redirect = handler.redirect_request(
            request, None, 302, "Found", {},
            "https://cdn.example.org/cover.jpg",
        )
        self.assertIsNone(redirect.get_header("Authorization"))
        self.assertIsNone(redirect.get_header("X-private"))
        self.assertEqual(
            "podcast-downloader", redirect.get_header("User-agent")
        )

    def test_same_origin_redirect_keeps_feed_credentials(self):
        handler = _CoverRedirectHandler()
        request = urllib.request.Request(
            "https://example.org/cover.jpg",
            headers={"Authorization": "Bearer artwork-secret"},
        )
        redirect = handler.redirect_request(
            request, None, 302, "Found", {},
            "https://example.org:443/cover2.jpg",
        )
        self.assertEqual(
            "Bearer artwork-secret", redirect.get_header("Authorization")
        )

    @patch("podcast_downloader.cover.urllib.request.build_opener")
    def test_cover_request_uses_timeout(self, build_opener):
        request = urllib.request.Request("https://example.org/cover.jpg")
        _open_cover_request(request)
        build_opener.return_value.open.assert_called_once_with(
            request, timeout=COVER_TIMEOUT_SECONDS
        )

    @patch("podcast_downloader.cover._open_cover_request")
    def test_large_content_length_is_rejected_before_writing(self, opener):
        response = MagicMock()
        response.headers.get.side_effect = lambda key: (
            "image/jpeg"
            if key == "Content-Type"
            else str(MAX_COVER_BYTES + 1)
        )
        opener.return_value.__enter__.return_value = response
        feed = feedparser.FeedParserDict(
            feed=feedparser.FeedParserDict(
                image=feedparser.FeedParserDict(href="https://example.org/cover.jpg")
            )
        )
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "exceeds"):
                download_podcast_cover({}, folder, feed)
            self.assertEqual([], os.listdir(folder))
            response.read.assert_not_called()

    @patch("podcast_downloader.cover._open_cover_request")
    def test_streaming_size_limit_cleans_temporary_file(self, opener):
        response = MagicMock()
        response.headers.get.side_effect = lambda key: (
            "image/jpeg" if key == "Content-Type" else None
        )
        response.read.side_effect = [b"123456", b"7890", b""]
        opener.return_value.__enter__.return_value = response
        feed = feedparser.FeedParserDict(
            feed=feedparser.FeedParserDict(
                image=feedparser.FeedParserDict(href="https://example.org/cover.jpg")
            )
        )
        with tempfile.TemporaryDirectory() as folder:
            with patch("podcast_downloader.cover.MAX_COVER_BYTES", 8):
                with self.assertRaisesRegex(ValueError, "exceeds"):
                    download_podcast_cover({}, folder, feed)
            self.assertEqual([], os.listdir(folder))

    @patch("podcast_downloader.cover._open_cover_request")
    def test_short_cover_body_is_not_published(self, opener):
        response = MagicMock()
        response.headers.get.side_effect = lambda key: (
            "image/jpeg" if key == "Content-Type" else "1000"
        )
        response.read.side_effect = [b"small", b""]
        opener.return_value.__enter__.return_value = response
        feed = feedparser.FeedParserDict(
            feed=feedparser.FeedParserDict(
                image=feedparser.FeedParserDict(href="https://example.org/cover.jpg")
            )
        )
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(IOError, "Incomplete"):
                download_podcast_cover({}, folder, feed)
            self.assertEqual([], os.listdir(folder))




if __name__ == "__main__":
    unittest.main()
