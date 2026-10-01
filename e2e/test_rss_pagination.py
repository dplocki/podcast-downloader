from typing import Callable, Dict, List

from pytest_httpserver import HTTPServer

from e2e.fixures import (
    PodcastDirectory,
    PodcastDownloaderRunner,
    download_destination_directory,
    podcast_directory,
    podcast_downloader,
    use_config,
)


def build_rss_page(title: str, enclosure_url: str, published: str, next_link=None):
    pagination_link = (
        f'<atom:link rel="next" type="application/rss+xml" href="{next_link}"/>'
        if next_link
        else ""
    )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Paginated podcast</title>
    {pagination_link}
    <item>
      <title>{title}</title>
      <pubDate>{published}</pubDate>
      <enclosure url="{enclosure_url}" length="11" type="audio/mpeg"/>
    </item>
  </channel>
</rss>
"""


def test_downloads_entries_from_all_rss_pages(
    httpserver: HTTPServer,
    use_config: Callable[[Dict], None],
    podcast_downloader: Callable[[List[str]], PodcastDownloaderRunner],
    podcast_directory: PodcastDirectory,
):
    first_file = "first-page.mp3"
    second_file = "second-page.mp3"
    first_file_url = httpserver.url_for("/" + first_file)
    second_file_url = httpserver.url_for("/" + second_file)

    httpserver.expect_request("/feed.xml").respond_with_data(
        build_rss_page(
            "First page episode",
            first_file_url,
            "Fri, 04 Sep 2026 10:00:00 +0000",
            "/feed-page-2.xml",
        ),
        content_type="application/rss+xml",
    )
    httpserver.expect_request("/feed-page-2.xml").respond_with_data(
        build_rss_page(
            "Second page episode",
            second_file_url,
            "Thu, 03 Sep 2026 10:00:00 +0000",
        ),
        content_type="application/rss+xml",
    )
    httpserver.expect_request("/" + first_file).respond_with_data("first audio")
    httpserver.expect_request("/" + second_file).respond_with_data("second audio")

    use_config(
        {
            "if_directory_empty": "download_all_from_feed",
            "podcasts": [
                {
                    "path": podcast_directory.path(),
                    "rss_link": httpserver.url_for("/feed.xml"),
                }
            ],
        }
    )

    podcast_downloader.run()

    podcast_directory.is_containing_only([first_file, second_file])
