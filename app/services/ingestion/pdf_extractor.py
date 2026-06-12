import re
from io import BytesIO

from pypdf import PdfReader

from app.core.doi import normalize_doi
from app.core.schemas.paper import AuthorSchema, PaperCreate

DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
ABSTRACT_MARKER = re.compile(r"\babstract\b", re.IGNORECASE)
SECTION_BREAK = re.compile(
    r"\n\s*(?:introduction|keywords|index terms|1\.\s*introduction)\b",
    re.IGNORECASE,
)
YEAR_PATTERN = re.compile(r"\b(?:19|20)\d{2}\b")
WHITESPACE = re.compile(r"\s+")


def _clean_text(text: str) -> str:
    return WHITESPACE.sub(" ", text).strip()


def _metadata_value(raw: object | None) -> str | None:
    if raw is None:
        return None
    if isinstance(raw, list):
        joined = " ".join(str(item).strip() for item in raw if str(item).strip())
        return joined or None
    value = str(raw).strip()
    return value or None


def _title_from_filename(filename: str) -> str:
    stem = filename.rsplit("/", 1)[-1]
    if stem.lower().endswith(".pdf"):
        stem = stem[:-4]
    stem = stem.replace("_", " ").replace("-", " ").strip()
    return stem or "Untitled PDF"


def _parse_authors(raw: str | None) -> list[AuthorSchema]:
    if not raw:
        return []
    parts = re.split(r";|,|\band\b", raw, flags=re.IGNORECASE)
    authors = [AuthorSchema(name=name.strip()) for name in parts if name.strip()]
    return authors[:20]


def _first_page_line(full_text: str) -> str | None:
    first_page = full_text.split("\f", 1)[0] if "\f" in full_text else full_text[:4000]
    for line in first_page.splitlines():
        cleaned = _clean_text(line)
        if 8 <= len(cleaned) <= 300:
            return cleaned
    return None


def _extract_title(metadata: dict, full_text: str, filename: str) -> str:
    meta_title = _metadata_value(metadata.get("/Title"))
    if meta_title and len(meta_title) > 3:
        return meta_title

    first_line = _first_page_line(full_text)
    if first_line:
        return first_line

    return _title_from_filename(filename)


def _extract_abstract(full_text: str, max_chars: int) -> str:
    match = ABSTRACT_MARKER.search(full_text)
    if not match:
        return ""

    rest = full_text[match.end() :].lstrip(" :-\n")
    end_match = SECTION_BREAK.search(rest)
    chunk = rest[: end_match.start()] if end_match else rest[: max_chars * 2]
    abstract = _clean_text(chunk)[:max_chars]
    return abstract if len(abstract) >= 80 else ""


def _extract_year(metadata: dict, full_text: str) -> int | None:
    for key in ("/CreationDate", "/ModDate"):
        raw = _metadata_value(metadata.get(key))
        if not raw:
            continue
        match = YEAR_PATTERN.search(raw)
        if match:
            return int(match.group(0))

    years = [int(match.group(0)) for match in YEAR_PATTERN.finditer(full_text[:2000])]
    if years:
        return years[-1]
    return None


def _find_doi(full_text: str) -> str | None:
    match = DOI_PATTERN.search(full_text)
    if not match:
        return None
    return normalize_doi(match.group(0))


def extract_paper_from_pdf(
    data: bytes,
    filename: str,
    *,
    abstract_max_chars: int,
) -> PaperCreate:
    if not data.startswith(b"%PDF"):
        raise ValueError("File is not a valid PDF")

    reader = PdfReader(BytesIO(data))
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception as exc:
            raise ValueError("Encrypted PDF could not be read") from exc

    metadata = reader.metadata or {}
    page_text = [page.extract_text() or "" for page in reader.pages]
    full_text = "\n".join(page_text).strip()
    if not full_text:
        raise ValueError(
            "No extractable text in PDF (scanned/image-only PDFs are not supported)",
        )

    title = _extract_title(metadata, full_text, filename)
    authors = _parse_authors(_metadata_value(metadata.get("/Author")))
    abstract = _extract_abstract(full_text, abstract_max_chars)
    if not abstract:
        abstract = _clean_text(full_text)[:abstract_max_chars]

    return PaperCreate(
        doi=_find_doi(full_text),
        title=title,
        authors=authors,
        abstract=abstract,
        year=_extract_year(metadata, full_text),
        venue=None,
        tags=["pdf-import"],
    )
