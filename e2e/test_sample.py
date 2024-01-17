import datetime
import os
import random
import string
import subprocess
import sys
import tempfile
from typing import Iterator
import pytest
import json
from feedgen.feed import FeedGenerator
from pathlib import Path


def generate_random_string(length: int) -> str:
    letters = string.ascii_letters
    random_string = "".join(random.choice(letters) for _ in range(length))
    return random_string


def generate_random_sentence(word_count: int) -> str:
    return (
        " ".join(
            generate_random_string(random.randrange(4, 7)) for _ in range(word_count)
        ).capitalize()
        + "."
    )


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
def temporary_directory():
    with tempfile.TemporaryDirectory() as tmp_dirname:
        yield tmp_dirname


@pytest.fixture()
def origin_feed_directory(tmp_path):
    feed_source_path = tmp_path / "feed_source"
    feed_source_path.mkdir()
    yield feed_source_path


@pytest.fixture()
def download_destination_directory(tmp_path) -> Path:
    feed_destination_path = tmp_path / "destination"
    feed_destination_path.mkdir()

    yield feed_destination_path


class FeedBuilder:
    def __init__(self, origin_feed_directory: Path) -> None:
        self.metadata = []
        self.origin_feed_directory = origin_feed_directory

    def add_entry(
        self,
        file_name: str = None,
        published_date: datetime = None,
        title: str = None,
        description: str = None,
    ):
        if file_name == None:
            file_name = generate_random_string(7) + ".mp3"

        if title == None:
            title = generate_random_sentence(4)

        if description == None:
            description = generate_random_sentence(6)

        self.metadata.append((file_name, title, description, published_date))

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

    def build(self):
        self.__fill_up_dates()

        fg = FeedGenerator()
        fg.title("Some Testfeed")
        fg.author({"name": "John Doe", "email": "john@example.de"})
        fg.subtitle("This is a cool feed!")
        fg.link(href="http://example.com", rel="alternate")

        for file_name, title, description, published_date in self.metadata:
            fe = fg.add_entry()
            fe.title(title)
            fe.description(description)
            fe.enclosure(
                f"file:///{self.origin_feed_directory}/{file_name}", 0, "audio/mpeg"
            )
            fe.published(published_date)

            self.__add_file_in_source(file_name)

        path_to_file = str(self.origin_feed_directory / "podcast.xml")
        fg.rss_file(path_to_file)

        return path_to_file

    def __add_file_in_source(self, file_name):
        path_to_file = os.path.join(self.origin_feed_directory, file_name)
        with open(path_to_file, "w") as file:
            file.write("test")


@pytest.fixture()
def feed_builder(origin_feed_directory):
    yield FeedBuilder(origin_feed_directory)


def build_config(config_path, config_object):
    with open(config_path, "w") as file:
        file.write(json.dumps(config_object))


def run_podcast_downloader():
    subprocess.check_call([sys.executable, "-m", "podcast_downloader"])


def check_the_download_directory(download_destination_directory: Path) -> Iterator[str]:
    return list(download_destination_directory.iterdir())


def test_answer(secure_config_file, feed_builder, download_destination_directory):
    feed_builder = feed_builder.add_entry().add_entry()
    build_config(
        secure_config_file,
        {
            "podcasts": [
                {
                    "name": "test",
                    "path": str(download_destination_directory),
                    "rss_link": feed_builder.build(),
                }
            ]
        },
    )

    run_podcast_downloader()

    check_the_download_directory(download_destination_directory)
