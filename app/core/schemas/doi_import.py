from pydantic import BaseModel, Field


class DoiBulkImportRequest(BaseModel):
    dois: list[str] = Field(min_length=1)
    enrich: bool = True
