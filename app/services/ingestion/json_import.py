import json

from pydantic import ValidationError

from app.core.schemas.json_import import REQUIRED_JSON_FIELDS, JsonBulkPaperImport
from app.core.schemas.paper import AuthorSchema, PaperCreate


class JsonImportError(ValueError):
    """Raised when a bulk JSON import payload is invalid."""


def _coerce_authors(raw: object) -> list[AuthorSchema]:
    if not isinstance(raw, list):
        raise JsonImportError("authors must be a list")

    authors: list[AuthorSchema] = []
    for item in raw:
        if isinstance(item, str):
            name = item.strip()
            if name:
                authors.append(AuthorSchema(name=name))
            continue
        if isinstance(item, dict):
            authors.append(AuthorSchema.model_validate(item))
            continue
        raise JsonImportError("each author must be a string or an object with a name")
    if not authors:
        raise JsonImportError("authors must contain at least one name")
    return authors


def _missing_fields(raw: dict) -> list[str]:
    return [field for field in REQUIRED_JSON_FIELDS if field not in raw or raw[field] in (None, "", [])]


def _coerce_paper(raw: object, index: int) -> PaperCreate:
    if not isinstance(raw, dict):
        raise JsonImportError(f"paper at index {index} must be an object")

    missing = _missing_fields(raw)
    if missing:
        raise JsonImportError(
            f"paper at index {index} is missing required fields: {', '.join(missing)}",
        )

    payload = dict(raw)
    payload["authors"] = _coerce_authors(payload["authors"])

    try:
        return JsonBulkPaperImport.model_validate(payload).to_paper_create()
    except ValidationError as exc:
        detail = exc.errors()[0]["msg"] if exc.errors() else str(exc)
        raise JsonImportError(f"paper at index {index}: {detail}") from exc


def parse_papers_json(raw: bytes) -> list[PaperCreate]:
    if not raw.strip():
        raise JsonImportError("JSON file is empty")

    try:
        data = json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise JsonImportError("JSON file must be UTF-8 encoded") from exc
    except json.JSONDecodeError as exc:
        raise JsonImportError(f"Invalid JSON: {exc.msg}") from exc

    if isinstance(data, list):
        items = data
    elif isinstance(data, dict) and isinstance(data.get("papers"), list):
        items = data["papers"]
    else:
        raise JsonImportError('JSON must be a list of papers or {"papers": [...]}')

    if not items:
        raise JsonImportError("JSON file contains no papers")

    return [_coerce_paper(item, index) for index, item in enumerate(items)]
