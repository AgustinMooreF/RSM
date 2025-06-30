from fastapi import APIRouter, HTTPException, status, Depends
from app.models.schemas import QueryRequest, QueryResponse
from app.services.document_service import DocumentService
from app.services.observability_service import ObservabilityService
from app.core.dependencies import get_document_service, get_observability_service

router = APIRouter()


@router.post("/query", response_model=QueryResponse, status_code=200)
async def query_documents(
    request: QueryRequest,
    document_service: DocumentService = Depends(get_document_service),
    observability_service: ObservabilityService = Depends(get_observability_service)
) -> QueryResponse:
    """
    Query documents using RAG (Retrieval-Augmented Generation) with observability.
    """
    # Log incoming query request
    observability_service.log_request("/query", {
        "question_length": len(request.question),
        "has_question": bool(request.question.strip())
    })
    
    try:
        if not request.question.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="empty question"
            )
        
        result = await document_service.query_documents(
            question=request.question
        )
        
        # Log successful response with metrics
        observability_service.log_response("/query", 200, len(str(result.dict())))
        observability_service.log_metrics("query_response", {
            "question_length": len(request.question),
            "answer_length": len(result.answer),
            "sources_count": len(result.sources)
        })
        
        return result
    
    except HTTPException as e:
        # Log HTTP error
        observability_service.log_response("/query", e.status_code, len(str(e.detail)))
        raise
    except Exception as e:
        # Log internal error
        observability_service.log_response("/query", 500, len(str(e)))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        ) 