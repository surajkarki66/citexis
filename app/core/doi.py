def normalize_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    value = doi.strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if value.lower().startswith(prefix):
            value = value[len(prefix) :]
    return value.lower() or None
