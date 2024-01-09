import os
import subprocess
import sys
import pytest


@pytest.fixture()
def secure_config_file():
    home_directory = os.path.expanduser("~")
    config_file_name = os.path.join(home_directory, ".podcast_downloader_config.json")
    backup_config_file_name = os.path.join(home_directory, ".safe_copy_podcast_downloader_config.json")

    if os.path.exists(config_file_name):
        os.rename(config_file_name, backup_config_file_name)

    yield config_file_name

    if os.path.exists(backup_config_file_name):
        os.remove(config_file_name)
        os.rename(backup_config_file_name, config_file_name)


def build_server():
    pass


def build_config(config_path):
    with open(config_path, 'w') as file:
        file.write('''{
        }''')


def run_podcast_downloader():
    subprocess.check_call([sys.executable, "-m", "podcast_downloader"])


def check_the_download_directory():
    pass


def test_answer(secure_config_file):
    build_server()
    build_config(secure_config_file)

    run_podcast_downloader()

    check_the_download_directory()
