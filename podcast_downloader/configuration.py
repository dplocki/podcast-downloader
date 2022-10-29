from calendar import weekday
from typing import List, Tuple
import time

SECONDS_IN_DAY = 24 * 60 * 60

CONFIG_IF_DIRECTORY_EMPTY = "if_directory_empty"
CONFIG_DOWNLOADS_LIMIT = "downloads_limit"
CONFIG_PODCAST_EXTENSIONS = "podcast_extensions"

CONFIG_PODCASTS = "podcasts"
CONFIG_PODCASTS_NAME = "name"
CONFIG_PODCASTS_PATH = "path"
CONFIG_PODCASTS_RSS_LINK = "rss_link"
CONFIG_PODCASTS_REQUIRE_DATE = "require_date"
CONFIG_PODCASTS_DISABLE = "disable"

WEEK_DAYS = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)


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


def get_n_age_date(day_number: int, from_date: time.struct_time) -> time.struct_time:
    return time.localtime(time.mktime(from_date) - day_number * SECONDS_IN_DAY)


def get_label_to_date(day_label: str) -> time.struct_time:
    if day_label.to_lower() in WEEK_DAYS:
        return get_week_day
    else:
        return get_nth_day


def get_week_day(weekday_label: str, from_date: time.struct_time) -> time.struct_time:
    pass


def get_nth_day(day: int, from_date: time.struct_time) -> time.struct_time:
    pass


def parse_day_label(raw_label: str) -> str:
    capitalize_raw_label = raw_label.capitalize()

    if capitalize_raw_label in WEEK_DAYS:
        return capitalize_raw_label

    short_weekdays = ("Mon", "Tues", "Weds", "Thurs", "Fri", "Sat", "Sun")
    index = short_weekdays.index(capitalize_raw_label)
    if index >= 0:
        return WEEK_DAYS[index]

    raise Exception(f"Cannot read weekday name '{raw_label}'")
