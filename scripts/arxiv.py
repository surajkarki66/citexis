import urllib.parse
import requests

query = urllib.parse.quote("all:transformer attention mechanism")
resp = requests.get(f"http://export.arxiv.org/api/query?search_query={query}&max_results=3")

import xml.etree.ElementTree as ET
root = ET.fromstring(resp.text)
ns = {"atom": "http://www.w3.org/2005/Atom"}

for entry in root.findall("atom:entry", ns):
    title = entry.find("atom:title", ns).text.strip()
    print(title[:80])