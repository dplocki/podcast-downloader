from functools import partial
from typing import List, Tuple, Union
from datetime import datetime, timedelta
import re
import time

SECONDS_IN_DAY = 24 * 60 * 60

CONFIG_IF_DIRECTORY_EMPTY = "if_directory_empty"
CONFIG_DOWNLOADS_LIMIT = "downloads_limit"
CONFIG_FILE_NAME_TEMPLATE = "file_name_template"
CONFIG_PODCAST_EXTENSIONS = "podcast_extensions"
CONFIG_HTTP_HEADER = "http_headers"
CONFIG_FILL_UP_GAPS = "fill_up_gaps"
CONFIG_DOWNLOAD_DELAY = "download_delay"
CONFIG_LAST_RUN_MARK_PATH = "last_run_mark_file_path"

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

MIN_MONTH_DAY = 1
MAX_MONTH_DAY = 28


def configuration_verification(config: dict) -> Tuple[bool, List[str]]:
    for podcast in config[CONFIG_PODCASTS]:
        podcast_name = podcast.get(CONFIG_PODCASTS_NAME, "<unnamed>")

        if CONFIG_PODCASTS_PATH not in podcast:
            return (
                False,
                f"There is no path for podcast {podcast_name}",
            )

        if CONFIG_PODCASTS_RSS_LINK not in podcast:
            return (
                False,
                f"There is no RSS link for podcast {podcast_name}",
            )

    return True, None


def get_n_age_date(day_number: int, from_date: time.struct_time) -> time.struct_time:
    return time.localtime(time.mktime(from_date) - day_number * SECONDS_IN_DAY)


def validate_month_day(day: int) -> int:
    if day < MIN_MONTH_DAY or day > MAX_MONTH_DAY:
        raise ValueError(
            f"Day number must be between {MIN_MONTH_DAY} and {MAX_MONTH_DAY}"
        )
    return day


def get_label_to_date(day_label: Union[str, int]) -> partial:
    if day_label in WEEK_DAYS:
        return partial(get_week_day, day_label)

    return partial(get_nth_day, validate_month_day(int(day_label)))


def get_week_day(weekday_label: str, from_date: time.struct_time) -> time.struct_time:
    from_datetime = datetime(*from_date[:6])
    weekday_from_date = from_datetime.weekday()
    weekday_label_index = WEEK_DAYS.index(weekday_label)
    result_datetime = from_datetime - timedelta(
        6
        if weekday_from_date == weekday_label_index
        else weekday_from_date - weekday_label_index - 1
    )

    return result_datetime.timetuple()


def get_nth_day(day: int, from_date: time.struct_time) -> time.struct_time:
    day = validate_month_day(day)
    from_datetime = datetime(*from_date[:6])

    if from_datetime.day > day:
        selected_day = from_datetime.replace(day=day)
    else:
        previous_month_last_day = from_datetime.replace(day=1) - timedelta(days=1)
        selected_day = previous_month_last_day.replace(day=day)

    return (selected_day + timedelta(days=1)).timetuple()


def parse_day_label(raw_label: str) -> Union[str, int]:
    if raw_label.isnumeric():
        return validate_month_day(int(raw_label))

    ordinal_match = re.fullmatch(r"(\d+)(st|nd|rd|th)", raw_label)
    if ordinal_match:
        return validate_month_day(int(ordinal_match.group(1)))

    capitalize_raw_label = raw_label.capitalize()
    if capitalize_raw_label in WEEK_DAYS:
        return capitalize_raw_label

    short_weekdays = ("Mon", "Tues", "Weds", "Thurs", "Fri", "Sat", "Sun")
    if capitalize_raw_label in short_weekdays:
        return WEEK_DAYS[short_weekdays.index(capitalize_raw_label)]

    raise Exception(f"Cannot read weekday name '{raw_label}'")
