import requests

resp = requests.get("https://api.openalex.org/works", params={
    "search": "CRISPR gene therapy",
    "per_page": 3,
    "sort": "cited_by_count:desc"
})

for work in resp.json()["results"]:
    print(work)