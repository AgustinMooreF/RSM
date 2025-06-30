from fastapi import APIRouter, HTTPException, status
from app.models.schemas import IngestRequest, IngestResponse

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse, status_code=201)
async def ingest_document(request: IngestRequest) -> IngestResponse:
    try:
        if not request.content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content cannot be empty"
            )
        
        # Mock response
        return IngestResponse(
            status="success",
            message=f"Successfully processed {request.document_type} document",
            chunks_created=5
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        ) 