import os
import tempfile
import urllib.request
from typing import Dict, Optional
from urllib.parse import urlsplit


COVER_FILE_NAME = "cover"
COVER_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif")
COVER_DOWNLOAD_CHUNK_SIZE = 64 * 1024
COVER_TIMEOUT_SECONDS = 30
MAX_COVER_BYTES = 20 * 1024 * 1024
CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/pjpeg": ".jpg",
    "image/png": ".png",
    "image/x-png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/avif": ".avif",
}


def _http_origin(url: str):
    """Return an HTTP(S) origin without accepting embedded credentials."""
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


class _CoverRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Keep feed headers only while the cover remains on the same origin."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None and _http_origin(req.full_url) != _http_origin(newurl):
            for key in list(redirected.headers):
                redirected.remove_header(key)
            for key in list(redirected.unredirected_hdrs):
                redirected.remove_header(key)
            redirected.add_header("User-Agent", "podcast-downloader")
        return redirected


def _open_cover_request(request):
    opener = urllib.request.build_opener(_CoverRedirectHandler())
    return opener.open(request, timeout=COVER_TIMEOUT_SECONDS)


def _cover_request_headers(
    feed_url: Optional[str], cover_url: str, headers: Dict[str, str]
) -> Dict[str, str]:
    cover_origin = _http_origin(cover_url)
    if cover_origin is None:
        raise ValueError("Unsupported or malformed podcast cover URL")

    if feed_url and _http_origin(feed_url) == cover_origin:
        return headers
    # External artwork CDNs may be used, but must not see feed credentials.
    return {"User-Agent": "podcast-downloader"}


def get_podcast_cover_url(feed) -> Optional[str]:
    image = feed.feed.get("image", {})
    return image.get("href") if image else None


def get_podcast_cover_extension(
    image_url: str, content_type: Optional[str] = None
) -> Optional[str]:
    extension = os.path.splitext(urlsplit(image_url).path)[1].lower()
    if extension in COVER_EXTENSIONS:
        return extension

    if content_type:
        return CONTENT_TYPE_EXTENSIONS.get(content_type.split(";", 1)[0].strip().lower())

    return None


def find_existing_podcast_cover(path: str) -> Optional[str]:
    prefix = COVER_FILE_NAME + "."

    for file_name in os.listdir(path):
        if not file_name.startswith(prefix) or file_name.endswith(".part"):
            continue

        cover_path = os.path.join(path, file_name)
        if os.path.isfile(cover_path):
            return cover_path

    return None


def download_podcast_cover(
    headers: Dict[str, str],
    path: str,
    feed,
    feed_url: Optional[str] = None,
) -> Optional[str]:
    existing_cover = find_existing_podcast_cover(path)
    if existing_cover:
        return None

    image_url = get_podcast_cover_url(feed)
    if not image_url:
        return None

    request = urllib.request.Request(
        image_url,
        headers=_cover_request_headers(feed_url, image_url, headers),
    )

    with _open_cover_request(request) as response:
        content_type = response.headers.get("Content-Type")
        extension = get_podcast_cover_extension(image_url, content_type)
        if not extension:
            return None

        declared_size = response.headers.get("Content-Length")
        if declared_size is not None and str(declared_size).isdigit():
            if int(declared_size) > MAX_COVER_BYTES:
                raise ValueError("Podcast cover exceeds the %d-byte limit" % MAX_COVER_BYTES)

        cover_path = os.path.join(path, COVER_FILE_NAME + extension)
        temporary_cover_path = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=path,
                prefix=".podcast-cover-",
                suffix=".part",
                delete=False,
            ) as cover_file:
                temporary_cover_path = cover_file.name
                bytes_written = 0

                while True:
                    chunk = response.read(COVER_DOWNLOAD_CHUNK_SIZE)
                    if not chunk:
                        break
                    bytes_written += len(chunk)
                    if bytes_written > MAX_COVER_BYTES:
                        raise ValueError(
                            "Podcast cover exceeds the %d-byte limit" % MAX_COVER_BYTES
                        )
                    cover_file.write(chunk)

                if bytes_written == 0:
                    raise IOError("Empty podcast cover response")
                if (
                    declared_size is not None
                    and str(declared_size).isdigit()
                    and bytes_written != int(declared_size)
                ):
                    raise IOError(
                        "Incomplete podcast cover: received %d of %s bytes"
                        % (bytes_written, declared_size)
                    )

            os.replace(temporary_cover_path, cover_path)
            temporary_cover_path = None
        finally:
            if temporary_cover_path is not None:
                try:
                    os.remove(temporary_cover_path)
                except FileNotFoundError:
                    pass

    return cover_path
