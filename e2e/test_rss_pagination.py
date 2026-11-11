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

def test_pagination_limit_skips_incomplete_feed(
    httpserver: HTTPServer,
    use_config: Callable[[Dict], None],
    podcast_downloader: Callable[[List[str]], PodcastDownloaderRunner],
    podcast_directory: PodcastDirectory,
):
    episode_url = httpserver.url_for("/episode.mp3")
    httpserver.expect_request("/feed.xml").respond_with_data(
        build_rss_page(
            "New episode",
            episode_url,
            "Fri, 04 Sep 2026 10:00:00 +0000",
            "/feed-2.xml",
        ),
        content_type="application/rss+xml",
    )

    use_config(
        {
            "max_rss_pages": 100,
            "if_directory_empty": "download_all_from_feed",
            "podcasts": [
                {
                    "path": podcast_directory.path(),
                    "rss_link": httpserver.url_for("/feed.xml"),
                    "max_rss_pages": 1,
                }
            ],
        }
    )

    result = podcast_downloader.run()
    assert result.is_containing("max_rss_pages=1")
    assert result.is_containing("Cannot complete RSS feed")
    podcast_directory.is_containing_only([])
    assert [request.path for request, _ in httpserver.log] == ["/feed.xml"]

def test_cross_origin_pagination_skips_partial_feed(
    httpserver: HTTPServer,
    use_config: Callable[[Dict], None],
    podcast_downloader: Callable[[List[str]], PodcastDownloaderRunner],
    podcast_directory: PodcastDirectory,
):
    media_url = httpserver.url_for("/episode.mp3")
    # A different port represents a different origin. It must never be contacted.
    bad_next_url = "http://127.0.0.1:9/internal"
    httpserver.expect_request("/feed.xml").respond_with_data(
        build_rss_page(
            "Episode",
            media_url,
            "Fri, 04 Sep 2026 10:00:00 +0000",
            bad_next_url,
        ),
        content_type="application/rss+xml",
    )

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

    result = podcast_downloader.run()
    assert result.is_containing("Blocked RSS pagination link")
    podcast_directory.is_containing_only([])
    assert [request.path for request, _ in httpserver.log] == ["/feed.xml"]


def test_redirect_to_other_origin_is_blocked_before_following(
    httpserver: HTTPServer,
    use_config: Callable[[Dict], None],
    podcast_downloader: Callable[[List[str]], PodcastDownloaderRunner],
    podcast_directory: PodcastDirectory,
):
    media_url = httpserver.url_for("/episode.mp3")
    httpserver.expect_request("/feed.xml").respond_with_data(
        build_rss_page(
            "Episode",
            media_url,
            "Fri, 04 Sep 2026 10:00:00 +0000",
            "/redirect.xml",
        ),
        content_type="application/rss+xml",
    )
    httpserver.expect_request("/redirect.xml").respond_with_data(
        "redirect", status=302, headers={"Location": "http://127.0.0.1:9/private"}
    )

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

    result = podcast_downloader.run()
    assert result.is_containing("Blocked RSS pagination redirect")
    podcast_directory.is_containing_only([])
    assert [request.path for request, _ in httpserver.log] == [
        "/feed.xml", "/redirect.xml"
    ]


def test_same_origin_redirect_is_followed(
    httpserver: HTTPServer,
    use_config: Callable[[Dict], None],
    podcast_downloader: Callable[[List[str]], PodcastDownloaderRunner],
    podcast_directory: PodcastDirectory,
):
    first_media = httpserver.url_for("/first.mp3")
    second_media = httpserver.url_for("/second.mp3")
    httpserver.expect_request("/feed.xml").respond_with_data(
        build_rss_page(
            "First", first_media, "Fri, 04 Sep 2026 10:00:00 +0000", "/redirect.xml"
        ),
        content_type="application/rss+xml",
    )
    httpserver.expect_request("/redirect.xml").respond_with_data(
        "redirect", status=302, headers={"Location": "/actual-page2.xml"}
    )
    httpserver.expect_request("/actual-page2.xml").respond_with_data(
        build_rss_page("Second", second_media, "Thu, 03 Sep 2026 10:00:00 +0000"),
        content_type="application/rss+xml",
    )
    httpserver.expect_request("/first.mp3").respond_with_data("first audio")
    httpserver.expect_request("/second.mp3").respond_with_data("second audio")

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
    podcast_directory.is_containing_only(["first.mp3", "second.mp3"])
