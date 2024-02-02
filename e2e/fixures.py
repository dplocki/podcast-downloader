import datetime
import json
import pytest
import random
import subprocess
import sys
from e2e.random import (
    generate_random_sentence,
    generate_random_mp3_file,
    generate_random_string,
)
from feedgen.feed import FeedGenerator
from pathlib import Path
from pytest_httpserver import HTTPServer
from typing import Dict, Generator, Iterable, List, Set


def print_set_content(content: Set):
    return ", ".join(sorted(content))


class FeedBuilder:
    FEED_RSS_FILE_NAME = "/rss_feed.xml"
    PUBLISHED_DATE_INDEX = 3

    def __init__(self, httpserver: HTTPServer, url_prefix: str = None) -> None:
        self.metadata = []
        self.httpserver = httpserver
        self.url_prefix = url_prefix or ""
        self.headers = None

    def set_request_headers(self, headers):
        self.headers = headers

    def add_entry(
        self,
        file_name: str = None,
        published_date: datetime = None,
        title: str = None,
        description: str = None,
        file_type: str = None,
    ):
        if file_name == None:
            file_name = generate_random_mp3_file()

        if title == None:
            title = generate_random_sentence(4)

        if description == None:
            description = generate_random_sentence(6)

        if file_type == None:
            file_type = "audio/mpeg"

        self.metadata.append((file_name, title, description, published_date, file_type))

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
            if metadatum[self.PUBLISHED_DATE_INDEX] != None:
                previous = metadatum[self.PUBLISHED_DATE_INDEX]
            else:
                previous -= datetime.timedelta(days=random.randrange(2, 6))

            result.append(
                (metadatum[0], metadatum[1], metadatum[2], previous, metadatum[4])
            )

        self.metadata = result[::-1]

    def __build_rss(self):
        fg = FeedGenerator()
        fg.title("Some Testfeed")
        fg.author({"name": "John Doe", "email": "john@example.de"})
        fg.subtitle("This is a cool feed!")
        fg.link(href="http://example.com", rel="alternate")

        for file_name, title, description, published_date, file_type in self.metadata:
            self.httpserver.expect_request(
                self.url_prefix + "/" + file_name, headers=self.headers
            ).respond_with_data("mp3_content")

            fe = fg.add_entry()
            fe.title(title)
            fe.description(description)
            fe.enclosure(
                self.httpserver.url_for(self.url_prefix + "/" + file_name), 0, file_type
            )
            fe.published(published_date)

        self.httpserver.expect_request(
            self.url_prefix + self.FEED_RSS_FILE_NAME
        ).respond_with_data(fg.rss_str())

    def get_feed_url(self) -> str:
        self.__fill_up_dates()
        self.__build_rss()

        return self.httpserver.url_for(self.url_prefix + self.FEED_RSS_FILE_NAME)


class PodcastDirectory:
    def __init__(self, download_destination_directory: Path) -> None:
        self.download_destination_directory = download_destination_directory

    def add_file(self, file_name: str) -> None:
        file_path = self.download_destination_directory / file_name.lower()
        file_path.write_text(file_name + " content")

    def is_containing_only(self, expected_files_list: List[str]) -> None:
        files_in_destination_directory = self.get_files_list()
        expected_unique_files = set(expected_files_list)

        if len(expected_unique_files) > 0:
            assert len(expected_unique_files) == len(
                expected_files_list
            ), f"The expected_files_list contain duplication"

            the_difference = files_in_destination_directory ^ expected_unique_files

            assert (
                len(the_difference) == 0
            ), f"The files in the podcast directory is different than expected.\nDirectory:  {print_set_content(files_in_destination_directory)}\nExpected:   {print_set_content(expected_unique_files)}\nDifference: {print_set_content(the_difference)}"
            return

        assert len(files_in_destination_directory) == 0

    def get_files_list(self) -> Iterable[str]:
        return set(file.name for file in self.download_destination_directory.iterdir())

    def path(self):
        return str(self.download_destination_directory)


class MultiplePodcastDirectory:
    def __init__(self, tmp_path: Path) -> None:
        self.tmp_path = tmp_path
        self.directories = {}

    def __get_directory(self, name) -> Path:
        if name not in self.directories:
            feed_destination_path = self.tmp_path / "destination"
            if not feed_destination_path.exists():
                feed_destination_path.mkdir()

            output_directory = feed_destination_path / name
            output_directory.mkdir()

            self.directories[name] = output_directory

        return self.directories[name]

    def get_first_directory(self) -> str:
        return str(self.__get_directory("first"))

    def get_second_directory(self) -> str:
        return str(self.__get_directory("second"))

    def get_first_directory_files(self) -> Generator[str, None, None]:
        return self.__get_directory("first").iterdir()

    def get_second_directory_files(self) -> Generator[str, None, None]:
        return self.__get_directory("second").iterdir()


class MultipleFeedBuilder:
    def __init__(self, httpserver) -> None:
        self.first_feed = FeedBuilder(httpserver, "/" + generate_random_string())
        self.second_feed = FeedBuilder(httpserver, "/" + generate_random_string())


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


@pytest.fixture()
def podcast_directory_manager(tmp_path):
    yield MultiplePodcastDirectory(tmp_path)


@pytest.fixture()
def feed_builder_manager(httpserver):
    return MultipleFeedBuilder(httpserver)


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
