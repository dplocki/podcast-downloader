from typing import Callable, Dict

from e2e.fixures import (
    FeedBuilder,
    PodcastDirectory,
    PodcastDownloaderRunner,
    download_destination_directory,  # noqa: F401 - required by podcast_directory
    feed,  # noqa: F401 - pytest fixture imported for discovery
    podcast_directory,  # noqa: F401 - pytest fixture imported for discovery
    podcast_downloader,  # noqa: F401 - pytest fixture imported for discovery
    use_config,  # noqa: F401 - pytest fixture imported for discovery
)


def test_configured_video_media_type_is_downloaded(
    feed: FeedBuilder,
    use_config: Callable[[Dict], None],
    podcast_downloader: PodcastDownloaderRunner,
    podcast_directory: PodcastDirectory,
):
    video_file = "episode.mp4"
    feed.add_entry(file_name=video_file, file_type="video/mp4")

    use_config(
        {
            "podcast_extensions": {".mp4": "video/mp4"},
            "podcasts": [
                {
                    "path": podcast_directory.path(),
                    "rss_link": feed.get_feed_url(),
                }
            ],
        }
    )

    podcast_downloader.run()

    podcast_directory.is_containing_only([video_file])
