import unittest

import feedparser

from podcast_downloader.rss import flatten_rss_links_data


def parse_items(items_xml):
    feed_xml = (
        '<?xml version="1.0"?><rss version="2.0"><channel>'
        "<title>Feed</title>" + items_xml + "</channel></rss>"
    )
    return feedparser.parse(feed_xml).entries


class TestFlattenRSSLinksData(unittest.TestCase):
    def test_entries_without_published_date_are_skipped(self):
        # Assign: one dated entry plus one entry without any date element
        entries = parse_items(
            "<item><title>Dated</title>"
            "<pubDate>Mon, 10 Feb 2020 17:03:38 GMT</pubDate>"
            '<enclosure url="http://www.p.com/dated.mp3" type="audio/mpeg"/>'
            "</item>"
            "<item><title>Undated</title>"
            '<enclosure url="http://www.p.com/undated.mp3" type="audio/mpeg"/>'
            "</item>"
        )

        # Act
        result = list(flatten_rss_links_data(iter(entries)))

        # Assert: no AttributeError, dated entry kept, undated one skipped
        links = [entity.link for entity in result]
        self.assertIn("http://www.p.com/dated.mp3", links)
        self.assertNotIn("http://www.p.com/undated.mp3", links)

    def test_dated_entries_still_flatten(self):
        entries = parse_items(
            "<item><title>Dated</title>"
            "<pubDate>Mon, 10 Feb 2020 17:03:38 GMT</pubDate>"
            '<enclosure url="http://www.p.com/dated.mp3" type="audio/mpeg"/>'
            "</item>"
        )

        result = list(flatten_rss_links_data(iter(entries)))

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, "Dated")
        self.assertEqual(result[0].link, "http://www.p.com/dated.mp3")


if __name__ == "__main__":
    unittest.main()
