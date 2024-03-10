# Podcast Downloader

![GitHub](https://img.shields.io/github/license/dplocki/podcast-downloader)
![Build Status](https://img.shields.io/endpoint.svg?url=https%3A%2F%2Factions-badge.atrox.dev%2Fdplocki%2Fpodcast-downloader%2Fbadge%3Fref%3Dmaster&style=flat)
![PyPI](https://img.shields.io/pypi/v/podcast-downloader)
[![Downloads](https://img.shields.io/pypi/dm/podcast-downloader.svg)](https://pypi.python.org/pypi/podcast-downloader)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

The Python module for downloading files from given RSS feeds.
It is not using database of any sort. It require configuration file.

The script is analyzing the directory where it put the previously downloaded files.
It is compering the last added file with the rss feed, finding the missing ones, and downloading them.

As name suggested, the script is designed for podcasts. The files searched by default are `mp3`.

## Setup

### Installation from PyPI

```bash
pip install podcast_downloader
```

## Running the script

The script [require configuration file](#configuration) in order to work.
After installation, the script can be called as any Python module:

```bash
python -m podcast_downloader
```

### In action

Using the [example above](#example), the result will be:

```log
[2020-06-16 19:54:35] Loading configuration (from file: "~/.podcast_downloader_config.json")
[2020-06-16 19:54:35] Checking "The Skeptic Guide"
[2020-06-16 19:54:35] Last downloaded file "skepticast2020-06-13.mp3"
[2020-06-16 19:54:39] The Skeptic Guide: Nothing new
[2020-06-16 19:54:39] ------------------------------
[2020-06-16 19:54:39] Finished
```

## Configuration

### The configuration file

The configuration file is placed in home directory.

The name: `.podcast_downloader_config.json`. The file is format in [JSON](https://en.wikipedia.org/wiki/JSON). The expected encoding is [utf-8](https://en.wikipedia.org/wiki/UTF-8).

### An example of configuration file

```json
{
  "if_directory_empty": "download_from_4_days",
  "podcasts": [
    {
      "name": "Python for dummies",
      "rss_link": "http://python-for-dummies/atom.rss",
      "path": "~/podcasts/PythonForDummies"
    },
    {
      "name": "The Skeptic Guide",
      "rss_link": "https://feed.theskepticsguide.org/feed/rss.aspx",
      "path": "~/podcasts/SGTTU"
    }
  ]
}
```

### The settings hierarchy

The script will replace default values by read from configuration file.
Those will be cover by all values given by command line.

```
 command line parameters > configuration file > default values
```

### The main options

| Property             | Type       | Required | Default                                | Note |
|:---------------------|:----------:|:--------:|:--------------------------------------:|:-----|
| `downloads_limit`    | number     | no       | infinity                               |      |
| `if_directory_empty` | string     | no       | download_last                          | See [In case of empty directory](#in-case-of-empty-directory) |
| `podcast_extensions` | key-value  | no       | `{".mp3": "audio/mpeg"}`               | See [File types filter](#file-types-filter) |
| `podcasts`           | subsection | yes      | `[]`                                   | See [Podcasts sub category](#podcasts-sub-category) |
| `http_headers`       | key-value  | no       | `{"User-Agent": "podcast-downloader"}` | See [HTTP request headers](#http-request-headers) |
| `fill_up_gaps`       | boolean    | no       | false                                  | See [Download files from gaps](#download-files-from-gaps) |

### Podcasts sub category

`Podcasts` is the part of configuration file where you provide the array of objects with fallowing content:

| Property             | Type       | Required | Default                                | Note |
|:---------------------|:----------:|:--------:|:--------------------------------------:|:-----|
| `name`               | string     | yes      | -                                      | The name of channel (use in logger) |
| `rss_link`           | string     | yes      | -                                      | The URL of RSS feed |
| `path`               | string     | yes      | -                                      | The path to directory, where podcast are stored, will be downloaded |
| `file_name_template` | string     | no       | `%file_name%.%file_extension%`         | The template for the downloaded files, see [File name template](#file-name-template)|
| `disable`            | boolean    | no       | `false`                                | This podcast will be ignored |
| `podcast_extensions` | key-value  | no       | `{".mp3": "audio/mpeg"}`               | The file filter |
| `if_directory_empty` | string     | no       | `download_last`                        | See [In case of empty directory](#in-case-of-empty-directory) |
| `require_date`       | boolean    | no       | `false`                                | **Deprecated** Is date of podcast should be added into name of file - use the `file_name_template`: `[%publish_date%] %file_name%.%file_extension%"` |
| `http_headers`       | key-value  | no       | `{"User-Agent": "podcast-downloader"}` | See [HTTP request headers](#http-request-headers) |
| `fill_up_gaps`       | boolean    | no       | false                                  | See [Download files from gaps](#download-files-from-gaps) |

### HTTP request headers

Some servers may don't like how the urllib is presenting itself to them (the HTTP User-Agent header). This may lead into problems like: `urllib.error.HTTPError: HTTP Error 403: Forbidden`. That is way, there is a possibility to present the script client as something else.

There is an option to specify HTTP headers when downloading files.
You can provide them using the `http_headers` value in the configuration file.
The option value should be a dictionary where each header is presented as a key-value pair, with the key being the header title and the value being the header value.

Default value: `{"User-Agent": "podcast-downloader"}`. Providing any value for `http_headers` will override the default value.

Podcast `http_headers` will be merged with the global `http_headers`. In case of a conflict (same key name), the vale from podcast sub-configuration will override the global one.

Example:

```json
{
  "http_headers": {
    "User-Agent": "podcast-downloader"
  },
  "podcasts": [
    {
      "name": "Unu Podcast",
      "rss_link": "http://www.unupodcast.org/feed.rss",
      "path": "~/podcasts/unu_podcast",
      "https_headers": {
        "User-Agent": "User-Agent: Mozilla/5.0",
      }
    }
  ]
}
```

## Script arguments

The script accept following command line arguments:

| Short version | Long name              | Parameter           | Default         | Note |
|:--------------|:-----------------------|:-------------------:|:---------------:|:-----|
|               | `--downloads_limit`    | number              | infinity        | The maximum number of downloaded mp3 files |
|               | `--if_directory_empty` | string              | `download_last` | The general approach on empty directory |

## Adding date to file name

If RSS channel doesn't have single and constant name convention, it may causing the script to working incorrectly. The solution is force files to have common and meaningful prefix. The script is able to adding the date on beginning of downloaded file name.

Use [File name template](#file-name-template) and option `%publish_date%`.

## File name template

Use to change the name of downloaded file after its downloading.

Default value (the `%file_name%.%file_extension%`) will simple save up the file as it was uploaded by original creator. The file name and its extension is taken from the link to podcast file.

Template values:

| Name               | Notes                                                   |
|:-------------------|:--------------------------------------------------------|
| `%file_name%`      | The file name taken from link, without extension        |
| `%file_extension%` | The extension for the file, taken from link             |
| `%publish_date%`   | The publish date of the RSS entry                       |
| `%title%`          | The title of the RSS entry                              |

### Non default the publish_date

The `%publish_date%` by default gives result in format `YEARMMDD`. In order to change the date you can provide the new format after the colon (the `:` character). The script respect the codes [of the 1989 C standard](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes), but the percent sign (`%`) must be replaced by dollar sign (`$`). This is because of my unfortunate decision to use the percent character as marker of the code.


| The standard code | The script code | Notes                                      |
|:------------------|:----------------|:-------------------------------------------|
| `%Y%m%d`          | `$Y$m$d`        | The default value of the `%publish_date%`  |
| `%A`              | `$A`            | Adds the weekday (local language settings) |
| `%x`              | `$x`            | The local date represent. **Warning**: in some settings, the `/` is used here, so it may caused problem in the file name |

### Examples

* `[%publish_date%] %file_name%.%file_extension%`
* `[%publish_date%] %title%.%file_extension%`

## File types filter

Podcasts are mostly stored as `*.mp3` files. By default Podcast Downloader will look just for them.

If your podcast support other types of media files, you can precised your own podcast file filter, by providing extension for the file (like `.mp3`), and type of link in RSS feed itself (for `mp3` it is `audio/mpeg`).

If you don't know the type of the file, you can check the RSS file. Seek for `enclosure` tags, should looks like this:

```xml
  <enclosure
    url="https://an.apple.supporter.page/podcast/episode23.m4a"
    length="14527149"
    type="audio/x-m4a" />
```

Notes: the dot on the file extension is require.

### Example

```json
  "podcast_extensions": {
    ".mp3": "audio/mpeg",
    ".m4a": "audio/x-m4a"
  }
```

## In case of empty directory

If a directory for podcast is empty, the script needs to recognize what to do. Due to lack of database, you can:

* [download all episodes from feed](#download-all-from-feed)
* [download only the last episode](#only-last)
* [download last n episodes](#download-n-last-episodes)
* [download all new episode from last n days](#download-all-from-n-days)
* [download all new episode since day after, the last episode should appear](#download-all-episode-since-last-excepted)

### Download all from feed

The script will download all episodes from the feed.

Set by `download_all_from_feed`.

### Only last

The script will download only the last episode from the feed.
It is a good approach when you wish to start listening the podcast.
It is also default approach of the script.

Set by `download_last`.

### Download last n episodes

The script will download exactly given number of episodes from the feed.

Set by `download_last_n_episodes`. The *n* must be replaced by number of episodes, which you wanted to have downloaded. For example: `download_last_5_episodes` means that five last episodes will be downloaded.

### Download all from n days

The script will download all episodes which appear in last *n* days. I can be use when you are downloading on regular schedule.
The *n* number is given within the setup value: `download_from_n_days`. For example: `download_from_3_days` means download all episodes from last 3 days.

### Download all episode since last excepted

The script will download all episodes which appear after the day of release of last episode.

The *n* number is the day of the normal episode.
You can provide here week days as word (size of the letters is ignored)

| Full week day | Shorten name |
|:--------------|:-------------|
| Monday        | Mon          |
| Tuesday       | Tues         |
| Wednesday     | Weds         |
| Thursday      | Thurs        |
| Friday        | Fri          |
| Saturday      | Sat          |
| Sunday        | Sun          |

You can provide the number, it will means the day of the month. The script accepts only number from 1 to 28.

Set by `download_from_`.

Examples:

| Example value          | Meaning |
|------------------------|---------|
| `download_from_monday` | New episodes appear in Monday. The script will download all episodes since last Tuesday (including it) |
| `download_from_Fri`    | New episodes appear in Friday. The script will download all episodes since last Saturday (including it) |
| `download_from_12`     | New episodes appear each 12th of month. The script will download all episodes since 13 month before |

## Download files from gaps

The script recognizes the stream of downloaded files (based on the feed). By default, the last downloaded file (according to the feed) marks the start of downloading. In case of gaps, situations where there are missing files before the last downloaded one, the script will ignore them by default. However, there is a possibility to change this behavior to download all missing files between already downloaded ones. To enable this, you need to set the `fill_up_gaps` value to **true**. It's important to note that the script will not download files before the first one (according to the feed).

Default value: `false`.

## The analyze of the RSS feed

The script is look through all the `items` nodes in RSS file. The `item` node can contain the `enclosure` node. Those nodes are used to passing the files. According to the convention the single `item` should contain only one `enclosure`, but script (as [the library used](https://pypi.org/project/feedparser/) under it) can handle the multiple files attached into podcast `item`.

## Converting the OPML

The [OPML](https://en.wikipedia.org/wiki/OPML) files can be converted into [configuration](#configuration). The output file needs to be adjusted (missing the `path`).

```py
import json
import sys
import xml.etree.ElementTree as ET


def build_podcast(node_rss):
    return {
        "name": node_rss.attrib["title"],
        "rss_link": node_rss.attrib["xmlUrl"],
        "path": "",
    }


tree = ET.parse(sys.argv[1])
podcasts = list(map(build_podcast, tree.findall("body/outline[@type='rss']")))
result = json.dumps({"podcasts": podcasts}, sort_keys=True, indent=4)

print(result)
```

Example of usage (after saving it as `opml_converter.py`):

```sh
python opml_converter.py example.opml > podcast_downloader_config.json
```
