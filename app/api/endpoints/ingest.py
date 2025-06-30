from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from app.models.schemas import IngestRequest, IngestResponse
from app.services.document_service import DocumentService
from app.core.dependencies import get_document_service

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse, status_code=201)
async def ingest_document(
    request: IngestRequest,
    document_service: DocumentService = Depends(get_document_service)
) -> IngestResponse:
    """
    Ingest a document from text content or URL.
    
    Supports text, HTML, markdown, and PDF URLs.
    """
    try:
        if not request.content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content cannot be empty"
            )
        
        result = await document_service.ingest_document(
            content=request.content,
            document_type=request.document_type
        )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/ingest/file", response_model=IngestResponse, status_code=201)
async def ingest_file(
    file: UploadFile = File(..., description="PDF file to upload"),
    document_type: str = Form(default="pdf", description="Document type"),
    document_service: DocumentService = Depends(get_document_service)
) -> IngestResponse:
    """
    Ingest a document from file upload.
    
    Currently supports PDF files only.
    """
    try:
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported for file upload"
            )
        
        if document_type != "pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File upload only supports PDF document type"
            )
        
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty"
            )
        
        result = await document_service.ingest_file(
            file_content=file_content,
            filename=file.filename or "uploaded_file.pdf",
            document_type=document_type
        )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        ) 