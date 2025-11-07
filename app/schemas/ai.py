"""Pydantic schemas for AI endpoints."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GenerateContentRequest(BaseModel):
    """Request schema for content generation."""

    prompt: str = Field(..., description="Generation prompt", min_length=1)
    context: Optional[Dict[str, Any]] = Field(
        None, description="Optional context data"
    )
    max_tokens: int = Field(
        default=500, ge=1, le=2000, description="Maximum tokens to generate"
    )
    stream: bool = Field(default=False, description="Stream response tokens")


class GenerateContentResponse(BaseModel):
    """Response schema for content generation."""

    content: str = Field(..., description="Generated content")


class NaturalLanguageQueryRequest(BaseModel):
    """Request schema for natural language to filter conversion."""

    query: str = Field(..., description="Natural language query", min_length=1)
    collection_name: str = Field(..., description="Collection to query")


class NaturalLanguageQueryResponse(BaseModel):
    """Response schema for natural language query."""

    filter_expression: Optional[str] = Field(
        None, description="Generated filter expression"
    )
    explanation: Optional[str] = Field(None, description="Query explanation")


class EnrichDataRequest(BaseModel):
    """Request schema for data enrichment."""

    data: Dict[str, Any] = Field(..., description="Data to enrich")
    instructions: str = Field(..., description="Enrichment instructions", min_length=1)


class EnrichDataResponse(BaseModel):
    """Response schema for data enrichment."""

    enriched_data: Dict[str, Any] = Field(..., description="Enriched data")


class GenerateSchemaRequest(BaseModel):
    """Request schema for schema generation."""

    description: str = Field(
        ..., description="Description of the collection", min_length=1
    )


class GenerateSchemaResponse(BaseModel):
    """Response schema for schema generation."""

    schema: List[Dict[str, Any]] = Field(..., description="Generated schema fields")


class SemanticSearchRequest(BaseModel):
    """Request schema for semantic search."""

    query: str = Field(..., description="Search query", min_length=1)
    collection_name: str = Field(..., description="Collection to search")
    k: int = Field(default=5, ge=1, le=50, description="Number of results")
    score_threshold: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Minimum similarity score"
    )


class SemanticSearchResult(BaseModel):
    """Single semantic search result."""

    metadata: Dict[str, Any] = Field(..., description="Document metadata")
    similarity: float = Field(..., description="Similarity score (0-1)")


class SemanticSearchResponse(BaseModel):
    """Response schema for semantic search."""

    results: List[SemanticSearchResult] = Field(..., description="Search results")
    total: int = Field(..., description="Total number of results")


class IndexCollectionRequest(BaseModel):
    """Request schema for indexing a collection."""

    collection_name: str = Field(..., description="Collection to index")
    rebuild: bool = Field(
        default=False, description="Rebuild index from scratch"
    )


class IndexCollectionResponse(BaseModel):
    """Response schema for collection indexing."""

    success: bool = Field(..., description="Whether indexing succeeded")
    message: str = Field(..., description="Status message")
    documents_indexed: int = Field(..., description="Number of documents indexed")


class ChatRequest(BaseModel):
    """Request schema for AI chat."""

    message: str = Field(..., description="User message", min_length=1)
    history: Optional[List[Dict[str, str]]] = Field(
        None, description="Conversation history"
    )


class ChatResponse(BaseModel):
    """Response schema for AI chat."""

    message: str = Field(..., description="AI response")
    model: str = Field(..., description="Model used")
