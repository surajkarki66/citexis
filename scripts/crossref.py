import requests

resp = requests.get("https://api.crossref.org/works", params={
    "query": "machine learning",
    "rows": 3,
})

for item in resp.json()["message"]["items"]:
    print(item)