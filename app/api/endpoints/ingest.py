from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from app.models.schemas import IngestRequest, IngestResponse
from app.services.document_service import DocumentService
from app.services.observability_service import ObservabilityService
from app.core.dependencies import get_document_service, get_observability_service

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse, status_code=201)
async def ingest_document(
    request: IngestRequest,
    document_service: DocumentService = Depends(get_document_service),
    observability_service: ObservabilityService = Depends(get_observability_service)
) -> IngestResponse:
    """
    Ingest a document from text content or URL.
    
    Supports text, HTML, markdown, and PDF URLs.
    """
    # Log incoming request
    observability_service.log_request("/ingest", {
        "document_type": request.document_type,
        "content_length": len(request.content),
        "has_content": bool(request.content.strip())
    })
    
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
        
        # Log successful response
        observability_service.log_response("/ingest", 201, len(str(result.dict())))
        
        return result
    
    except HTTPException as e:
        # Log HTTP error
        observability_service.log_response("/ingest", e.status_code, len(str(e.detail)))
        raise
    except Exception as e:
        # Log internal error
        observability_service.log_response("/ingest", 500, len(str(e)))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/ingest/file", response_model=IngestResponse, status_code=201)
async def ingest_file(
    file: UploadFile = File(..., description="PDF file to upload"),
    document_type: str = Form(default="pdf", description="Document type"),
    document_service: DocumentService = Depends(get_document_service),
    observability_service: ObservabilityService = Depends(get_observability_service)
) -> IngestResponse:
    """
    Ingest a document from file upload.
    
    Currently supports PDF files only.
    """
    # Log incoming file upload request
    observability_service.log_request("/ingest/file", {
        "filename": file.filename,
        "document_type": document_type,
        "content_type": file.content_type
    })
    
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
        
        # Add file size to observability
        observability_service.log_metrics("file_upload", {
            "filename": file.filename,
            "file_size": len(file_content),
            "document_type": document_type
        })
        
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
        
        # Log successful response
        observability_service.log_response("/ingest/file", 201, len(str(result.dict())))
        
        return result
    
    except HTTPException as e:
        # Log HTTP error
        observability_service.log_response("/ingest/file", e.status_code, len(str(e.detail)))
        raise
    except Exception as e:
        # Log internal error
        observability_service.log_response("/ingest/file", 500, len(str(e)))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        ) 