import datetime
import os
import subprocess
import sys
import tempfile
import pytest
import json
from feedgen.feed import FeedGenerator


@pytest.fixture()
def secure_config_file():
    home_directory = os.path.expanduser("~")
    config_file_name = os.path.join(home_directory, ".podcast_downloader_config.json")
    backup_config_file_name = os.path.join(
        home_directory, ".safe_copy_podcast_downloader_config.json"
    )

    if os.path.exists(config_file_name):
        os.rename(config_file_name, backup_config_file_name)

    yield config_file_name

    if os.path.exists(backup_config_file_name):
        os.remove(config_file_name)
        os.rename(backup_config_file_name, config_file_name)


@pytest.fixture()
def create_temporary_directory():
    with tempfile.TemporaryDirectory() as tmp_dirname:
        yield tmp_dirname


@pytest.fixture()
def create_origin_feed_directory(create_temporary_directory):
    feed_source_path = os.path.join(create_temporary_directory, "feed_source")
    os.makedirs(feed_source_path)
    yield feed_source_path


@pytest.fixture()
def create_download_destination_directory(create_temporary_directory):
    feed_destination_path = os.path.join(create_temporary_directory, "destination")
    os.makedirs(feed_destination_path)
    yield feed_destination_path


class FeedBuilder:
    def __init__(self, feed_source) -> None:
        self.feed_source = feed_source
        self.fg = FeedGenerator()
        self.fg.title("Some Testfeed")
        self.fg.author({"name": "John Doe", "email": "john@example.de"})
        self.fg.subtitle("This is a cool feed!")
        self.fg.link(href="http://example.com", rel="alternate")

    def add_entry(self):
        fe = self.fg.add_entry()
        fe.id("http://lernfunk.de/media/654321/1/file.mp3")
        fe.title("The First Episode")
        fe.description("Enjoy our first episode.")
        fe.enclosure(f"file:///{self.feed_source}/file.mp3", 0, "audio/mpeg")
        fe.published(
            datetime.datetime(
                2014, 7, 10, 2, 43, 55, 230107, tzinfo=datetime.timezone.utc
            )
        )

        self.__add_file_in_source("file.mp3")

        return self

    def build(self):
        rss_file_name = "podcast.xml"
        self.fg.rss_file(rss_file_name)

        return rss_file_name

    def __add_file_in_source(self, file_name):
        path_to_file = os.path.join(self.feed_source, file_name)
        with open(path_to_file, "w") as file:
            file.write("test")


@pytest.fixture()
def feed_builder(create_origin_feed_directory):
    yield FeedBuilder(create_origin_feed_directory)


def build_config(config_path, config_object):
    with open(config_path, "w") as file:
        file.write(json.dumps(config_object))


def run_podcast_downloader():
    subprocess.check_call([sys.executable, "-m", "podcast_downloader"])


def check_the_download_directory():
    pass


def test_answer(
    secure_config_file, feed_builder, create_download_destination_directory
):
    rss_file = feed_builder.add_entry().add_entry().build()
    build_config(
        secure_config_file,
        {
            "podcasts": [
                {
                    "name": "test",
                    "path": create_download_destination_directory,
                    "rss_link": rss_file,
                }
            ]
        },
    )

    run_podcast_downloader()

    check_the_download_directory()
