import os
import urllib.request
from typing import Dict, Optional
from urllib.parse import urlsplit


COVER_FILE_NAME = "cover"
COVER_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif")
COVER_DOWNLOAD_CHUNK_SIZE = 64 * 1024
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


def download_podcast_cover(headers: Dict[str, str], path: str, feed) -> Optional[str]:
    existing_cover = find_existing_podcast_cover(path)
    if existing_cover:
        return None

    image_url = get_podcast_cover_url(feed)
    if not image_url:
        return None

    request = urllib.request.Request(image_url, headers=headers)
    with urllib.request.urlopen(request) as response:
        content_type = response.headers.get("Content-Type")
        extension = get_podcast_cover_extension(image_url, content_type)
        if not extension:
            return None

        cover_path = os.path.join(path, COVER_FILE_NAME + extension)
        temporary_cover_path = cover_path + ".part"

        try:
            with open(temporary_cover_path, "wb") as cover_file:
                while True:
                    chunk = response.read(COVER_DOWNLOAD_CHUNK_SIZE)
                    if not chunk:
                        break
                    cover_file.write(chunk)
            os.replace(temporary_cover_path, cover_path)
        except Exception:
            try:
                os.remove(temporary_cover_path)
            except FileNotFoundError:
                pass
            raise

    return cover_path
