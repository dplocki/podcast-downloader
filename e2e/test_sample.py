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


class FeedBuilder():

    def __init__(self) -> None:
        self.fg = FeedGenerator()
        self.fg.title('Some Testfeed')
        self.fg.author( {'name':'John Doe','email':'john@example.de'} )
        self.fg.subtitle('This is a cool feed!')
        self.fg.link( href='http://example.com', rel='alternate' )


    def add_entry(self):
        fe = self.fg.add_entry()
        fe.id('http://lernfunk.de/media/654321/1/file.mp3')
        fe.title('The First Episode')
        fe.description('Enjoy our first episode.')
        fe.enclosure('http://lernfunk.de/media/654321/1/file.mp3', 0, 'audio/mpeg')
        fe.published(datetime.datetime(2014, 7, 10, 2, 43, 55, 230107, tzinfo=datetime.timezone.utc))

        return self


    def build(self):
        rss_file_name = 'podcast.xml'
        self.fg.rss_file(rss_file_name)

        return rss_file_name


def build_config(config_path, config_object):
    with open(config_path, "w") as file:
        file.write(json.dumps(config_object))


def run_podcast_downloader():
    subprocess.check_call([sys.executable, "-m", "podcast_downloader"])


def check_the_download_directory():
    pass


def test_answer(secure_config_file, create_temporary_directory):
    rss_file = FeedBuilder().add_entry().add_entry().build()

    build_config(
        secure_config_file,
        {
            "podcasts": [
                {
                    "name": "test",
                    "path": create_temporary_directory,
                    "rss_link": rss_file,
                }
            ]
        },
    )

    run_podcast_downloader()

    check_the_download_directory()
