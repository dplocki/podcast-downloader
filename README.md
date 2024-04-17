# Podcast Downloader

![GitHub](https://img.shields.io/github/license/dplocki/podcast-downloader)
![Build Status](https://img.shields.io/endpoint.svg?url=https%3A%2F%2Factions-badge.atrox.dev%2Fdplocki%2Fpodcast-downloader%2Fbadge%3Fref%3Dmaster&style=flat)
![PyPI](https://img.shields.io/pypi/v/podcast-downloader)
[![Downloads](https://img.shields.io/pypi/dm/podcast-downloader.svg)](https://pypi.python.org/pypi/podcast-downloader)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

The Python module designed for downloading files from given RSS feeds, particularly targeted at podcasts.
It does not use any sort of database but requires a configuration file.

The script is intended to be run periodically. Upon starting, it analyzes the directory where it previously stored downloaded files.
It then compares these files with those listed in the RSS feed, identifying any missing ones and downloading them.

The files searched by default are `mp3`.

The result of using the [example below](#configuration), on empty directories, will be:

```log
dplocki@ghost-wheel:~$ python -m podcast_downloader
[2024-04-08 21:19:10] Loading configuration (from file: "~/.podcast_downloader_config.json")
[2024-04-08 21:19:15] Checking "The Skeptic Guide"
[2024-04-08 21:19:15] Last downloaded file "<none>"
[2024-04-08 21:19:15] The Skeptic Guide: Downloading file: "https://traffic.libsyn.com/secure/skepticsguide/skepticast2024-04-06.mp3" saved as "skepticast2024-04-06.mp3"
[2024-04-08 21:19:41] Checking "The Real Python Podcast"
[2024-04-08 21:19:41] Last downloaded file "<none>"
[2024-04-08 21:19:41] The Real Python Podcast: Downloading file: "https://chtbl.com/track/92DB94/files.realpython.com/podcasts/RPP_E199_03_Calvin.eef1db4d6679.mp3" saved as "[20240405] rpp_e199_03_calvin.eef1db4d6679.mp3"
[2024-04-08 21:20:04] Finished
```

The result:

```
dplocki@ghost-wheel:~$ tree podcasts/
podcasts/
├── RealPython
│   └── [20240405] rpp_e199_03_calvin.eef1db4d6679.mp3
└── SGTTU
    └── skepticast2024-04-06.mp3

2 directories, 2 files
```

## Setup

Installation from PyPI:

```bash
pip install podcast_downloader
```

## Running the script

The script [requires configuration file](#configuration) in order to work.
After installation, the script can be run as any Python module:

```bash
python -m podcast_downloader
```

It is also possible to run the script with given configuration file:

```bash
python -m podcast_downloader --config my_config.json
```

## Configuration

An example of configuration file

```json
{
  "if_directory_empty": "download_from_4_days",
  "podcasts": [
    {
      "name": "The Skeptic Guide",
      "rss_link": "https://feed.theskepticsguide.org/feed/rss.aspx",
      "path": "~/podcasts/SGTTU"
    },
    {
      "rss_link": "https://realpython.com/podcasts/rpp/feed",
      "path": "~/podcasts/RealPython",
      "file_name_template": "[%publish_date%] %file_name%.%file_extension%"
    }
  ]
}
```

### The configuration file

By default the configuration file is placed in home directory. It's file name is: `.podcast_downloader_config.json`.

The config file is format in [JSON](https://en.wikipedia.org/wiki/JSON). The expected encoding is [utf-8](https://en.wikipedia.org/wiki/UTF-8).

The path to configuration file can be specified by [script argument](#script-arguments).

### The settings hierarchy

The script replaces default values by those read from configuration file.
Those will be overload by values given from command line.

```
command line parameters > configuration file > default values
```

### The main options

| Property             | Type       | Required? | Default                                | Note |
|:---------------------|:----------:|:---------:|:--------------------------------------:|:-----|
| `downloads_limit`    | number     | no        | infinity                               |      |
| `if_directory_empty` | string     | no        | download_last                          | See [In case of empty directory](#in-case-of-empty-directory) |
| `podcast_extensions` | key-value  | no        | `{".mp3": "audio/mpeg"}`               | See [File types filter](#file-types-filter) |
| `podcasts`           | subsection | yes       | `[]`                                   | See [Podcasts sub category](#podcasts-sub-category) |
| `http_headers`       | key-value  | no        | `{"User-Agent": "podcast-downloader"}` | See [HTTP request headers](#http-request-headers) |
| `fill_up_gaps`       | boolean    | no        | false                                  | See [Download files from gaps](#download-files-from-gaps) |
| `download_delay`     | number     | no        | `0`                                    | See [Download delay](#download-delay) |

### Podcasts sub category

The `podcasts` segment is the part of configuration file where you provide the array of objects with fallowing content:

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

Some servers may not like how the urllib is presenting itself to them (the HTTP User-Agent header). This may lead into problems like: `urllib.error.HTTPError: HTTP Error 403: Forbidden`. That is why, there is a possibility for the script to pose as something else: by specifying the HTTP headers during downloading files.

Use the `http_headers` option in the configuration file. The value should be a dictionary object where each header is presented as a key-value pair. The key being the header title and the value being the header value.

By default the value is: `{"User-Agent": "podcast-downloader"}`. Providing anything else for `http_headers` will override all the default values (they do not merge).

On other hand in the podcast sub-configuration, the `http_headers` will be merged with the global `http_headers`. In case of a conflict (same key name), the vale from podcast sub-configuration will override the global one.

Example:

```json
{
  "http_headers": {
    "User-Agent": "podcast-downloader"

  },
  "podcasts": [
    {
      "name": "Unua Podcast",
      "rss_link": "http://www.unuapodcast.org/feed.rss",
      "path": "~/podcasts/unua_podcast",
      "https_headers": {
        "User-Agent": "Mozilla/5.0"
      }
    },
    {
      "name": "Dua Podcast",
      "rss_link": "http://www.duapodcast.org/feed.rss",
      "path": "~/podcasts/dua_podcast",
      "https_headers": {
        "Authorization": "Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ=="
      }
    }
  ]
}
```

In this example, the Unua Podcast will be download just with the header: `User-Agent: Mozilla/5.0`, and the Dua Podcast with: `User-Agent: podcast-downloader` and `Authorization: Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ==`.

### Download delay

When you had a lot of files to download from a single server, it may be better to set up the small delay between downloads to avoid being recognized as an attacker by the server. In the script there is an option called `download_delay`, which represents the **number of seconds** the script will wait between downloads.

The default value is `0`.

Notes:

 * this delay applies per podcast, not between two different podcasts
 * the value can be provided as [script argument](#script-arguments)

## Script arguments

The script accepts following command line arguments:

| Short version | Long name              | Parameter           | Default                             | Note |
|:--------------|:-----------------------|:-------------------:|:-----------------------------------:|:-----|
|               | `--config`             | string              | `~/.podcast_downloader_config.json` | The placement of the configuration file |
|               | `--downloads_limit`    | number              | infinity                            | The maximum number of downloaded mp3 files |
|               | `--if_directory_empty` | string              | `download_last`                     | The general approach on empty directory |
|               | `--download_delay`     | number              | `0`                                 | The waiting time (seconds) between downloads |

## File name template

Use to adjust the file name after downloading.

Default value (the `%file_name%.%file_extension%`) will simple save up the file as it was uploaded by original creator. The file name and its extension is based on the link to podcast file.

Template values:

| Name               | Notes                                                   |
|:-------------------|:--------------------------------------------------------|
| `%file_name%`      | The file name from the link, without extension          |
| `%file_extension%` | The extension for the file, from link                   |
| `%publish_date%`   | The publish date of the RSS entry                       |
| `%title%`          | The title of the RSS entry                              |

### Non-default the publish_date

The `%publish_date%` by default gives result in format `YEARMMDD`. In order to change it you can provide the new one after the colon (the `:` character). The script respect the codes [of the 1989 C standard](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes), but the percent sign (`%`) must be replaced by dollar sign (`$`). This is because of my unfortunate decision to use the percent character as marker of the code.

| The standard code | The script code | Notes                                      |
|:------------------|:----------------|:-------------------------------------------|
| `%Y%m%d`          | `$Y$m$d`        | The default value of the `%publish_date%`  |
| `%A`              | `$A`            | Adds the weekday (local language settings) |
| `%x`              | `$x`            | The local date represent. **Warning**: in some settings, the `/` is used here, so it may caused problem in the file name |

### Examples

* `[%publish_date%] %file_name%.%file_extension%`
* `[%publish_date%] %title%.%file_extension%`

## File types filter

Podcasts are mostly stored as `*.mp3` files. By default Podcast Downloader looks just for them, ignoring all others types.

If your podcast supports other types of media files, you can specified the file filters. Provide the  extension of the file (like `.mp3`) and type of link in RSS feed itself (for `mp3` it is `audio/mpeg`).

If you don't know the type of the file, you can look for it in the RSS file. Seek for `enclosure` tags, should looks like this:

```xml
  <enclosure url="https://www.vidocast.url/podcast/episode23.m4a"
             length="14527149"
             type="audio/x-m4a" />
```

**Note**: the dot on the file extension is require.

### Example

```json
  "podcast_extensions": {
    ".mp3": "audio/mpeg",
    ".m4a": "audio/x-m4a"
  }
```

## In case of empty directory

If a directory for podcast is empty, the script needs to know what to do. Due to lack of database, you can:

* [download all episodes from feed](#download-all-from-feed)
* [download only the last episode](#download-last)
* [download last n episodes](#download-last-n-episodes)
* [download all new episode from last n days](#download-all-from-n-days)
* [download all new episode since day after, the last episode should appear](#download-all-episode-since-last-excepted)

Default behavior is: `download_last`

### Download all from feed

The script will download all episodes from the feed.

Set by `download_all_from_feed`.

### Download last

The script will download only the last episode from the feed.
It is also default approach of the script.

Set by `download_last`.

### Download last n episodes

The script will download exactly the given number of episodes from the feed.

Set by `download_last_n_episodes`. The *n* must be replaced by a number of episodes, which you wanted to have downloaded. For example: `download_last_5_episodes` means that five most recent episodes will be downloaded.

### Download all from n days

The script will download all episodes which appear in recent *n* days. It can be use when you are downloading on regular schedule.
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

The script recognizes the stream of downloaded files (based on the feed data). By default, the last downloaded file (according to the feed) marks the start of downloading. In case of gaps, situation where there are missing files before the last downloaded one, the script will ignore them by default. However, there is a possibility to change this behavior to download all missing files between already downloaded ones. To enable this, you need to set the `fill_up_gaps` value to **true**. It's important to note that the script will not download files before the first one (according to the feed), the most earlier episode.

Default value: `false`.

## The analyze of the RSS feed

The script looks through all the `items` nodes in RSS file. The `item` node can contain the `enclosure` node. Those nodes are used to passing the files. According to the convention the single `item` should contain only one `enclosure`, but script (as [the library used](https://pypi.org/project/feedparser/) under it) can handle the multiple files attached into podcast `item`.

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
