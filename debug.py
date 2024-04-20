from podcast_downloader.parameters import load_configuration_file
from podcast_downloader.rss import load_feed


config = load_configuration_file('a.json')
podcast_config = config['podcasts'][0]
rss_source_link = podcast_config['rss_link']
feed = load_feed(rss_source_link)

print(feed)
