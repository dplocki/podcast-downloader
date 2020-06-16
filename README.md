# Podcast Downloader

The Python module for downloading missing mp3 from given RSS feeds (mostly podcasts).
It do not using database of any sort, but it require configuration file.

## Setup

### Installation from PyPI

```bash
pip install podcast_downloader
```

### Configuration

Provide a configuration file. Place the `.podcast_downloader_config.json` it your home directory ([JSON](https://en.wikipedia.org/wiki/JSON) format). It should contain an array of settings. Each setting per RSS channel.

### Usage

```bash
python -m podcast_downloader
```

## In action

Using the [example above](#example), the result will be:

```log
[2020-06-16 19:54:35] Loading configuration (from file: "~/.podcast_downloader_config.json")
[2020-06-16 19:54:35] Checking "The Skeptic Guide"
[2020-06-16 19:54:35] Last downloaded file "skepticast2020-06-13.mp3"
[2020-06-16 19:54:39] The Skeptic Guide: Nothing new
[2020-06-16 19:54:39] ------------------------------
[2020-06-16 19:54:39] Finished
```

## Script arguments

The script accept following command line arguments:

| Short version | Long name              | Parameter           | Default         | Note |
|:--------------|:-----------------------|:-------------------:|:---------------:|:-----|
|               | `--downloads_limit`    | number              | inifinity       | The maximum number of downloaded mp3 files |
|               | `--if_directory_empty` | string              | `download_last` | The general approach on empty directory' |

## Configuration hierarchy

The script will replace default values by read from configuration file.
Those will be cover by all values given by command line.

### Podcasts

`Podcasts` is the part of configuration file where you provide the array of objects with fallowing content:

| Property       | Type    | Required | Default | Note |
|:---------------|:-------:|:--------:|:-------:|:-----|
| `name`         | string  | yes      | -       | The name of channel (used in logger) |
| `rss_link`     | string  | yes      | -       | The URL of RSS channel |
| `path`         | string  | yes      | -       | The path to directory, for podcast files |
| `require_date` | boolean | no       | `false` | Is date of podcast should be added into name of file |
| `disable`      | boolean | no       | `false` | This podcast will be ignored |

An example:

```json
{
    "if_directory_empty": "download_from_4_days",
    "podcasts": [
        {
            "name": "The Skeptic Guide",
            "rss_link": "http://www.theskepticsguide.org/feed/rss.aspx",
            "path": "~/podcasts/SGTTU"
        }
    ]
}
```

## Adding date to file name

If RSS channel doesn't have single and constant name convention, script is able to adding the date on beginning of downloaded file name. Just set the `require_date` option to true.

## In case of empty directory

If a directory for podcast is empty, the script needs to recognize what to do. Due to lack of database, you can:

* download only the last episode

* download all new episode from last n days

### Only last

The script will download only the last episode from the feed.
It is a good approach when you wish to start listening the podcast.
It is also default approach of the script.

Set by `download_last`.

### Download all from n days

The script will download all episodes which appear in last *n* days. I can be use when you are downloading on regular schedule.
The *n* number is given within the setup value: `download_from_n_days`. For example: `download_from_3_days` means download all episodes from last 3 days.
