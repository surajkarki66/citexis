import re
import xml.etree.ElementTree as ET

import httpx

from app.core.doi import normalize_doi

ARXIV_API = "https://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
ARXIV_ID_PATTERN = re.compile(r"arxiv\.org/abs/([^/?#]+)", re.IGNORECASE)
ARXIV_USER_AGENT = "Citexis/0.1 (https://github.com/citexis; mailto:support@citexis.local)"


def build_arxiv_search_query(user_query: str) -> str:
    query = user_query.strip()
    if not query:
        raise ValueError("Search query is required")

    lowered = query.lower()
    if any(
        marker in lowered
        for marker in ("cat:", "all:", "ti:", "au:", "abs:", " and ", " or ", "id:")
    ):
        return query

    terms = query.split()
    return "all:" + "+".join(terms)


def _arxiv_id_from_entry(entry: ET.Element) -> str | None:
    raw_id = entry.findtext("atom:id", default="", namespaces=ATOM_NS).strip()
    match = ARXIV_ID_PATTERN.search(raw_id)
    if match:
        return match.group(1)
    for link in entry.findall("atom:link", ATOM_NS):
        href = link.attrib.get("href", "")
        match = ARXIV_ID_PATTERN.search(href)
        if match:
            return match.group(1)
    return None


def _doi_from_entry(entry: ET.Element) -> str | None:
    raw_doi = entry.findtext("arxiv:doi", default="", namespaces=ATOM_NS).strip()
    if raw_doi:
        return normalize_doi(raw_doi)

    for link in entry.findall("atom:link", ATOM_NS):
        if link.attrib.get("title") == "doi":
            return normalize_doi(link.attrib.get("href"))
    return None


def _year_from_entry(entry: ET.Element) -> int | None:
    published = entry.findtext("atom:published", default="", namespaces=ATOM_NS).strip()
    if len(published) >= 4 and published[:4].isdigit():
        return int(published[:4])
    return None


def parse_arxiv_feed(xml_text: str) -> tuple[int, list[dict]]:
    root = ET.fromstring(xml_text)
    total_raw = root.findtext("{http://a9.com/-/spec/opensearch/1.1/}totalResults", default="0")
    total_results = int(total_raw or 0)

    papers: list[dict] = []
    for entry in root.findall("atom:entry", ATOM_NS):
        title = " ".join(entry.findtext("atom:title", default="", namespaces=ATOM_NS).split())
        authors = [
            name.strip()
            for author in entry.findall("atom:author", ATOM_NS)
            if (name := author.findtext("atom:name", default="", namespaces=ATOM_NS).strip())
        ]
        papers.append(
            {
                "arxiv_id": _arxiv_id_from_entry(entry),
                "title": title,
                "authors": authors,
                "doi": _doi_from_entry(entry),
                "year": _year_from_entry(entry),
            },
        )
    return total_results, papers


class ArxivSource:
    """Search arXiv and extract DOIs from Atom feed entries."""

    async def search(self, query: str, limit: int) -> dict:
        search_query = build_arxiv_search_query(query)
        max_results = max(1, min(limit, 50))

        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": ARXIV_USER_AGENT},
        ) as client:
            response = await client.get(
                ARXIV_API,
                params={
                    "search_query": search_query,
                    "start": 0,
                    "max_results": max_results,
                },
            )
            response.raise_for_status()

        try:
            total_results, papers = parse_arxiv_feed(response.text)
        except ET.ParseError as exc:
            raise ValueError("arXiv returned an invalid response") from exc

        dois = [paper["doi"] for paper in papers if paper["doi"]]

        return {
            "query": query,
            "arxiv_query": search_query,
            "total_results": total_results,
            "returned": len(papers),
            "doi_count": len(dois),
            "dois": dois,
            "papers": papers,
        }
