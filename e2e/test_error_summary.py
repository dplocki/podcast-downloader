import re
from typing import Callable, Dict

from pytest_httpserver import HTTPServer

from e2e.fixures import (
    PodcastDirectory,
    PodcastDownloaderRunner,
    download_destination_directory,
    podcast_directory,
    podcast_downloader,
    use_config,
)


def test_failed_download_is_repeated_in_final_error_summary(
    httpserver: HTTPServer,
    use_config: Callable[[Dict], None],
    podcast_downloader: PodcastDownloaderRunner,
    podcast_directory: PodcastDirectory,
):
    file_name = "broken.mp3"
    audio_url = httpserver.url_for("/" + file_name)
    feed_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Error summary podcast</title>
    <item>
      <title>Broken episode</title>
      <pubDate>Fri, 04 Sep 2026 10:00:00 +0000</pubDate>
      <enclosure url="{audio_url}" length="4" type="audio/mpeg"/>
    </item>
  </channel>
</rss>
"""

    httpserver.expect_request("/feed.xml").respond_with_data(
        feed_xml, content_type="application/rss+xml"
    )
    httpserver.expect_request("/" + file_name).respond_with_data("boom", status=500)

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

    runner = podcast_downloader.run()
    output = runner.get_output()

    plain_output = [
        re.sub(r"\x1b\[[0-9;]*m", "", line) for line in output
    ]
    assert any(
        "Finished with 1 recoverable error:" in line for line in plain_output
    )
    assert sum("could not be saved to disk" in line for line in output) == 2
    assert podcast_directory.get_files_list() == set()
