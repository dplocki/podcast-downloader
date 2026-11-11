import logging
import re
import urllib.request
import time
from dataclasses import dataclass
from functools import partial
from itertools import takewhile, islice
from typing import Callable, Generator, Iterator, List, Optional
import unicodedata
import feedparser
from urllib.parse import urljoin, urlsplit, unquote


FILE_NAME_CHARACTER_LIMIT = 255
DEFAULT_MAX_RSS_PAGES = 1000
PAGINATION_TIMEOUT_SECONDS = 30


class RSSPaginationError(RuntimeError):
    """An RSS pagination run could not be completed safely."""


class RSSPaginationLimitExceeded(RSSPaginationError):
    """The configured RSS page limit was reached before pagination ended."""


@dataclass
class RSSEntity:
    published_date: time.struct_time
    title: str
    type: str
    link: str


def link_to_file_name_with_extension(link: str) -> str:
    path = urlsplit(link).path
    return unquote(path).rsplit("/")[-1].replace("\\", "").lower()


def link_to_file_name(link: str) -> str:
    link = link_to_file_name_with_extension(link)
    if link.find(".") >= 0:
        link = link.rpartition(".")[0]

    return link


def link_to_extension(link: str) -> str:
    link = link_to_file_name_with_extension(link)
    if link.find(".") >= 0:
        return link.rpartition(".")[-1]

    return ""


def str_to_filename(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"[\u0000-\u001F\u007F\*/:<>\"\?\\\|]", " ", value)

    return value.strip()


def file_template_to_file_name(name_template: str, entity: RSSEntity) -> str:
    publish_date_template = "%publish_date:"
    publish_date_template_len = len(publish_date_template)

    while "%publish_date:" in name_template:
        start_token = name_template.index("%publish_date:")
        token = name_template[
            start_token : name_template.index(
                "%", start_token + publish_date_template_len
            )
            + 1
        ]
        result = time.strftime(
            token[publish_date_template_len:-1].replace("$", "%"), entity.published_date
        )
        name_template = name_template.replace(token, result)

    return (
        name_template.replace("%file_name%", link_to_file_name(entity.link))
        .replace("%publish_date%", time.strftime("%Y%m%d", entity.published_date))
        .replace("%file_extension%", link_to_extension(entity.link))
        .replace("%title%", str_to_filename(entity.title))
        .strip()
    )


def limit_file_name(maximum_length: int, file_name: str) -> str:
    last_dot_index = file_name.rfind(".")
    if last_dot_index == -1:
        return file_name[:maximum_length]

    file_name_length = len(file_name)
    if file_name_length <= maximum_length:
        return file_name

    return (
        file_name[: maximum_length - file_name_length + last_dot_index]
        + file_name[last_dot_index:]
    )


def get_next_feed_link(feed: feedparser.FeedParserDict) -> Optional[str]:
    for link in feed.get("feed", {}).get("links", []):
        if str(link.get("rel", "")).lower() == "next" and link.get("href"):
            return link["href"]

    return None


def _http_origin(url: str):
    """Return the normalized scheme, hostname and port for a safe HTTP URL."""
    try:
        parts = urlsplit(url)
        if (
            parts.scheme.lower() not in ("http", "https")
            or not parts.hostname
            or parts.username is not None
            or parts.password is not None
        ):
            return None
        port = parts.port or (443 if parts.scheme.lower() == "https" else 80)
        if not 1 <= port <= 65535:
            return None
    except ValueError:
        return None

    return parts.scheme.lower(), parts.hostname.lower().rstrip("."), port


