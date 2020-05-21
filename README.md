# Podcast Downloader

The Python script for downloading new mp3 from RSS given channels.
It do not using any database, but it require configuration file.

## Script arguments

The script accept following command line arguments:

| Short version | Long name           | Parameter           | Default   | Note |
|:--------------|:--------------------|:-------------------:|:---------:|:-----|
|               | `--downloads_limit` | number              | inifinity | The maksimum number of downloaded mp3 files |

## Configuration

Provide a configuraiton file with name `config.json` ([JSON](https://en.wikipedia.org/wiki/JSON) format). It should contain an array of settings. Each setting per RSS channel.

| Property       | Type    | Required | Default | Note |
|:---------------|:-------:|:--------:|:-------:|:-----|
| `name`         | string  | yes      | -       | The name of channel (used in logger) |
| `rss_link`     | string  | yes      | -       | The URL of RSS channel |
| `path`         | string  | yes      | -       | The path to directory, for podcast files |
| `require_date` | boolean | no       | `false` | Is date of podcast should be added into name of file |
| `disable`      | boolean | no       | `false` | This podcast will be ignored |

### Example

```json
[
    {
        "name": "The Skeptic Guide",
        "rss_link": "http://www.theskepticsguide.org/feed/rss.aspx",
        "path": "~/podcasts/SGTTU"
    }
]
```

## In action

Using the [example above](#example), the result will be:

```log
[2020-03-29 11:24:30] Loading configuration (from file: "config.json")
[2020-03-29 11:24:30] Checking "The Skeptic Guide"
[2020-03-29 11:24:30] Last downloaded file "skepticast2020-03-21.mp3"
[2020-03-29 11:24:34] The Skeptic Guide: Downloading file: "https://media.libsyn.com/media/skepticsguide/skepticast2020-03-28.mp3"
[2020-03-29 11:24:34] ------------------------------
[2020-03-29 11:24:34] Finished
```

## Adding date to file name

If RSS channel doesn't have single and constant name convention, script is able to adding the date on beginning of downloaded file name. Just set the `require_date` option to true.
