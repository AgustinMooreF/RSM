from typing import Literal, Optional, List
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
    document_info: Optional[dict] = Field(None, description="Additional document information")


class QueryRequest(BaseModel):
    question: str = Field(..., description="Question to ask about the ingested documents")


class Source(BaseModel):
    page: Optional[int] = Field(None, description="Page number (for PDFs)")
    text: str = Field(..., description="Source text passage")
    

class QueryResponse(BaseModel):
    answer: str = Field(..., description="Generated answer")
    sources: List[Source] = Field(default=[], description="Source passages used for the answer") 