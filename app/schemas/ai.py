from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class AIGenerateRequest(BaseModel):
    """Request schema for AI content generation."""
    prompt: str = Field(..., description="The main prompt or content to process")
    context: Optional[str] = Field(None, description="Additional context or background info")
    task: str = Field(..., description="Task type: summarize, expand, seo, tone, custom")
    tone: Optional[str] = Field(None, description="Desired tone (e.g., professional, friendly)")
    max_length: Optional[int] = Field(None, description="Max length of the output")


class AIGenerateResponse(BaseModel):
    """Response schema for AI content generation."""
    result: str
    usage: Optional[Dict[str, int]] = None


class AIAgentQueryRequest(BaseModel):
    """Request schema for AI Data Agent."""
    query: str = Field(..., description="Natural language query about the data")


class AIAgentQueryResponse(BaseModel):
    """Response schema for AI Data Agent."""
    answer: str
    sql_query: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
