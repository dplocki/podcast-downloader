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
