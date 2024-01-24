import datetime
import json
import pytest
import random
import subprocess
import sys
from e2e.random import generate_random_sentence, generate_random_mp3_file
from feedgen.feed import FeedGenerator
from pathlib import Path
from pytest_httpserver import HTTPServer
from typing import Dict, List


class FeedBuilder:
    FEED_RSS_FILE_NAME = "/rss_feed.xml"

    def __init__(self, httpserver: HTTPServer) -> None:
        self.metadata = []
        self.httpserver = httpserver

    def add_entry(
        self,
        file_name: str = None,
        published_date: datetime = None,
        title: str = None,
        description: str = None,
    ):
        if file_name == None:
            file_name = generate_random_mp3_file()

        if title == None:
            title = generate_random_sentence(4)

        if description == None:
            description = generate_random_sentence(6)

        self.metadata.append((file_name, title, description, published_date))

        return self

    def add_random_entries(self, n: int = None):
        for _ in range(n or random.randint(4, 7)):
            self.add_entry()

        return self

    def __fill_up_dates(self):
        result = []
        previous = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            days=random.randrange(3, 5)
        )

        while self.metadata:
            metadatum = self.metadata.pop()
            previous -= datetime.timedelta(days=random.randrange(2, 6))
            result.append((metadatum[0], metadatum[1], metadatum[2], previous))

        self.metadata = reversed(result)

    def __build_rss(self):
        fg = FeedGenerator()
        fg.title("Some Testfeed")
        fg.author({"name": "John Doe", "email": "john@example.de"})
        fg.subtitle("This is a cool feed!")
        fg.link(href="http://example.com", rel="alternate")

        for file_name, title, description, published_date in self.metadata:
            self.httpserver.expect_request("/" + file_name).respond_with_data(
                "mp3_content"
            )

            fe = fg.add_entry()
            fe.title(title)
            fe.description(description)
            fe.enclosure(self.httpserver.url_for(file_name), 0, "audio/mpeg")
            fe.published(published_date)

        self.httpserver.expect_request(self.FEED_RSS_FILE_NAME).respond_with_data(
            fg.rss_str()
        )

    def get_feed_url(self) -> str:
        self.__fill_up_dates()
        self.__build_rss()

        return self.httpserver.url_for(self.FEED_RSS_FILE_NAME)


class PodcastDirectory:
    def __init__(self, download_destination_directory: Path) -> None:
        self.download_destination_directory = download_destination_directory

    def add_file(self, file_name: str) -> None:
        file_path = self.download_destination_directory / file_name.lower()
        file_path.write_text(file_name + " content")

    def is_containing_only(self, expected_files_list: List[str]) -> None:
        files_in_destination_directory = set(
            self.download_destination_directory.iterdir()
        )
        expected_unique_files = set(expected_files_list)

        if len(expected_unique_files) > 0:
            assert len(expected_unique_files) == len(
                files_in_destination_directory
            ), f"The expected_files_list contain duplication"
        assert (
            len(files_in_destination_directory & expected_unique_files) == 0
        ), f"The files in the podcast directory is different than expected"

    def path(self):
        return str(self.download_destination_directory)


@pytest.fixture()
def download_destination_directory(tmp_path) -> Path:
    feed_destination_path = tmp_path / "destination"
    feed_destination_path.mkdir()

    yield feed_destination_path


@pytest.fixture()
def feed(httpserver):
    yield FeedBuilder(httpserver)


@pytest.fixture()
def podcast_directory(download_destination_directory):
    yield PodcastDirectory(download_destination_directory)


@pytest.fixture
def use_config():
    def internal(config_object: Dict):
        config_file_name.write_text(json.dumps(config_object))

    home_directory = Path.home()
    config_file_name = home_directory / ".podcast_downloader_config.json"
    backup_config_file_name = (
        home_directory / ".safe_copy_podcast_downloader_config.json"
    )

    if config_file_name.exists():
        config_file_name.rename(backup_config_file_name)

    yield internal

    if backup_config_file_name.exists():
        config_file_name.unlink()
        backup_config_file_name.rename(config_file_name)


def run_podcast_downloader():
    subprocess.check_call([sys.executable, "-m", "podcast_downloader"])