class _SameOriginRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, allowed_origin):
        self.allowed_origin = allowed_origin

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if _http_origin(newurl) != self.allowed_origin:
            raise RSSPaginationError(
                "Blocked RSS pagination redirect to a different origin"
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _fetch_paginated_feed(rss_link: str, allowed_origin):
    """Fetch an untrusted next page without making cross-origin requests."""
    if _http_origin(rss_link) != allowed_origin:
        raise RSSPaginationError(
            "Blocked RSS pagination link to a different origin"
        )

    request = urllib.request.Request(
        rss_link, headers={"User-Agent": "podcast-downloader"}
    )
    opener = urllib.request.build_opener(
        _SameOriginRedirectHandler(allowed_origin)
    )

    try:
        with opener.open(request, timeout=PAGINATION_TIMEOUT_SECONDS) as response:
            final_url = response.geturl()
            if _http_origin(final_url) != allowed_origin:
                raise RSSPaginationError(
                    "Blocked RSS pagination response from a different origin"
                )
            headers = {
                key.lower(): value for key, value in response.headers.items()
            }
            headers.setdefault("content-location", final_url)
            return feedparser.parse(response, response_headers=headers)
    except RSSPaginationError:
        raise
    except Exception as error:
        raise RSSPaginationError(
            "Could not load an RSS pagination page: %s" % error
        ) from error


def load_feed(
    rss_link: str, max_pages: int = DEFAULT_MAX_RSS_PAGES
) -> feedparser.FeedParserDict:
    if type(max_pages) is not int or max_pages < 1:
        raise ValueError("max_rss_pages must be a positive integer")

    feed = feedparser.parse(rss_link)
    current_feed = feed
    current_link = rss_link
    visited_links = {rss_link}
    allowed_origin = _http_origin(feed.get("href") or rss_link)

    while True:
        next_link = get_next_feed_link(current_feed)
        if not next_link:
            break

        next_link = urljoin(current_feed.get("href") or current_link, next_link)
        if allowed_origin is None or _http_origin(next_link) != allowed_origin:
            raise RSSPaginationError(
                "Blocked RSS pagination link outside the initial feed origin"
            )
        if next_link in visited_links:
            break

        if len(visited_links) >= max_pages:
            raise RSSPaginationLimitExceeded(
                "RSS pagination for %s exceeded max_rss_pages=%d; "
                "increase the limit to load the complete feed" % (rss_link, max_pages)
            )

        visited_links.add(next_link)
        next_feed = _fetch_paginated_feed(next_link, allowed_origin)
        if next_feed.get("bozo", False) and not next_feed.entries:
            raise RSSPaginationError(
                "Could not load RSS pagination page %s: %s"
                % (next_link, next_feed.get("bozo_exception", "invalid feed"))
            )

        feed.entries.extend(next_feed.entries)
        current_feed = next_feed
        current_link = next_link

    return feed

def get_feed_title_from_feed(feedParser: feedparser.FeedParserDict) -> str:
    return feedParser.feed.title


def get_raw_rss_entries_from_feed(
    feedParser: feedparser.FeedParserDict,
) -> Generator[feedparser.FeedParserDict, None, None]:
    yield from feedParser.entries


def flatten_rss_links_data(
    source: Generator[feedparser.FeedParserDict, None, None]
) -> Generator[RSSEntity, None, None]:
    return (
        RSSEntity(
            rss_entry.published_parsed,
            rss_entry.title,
            link.type,
            link.get("href", None),
        )
        for rss_entry in source
        for link in rss_entry.links
    )


def build_only_allowed_filter_for_link_data(
    allowed_types: List[str],
) -> Callable[[RSSEntity], bool]:
    return lambda link_data: link_data.type in allowed_types


def build_only_new_entities(
    to_name_function: Callable[[RSSEntity], str]
) -> Callable[[str, List[RSSEntity]], Generator[RSSEntity, None, None]]:
    return lambda from_file, raw_rss_entries: takewhile(
        lambda rss_entity: to_name_function(rss_entity) != from_file, raw_rss_entries
    )


def only_last_n_entities(
    n: int, raw_rss_entries: Iterator[RSSEntity]
) -> Iterator[RSSEntity]:
    return islice(raw_rss_entries, n)


def is_entity_newer(from_date: time.struct_time, entity: RSSEntity) -> bool:
    return entity.published_date[:3] >= from_date[:3]


def only_entities_from_date(from_date: time.struct_time) -> Callable[[RSSEntity], bool]:
    return partial(filter, partial(is_entity_newer, from_date))
