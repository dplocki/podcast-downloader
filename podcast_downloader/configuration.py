from typing import List, Tuple

CONFIG_IF_DIRECTORY_EMPTY = "if_directory_empty"
CONFIG_DOWNLOADS_LIMIT = "downloads_limit"
CONFIG_PODCAST_EXTENSIONS = "podcast_extensions"

CONFIG_PODCASTS = "podcasts"
CONFIG_PODCASTS_NAME = "name"
CONFIG_PODCASTS_PATH = "path"
CONFIG_PODCASTS_RSS_LINK = "rss_link"
CONFIG_PODCASTS_REQUIRE_DATE = "require_date"
CONFIG_PODCASTS_DISABLE = "disable"


def configuration_verification(config: dict) -> Tuple[bool, List[str]]:
    for podcast in config[CONFIG_PODCASTS]:
        if not CONFIG_PODCASTS_NAME in podcast:
            return False, "Name is missing for one of the podcast"

        if not CONFIG_PODCASTS_PATH in podcast:
            return (
                False,
                f"There is no path for podcast {podcast[CONFIG_PODCASTS_NAME]}",
            )

        if not CONFIG_PODCASTS_RSS_LINK in podcast:
            return (
                False,
                f"There is no RSS link for podcast {podcast[CONFIG_PODCASTS_NAME]}",
            )

    return True, None
