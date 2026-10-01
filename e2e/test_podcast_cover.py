from pathlib import Path
from typing import Callable, Dict, List

from e2e.fixures import (
    PodcastDirectory,
    PodcastDownloaderRunner,
    download_destination_directory,
    podcast_directory,
    podcast_downloader,
    use_config,
)


def build_feed(cover_markup: str) -> str:
    return f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<rss xmlns:itunes=\"http://www.itunes.com/dtds/podcast-1.0.dtd\" version=\"2.0\">
  <channel>
    <title>Cover Test</title>
    <link>https://example.com</link>
    <description>Cover test feed</description>
    {cover_markup}
  </channel>
</rss>
"""


def test_podcast_cover_is_disabled_by_default(
    httpserver,
    use_config: Callable[[Dict], None],
    podcast_downloader: Callable[[List[str]], PodcastDownloaderRunner],
    podcast_directory: PodcastDirectory,
):
    cover_url = httpserver.url_for("/cover.jpg")
    httpserver.expect_request("/feed.xml").respond_with_data(
        build_feed(f"<image><url>{cover_url}</url></image>"),
        content_type="application/rss+xml",
    )

    use_config(
        {
            "podcasts": [
                {
                    "path": podcast_directory.path(),
                    "rss_link": httpserver.url_for("/feed.xml"),
                }
            ]
        }
    )

    podcast_downloader.run()

    requested_paths = [request.path for request, _ in httpserver.log]
    assert requested_paths == ["/feed.xml"]
    podcast_directory.is_containing_only([])


def test_rss_podcast_cover_is_downloaded_when_enabled(
    httpserver,
    use_config: Callable[[Dict], None],
    podcast_downloader: Callable[[List[str]], PodcastDownloaderRunner],
    podcast_directory: PodcastDirectory,
):
    cover_url = httpserver.url_for("/cover.jpg?size=1500")
    httpserver.expect_request("/feed.xml").respond_with_data(
        build_feed(f"<image><url>{cover_url}</url></image>"),
        content_type="application/rss+xml",
    )
    httpserver.expect_request("/cover.jpg", query_string="size=1500").respond_with_data(
        b"rss-cover", content_type="image/jpeg"
    )

    use_config(
        {
            "download_podcast_cover": True,
            "podcasts": [
                {
                    "path": podcast_directory.path(),
                    "rss_link": httpserver.url_for("/feed.xml"),
                }
            ],
        }
    )

    podcast_downloader.run()

    cover_path = Path(podcast_directory.path()) / "cover.jpg"
    assert cover_path.read_bytes() == b"rss-cover"
    podcast_directory.is_containing_only(["cover.jpg"])


def test_itunes_podcast_cover_uses_content_type_and_podcast_headers(
    httpserver,
    use_config: Callable[[Dict], None],
    podcast_downloader: Callable[[List[str]], PodcastDownloaderRunner],
    podcast_directory: PodcastDirectory,
):
    cover_url = httpserver.url_for("/artwork")
    httpserver.expect_request("/feed.xml").respond_with_data(
        build_feed(f'<itunes:image href="{cover_url}" />'),
        content_type="application/rss+xml",
    )
    httpserver.expect_request(
        "/artwork", headers={"X-Cover-Test": "enabled"}
    ).respond_with_data(b"itunes-cover", content_type="image/png")

    use_config(
        {
            "podcasts": [
                {
                    "path": podcast_directory.path(),
                    "rss_link": httpserver.url_for("/feed.xml"),
                    "download_podcast_cover": True,
                    "http_headers": {"X-Cover-Test": "enabled"},
                }
            ]
        }
    )

    podcast_downloader.run()

    cover_path = Path(podcast_directory.path()) / "cover.png"
    assert cover_path.read_bytes() == b"itunes-cover"
    podcast_directory.is_containing_only(["cover.png"])
