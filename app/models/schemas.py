from typing import Literal
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    app_name: str
    version: str


class IngestRequest(BaseModel):
    content: str = Field(..., description="Document content or URL to ingest")
    document_type: Literal["pdf", "text", "html", "markdown"] = Field(
        ..., description="Type of document being ingested"
    )


class IngestResponse(BaseModel):
    status: Literal["success", "error"]
    message: str
    chunks_created: int = Field(ge=0, description="Number of chunks created from the document") 