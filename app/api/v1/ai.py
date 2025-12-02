from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import require_auth
from app.schemas.ai import (
    AIGenerateRequest, AIGenerateResponse, 
    AIAgentQueryRequest, AIAgentQueryResponse,
    AITaggingRequest, AITaggingResponse,
    AIExtractionRequest, AIExtractionResponse
)
from app.services.ai_service import ai_service
from app.services.ai_agent import ai_agent_service

router = APIRouter()


@router.post("/generate", response_model=AIGenerateResponse)
async def generate_content(
    request: AIGenerateRequest,
    current_user: dict = Depends(require_auth)
):
    """
    Generate content using AI.
    
    Tasks:
    - summarize: Summarize text
    - seo: Generate SEO tags
    - expand: Expand points into paragraphs
    - tone: Rewrite in a specific tone
    """
    try:
        return await ai_service.generate_content(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI generation failed"
        )


@router.post("/agent/query", response_model=AIAgentQueryResponse)
async def query_data_agent(
    request: AIAgentQueryRequest,
    current_user: dict = Depends(require_auth)
):
    """
    Query the database using natural language via the AI Data Agent.
    """
    # Check if user is admin (optional, for safety)
    # if not current_user.get("is_superuser"):
    #     raise HTTPException(status_code=403, detail="Not authorized")
        
    try:
        return await ai_agent_service.query(request.query)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/generate/tags", response_model=AITaggingResponse)
async def generate_tags(
    request: AITaggingRequest,
    current_user: dict = Depends(require_auth)
):
    """
    Generate tags for content.
    """
    try:
        return await ai_service.generate_tags(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI tagging failed"
        )


@router.post("/extract", response_model=AIExtractionResponse)
async def extract_content(
    request: AIExtractionRequest,
    current_user: dict = Depends(require_auth)
):
    """
    Extract structured data from text.
    """
    try:
        return await ai_service.extract_content(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI extraction failed"
        )
