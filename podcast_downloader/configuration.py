from functools import partial
from typing import List, Tuple, Union
from datetime import datetime, timedelta
import time

SECONDS_IN_DAY = 24 * 60 * 60

CONFIG_IF_DIRECTORY_EMPTY = "if_directory_empty"
CONFIG_DOWNLOADS_LIMIT = "downloads_limit"
CONFIG_FILE_NAME_TEMPLATE = "file_name_template"
CONFIG_PODCAST_EXTENSIONS = "podcast_extensions"
CONFIG_HTTP_HEADER = "http_headers"
CONFIG_FILL_UP_GAPS = "fill_up_gaps"

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


def get_label_to_date(day_label: Union[str, int]) -> partial:
    if day_label in WEEK_DAYS:
        return partial(get_week_day, day_label)

    return partial(get_nth_day, int(day_label))


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
    from_datetime = datetime(*from_date[:6])

    day_difference = from_date[2] - day
    datetime_result = (
        from_datetime - timedelta(days=day_difference - 1)
        if day_difference > 0
        else (from_datetime.replace(day=1) - timedelta(days=28)).replace(day=day + 1)
    )

    return datetime_result.timetuple()


def parse_day_label(raw_label: str) -> Union[str, int]:
    if raw_label.isnumeric():
        return int(raw_label)

    if raw_label == "1st":
        return 1

    if raw_label == "2nd":
        return 2

    if raw_label == "3rd":
        return 3

    if raw_label[-2:] == "th":
        return int(raw_label[:-2])

    capitalize_raw_label = raw_label.capitalize()
    if capitalize_raw_label in WEEK_DAYS:
        return capitalize_raw_label

    short_weekdays = ("Mon", "Tues", "Weds", "Thurs", "Fri", "Sat", "Sun")
    if capitalize_raw_label in short_weekdays:
        return WEEK_DAYS[short_weekdays.index(capitalize_raw_label)]

    raise Exception(f"Cannot read weekday name '{raw_label}'")
