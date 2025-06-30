from fastapi import APIRouter, HTTPException, status, Depends
from app.models.schemas import QueryRequest, QueryResponse
from app.services.document_service import DocumentService
from app.core.dependencies import get_document_service

router = APIRouter()


@router.post("/query", response_model=QueryResponse, status_code=200)
async def query_documents(
    request: QueryRequest,
    document_service: DocumentService = Depends(get_document_service)
) -> QueryResponse:
    try:
        if not request.question.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="empty question"
            )
        
        result = await document_service.query_documents(
            question=request.question
        )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        ) 