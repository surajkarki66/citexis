import xml.etree.ElementTree as ET

import httpx

from app.core.schemas.paper import AuthorSchema, PaperCreate
from app.services.ingestion.sources.base import PaperSource

ARXIV_API = "http://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


class ArxivSource(PaperSource):
    async def fetch(self, query: str, limit: int = 100) -> list[PaperCreate]:
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": limit,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(ARXIV_API, params=params)
            response.raise_for_status()

        root = ET.fromstring(response.text)
        papers: list[PaperCreate] = []

        for entry in root.findall("atom:entry", ATOM_NS):
            title = (entry.findtext("atom:title", default="", namespaces=ATOM_NS) or "").strip()
            abstract = (
                entry.findtext("atom:summary", default="", namespaces=ATOM_NS) or ""
            ).strip()
            authors = [
                AuthorSchema(name=(a.findtext("atom:name", default="", namespaces=ATOM_NS) or ""))
                for a in entry.findall("atom:author", ATOM_NS)
            ]
            published = entry.findtext("atom:published", default="", namespaces=ATOM_NS)
            year = int(published[:4]) if published else None
            link = next(
                (
                    l.attrib["href"]
                    for l in entry.findall("atom:link", ATOM_NS)
                    if l.attrib.get("type") == "application/pdf"
                ),
                None,
            )
            arxiv_id = entry.findtext("atom:id", default="", namespaces=ATOM_NS).split("/")[-1]

            papers.append(
                PaperCreate(
                    title=title,
                    abstract=abstract,
                    authors=authors,
                    year=year,
                    venue="arXiv",
                    tags=[],
                    full_text_url=link,
                    doi=f"arxiv:{arxiv_id}" if arxiv_id else None,
                )
            )

        return papers
