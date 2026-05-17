import requests

# CORE requires a free API key (quick signup)
resp = requests.get("https://api.core.ac.uk/v3/search/works", params={
    "q": "renewable energy storage",
    "limit": 3
}, headers={"Authorization": "Bearer ef1crpJswgFNiH0Dy2OMnxhZBXKaAU74"})

for work in resp.json()["results"]:
    print(f"{work['title']}")
    print(f"  Full text: {'Yes' if work.get('fullText') else 'Abstract only'}")