import os
import tempfile
import unittest
from unittest.mock import MagicMock, call, patch

import feedparser

from podcast_downloader.cover import (
    COVER_DOWNLOAD_CHUNK_SIZE,
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

    @patch("podcast_downloader.cover.urllib.request.urlopen")
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

    @patch("podcast_downloader.cover.urllib.request.urlopen")
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


if __name__ == "__main__":
    unittest.main()
