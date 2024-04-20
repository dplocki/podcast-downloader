from podcast_downloader.rss import load_feed


rss_source_link = 'https://feed.theskepticsguide.org/feed/rss.aspx'
feed = load_feed(rss_source_link)

print(feed)