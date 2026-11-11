from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
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


def other_host_url(url: str) -> str:
    parsed = urlsplit(url)
    alt_host = "127.0.0.1" if parsed.hostname == "localhost" else "localhost"
    return urlunsplit((
        parsed.scheme,
        "%s:%d" % (alt_host, parsed.port),
        parsed.path,
        parsed.query,
        parsed.fragment,
    ))


def test_external_cover_origin_does_not_receive_feed_authentication(
    httpserver,
    use_config: Callable[[Dict], None],
    podcast_downloader: Callable[[List[str]], PodcastDownloaderRunner],
    podcast_directory: PodcastDirectory,
):
    external_url = other_host_url(httpserver.url_for("/cdn-cover.jpg"))
    httpserver.expect_request("/feed.xml").respond_with_data(
        build_feed(f"<image><url>{external_url}</url></image>"),
        content_type="application/rss+xml",
    )
    httpserver.expect_request("/cdn-cover.jpg").respond_with_data(
        b"cover data", content_type="image/jpeg"
    )

    use_config({
        "download_podcast_cover": True,
        "http_headers": {"Authorization": "Bearer private-rss-token"},
        "podcasts": [{
            "path": podcast_directory.path(),
            "rss_link": httpserver.url_for("/feed.xml"),
        }],
    })

    podcast_downloader.run()

    cover_path = Path(podcast_directory.path()) / "cover.jpg"
    assert cover_path.read_bytes() == b"cover data"
    requests = [req for req, _ in httpserver.log if req.path == "/cdn-cover.jpg"]
    assert len(requests) == 1
    assert requests[0].headers.get("Authorization") is None


def test_cover_redirect_to_other_origin_drops_feed_authentication(
    httpserver,
    use_config: Callable[[Dict], None],
    podcast_downloader: Callable[[List[str]], PodcastDownloaderRunner],
    podcast_directory: PodcastDirectory,
):
    final_url = other_host_url(httpserver.url_for("/final-cover.jpg"))
    initial_url = httpserver.url_for("/cover-redirect.jpg")
    httpserver.expect_request("/feed.xml").respond_with_data(
        build_feed(f"<image><url>{initial_url}</url></image>"),
        content_type="application/rss+xml",
    )
    httpserver.expect_request("/cover-redirect.jpg").respond_with_data(
        "redirect", status=302, headers={"Location": final_url}
    )
    httpserver.expect_request("/final-cover.jpg").respond_with_data(
        b"cover after redirect", content_type="image/jpeg"
    )

    use_config({
        "download_podcast_cover": True,
        "http_headers": {"Authorization": "Bearer private-rss-token"},
        "podcasts": [{
            "path": podcast_directory.path(),
            "rss_link": httpserver.url_for("/feed.xml"),
        }],
    })

    podcast_downloader.run()

    cover_path = Path(podcast_directory.path()) / "cover.jpg"
    assert cover_path.read_bytes() == b"cover after redirect"
    first = [req for req, _ in httpserver.log if req.path == "/cover-redirect.jpg"]
    last = [req for req, _ in httpserver.log if req.path == "/final-cover.jpg"]
    assert len(first) == len(last) == 1
    assert first[0].headers.get("Authorization") == "Bearer private-rss-token"
    assert last[0].headers.get("Authorization") is None
    assert not list(Path(podcast_directory.path()).glob(".podcast-cover-*.part"))
