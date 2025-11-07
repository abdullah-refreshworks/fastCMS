"""API endpoints for AI-powered features."""

from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import UserContext, require_auth
from app.core.exceptions import BadRequestException, NotFoundException
from app.db.repositories.collection import CollectionRepository
from app.db.repositories.record import RecordRepository
from app.db.session import get_db
from app.schemas.ai import (
    ChatRequest,
    ChatResponse,
    EnrichDataRequest,
    EnrichDataResponse,
    GenerateContentRequest,
    GenerateContentResponse,
    GenerateSchemaRequest,
    GenerateSchemaResponse,
    IndexCollectionRequest,
    IndexCollectionResponse,
    NaturalLanguageQueryRequest,
    NaturalLanguageQueryResponse,
    SemanticSearchRequest,
    SemanticSearchResponse,
    SemanticSearchResult,
)
from app.services.ai_service import AIService
from app.services.vector_store_service import VectorStoreService

router = APIRouter()


def check_ai_enabled() -> None:
    """Check if AI features are enabled."""
    if not settings.AI_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI features are not enabled. Set AI_ENABLED=true in configuration.",
        )

    if settings.AI_PROVIDER == "openai" and not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI API key not configured",
        )
    elif settings.AI_PROVIDER == "anthropic" and not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Anthropic API key not configured",
        )


@router.post(
    "/generate",
    response_model=GenerateContentResponse,
    summary="Generate content with AI",
    dependencies=[Depends(check_ai_enabled)],
)
async def generate_content(
    data: GenerateContentRequest,
    user_context: UserContext = Depends(require_auth),
) -> GenerateContentResponse:
    """
    Generate content using AI based on a prompt.
    Requires authentication.
    """
    ai_service = AIService()

    try:
        content = await ai_service.generate_content(
            prompt=data.prompt,
            context=data.context,
            max_tokens=data.max_tokens,
        )

        return GenerateContentResponse(content=content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content generation failed: {str(e)}",
        )


@router.post(
    "/generate/stream",
    summary="Stream generated content",
    dependencies=[Depends(check_ai_enabled)],
)
async def generate_content_stream(
    data: GenerateContentRequest,
    user_context: UserContext = Depends(require_auth),
) -> StreamingResponse:
    """
    Stream generated content token by token.
    Requires authentication.
    """
    ai_service = AIService()

    async def generate() -> AsyncIterator[str]:
        """Generate SSE stream."""
        try:
            async for chunk in ai_service.generate_content_stream(
                prompt=data.prompt,
                context=data.context,
            ):
                # Format as Server-Sent Event
                yield f"data: {chunk}\n\n"
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/query/natural-language",
    response_model=NaturalLanguageQueryResponse,
    summary="Convert natural language to API filter",
    dependencies=[Depends(check_ai_enabled)],
)
async def natural_language_query(
    data: NaturalLanguageQueryRequest,
    db: AsyncSession = Depends(get_db),
    user_context: UserContext = Depends(require_auth),
) -> NaturalLanguageQueryResponse:
    """
    Convert natural language query to FastCMS filter syntax.
    Requires authentication.
    """
    # Get collection schema
    collection_repo = CollectionRepository(db)
    collection = await collection_repo.get_by_name(data.collection_name)

    if not collection:
        raise NotFoundException(f"Collection '{data.collection_name}' not found")

    ai_service = AIService()

    try:
        filter_expr = await ai_service.natural_language_to_filter(
            query=data.query,
            collection_schema=collection.schema,
        )

        return NaturalLanguageQueryResponse(
            filter_expression=filter_expr,
            explanation=f"Converted query: '{data.query}'" if filter_expr else None,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query conversion failed: {str(e)}",
        )


@router.post(
    "/enrich",
    response_model=EnrichDataResponse,
    summary="Enrich data with AI",
    dependencies=[Depends(check_ai_enabled)],
)
async def enrich_data(
    data: EnrichDataRequest,
    user_context: UserContext = Depends(require_auth),
) -> EnrichDataResponse:
    """
    Enrich or validate data using AI.
    Requires authentication.
    """
    ai_service = AIService()

    try:
        enriched = await ai_service.enrich_data(
            data=data.data,
            instructions=data.instructions,
        )

        return EnrichDataResponse(enriched_data=enriched)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data enrichment failed: {str(e)}",
        )


@router.post(
    "/schema/generate",
    response_model=GenerateSchemaResponse,
    summary="Generate collection schema with AI",
    dependencies=[Depends(check_ai_enabled)],
)
async def generate_schema(
    data: GenerateSchemaRequest,
    user_context: UserContext = Depends(require_auth),
) -> GenerateSchemaResponse:
    """
    Generate a collection schema based on natural language description.
    Requires authentication.
    """
    ai_service = AIService()

    try:
        schema = await ai_service.generate_schema_suggestion(data.description)

        return GenerateSchemaResponse(schema=schema)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Schema generation failed: {str(e)}",
        )


@router.post(
    "/search/semantic",
    response_model=SemanticSearchResponse,
    summary="Semantic search in collection",
    dependencies=[Depends(check_ai_enabled)],
)
async def semantic_search(
    data: SemanticSearchRequest,
    db: AsyncSession = Depends(get_db),
    user_context: UserContext = Depends(require_auth),
) -> SemanticSearchResponse:
    """
    Perform semantic search using vector embeddings.
    Requires authentication and collection to be indexed.
    """
    # Verify collection exists
    collection_repo = CollectionRepository(db)
    collection = await collection_repo.get_by_name(data.collection_name)

    if not collection:
        raise NotFoundException(f"Collection '{data.collection_name}' not found")

    vector_service = VectorStoreService(data.collection_name)

    try:
        await vector_service.load_or_create()
        results = await vector_service.search(
            query=data.query,
            k=data.k,
            score_threshold=data.score_threshold,
        )

        return SemanticSearchResponse(
            results=[
                SemanticSearchResult(metadata=metadata, similarity=similarity)
                for metadata, similarity in results
            ],
            total=len(results),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic search failed: {str(e)}",
        )


@router.post(
    "/index/collection",
    response_model=IndexCollectionResponse,
    summary="Index collection for semantic search",
    dependencies=[Depends(check_ai_enabled)],
)
async def index_collection(
    data: IndexCollectionRequest,
    db: AsyncSession = Depends(get_db),
    user_context: UserContext = Depends(require_auth),
) -> IndexCollectionResponse:
    """
    Index a collection's records for semantic search.
    Requires authentication and admin role.
    """
    # Only admins can index collections
    if user_context.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required for indexing",
        )

    # Verify collection exists
    collection_repo = CollectionRepository(db)
    collection = await collection_repo.get_by_name(data.collection_name)

    if not collection:
        raise NotFoundException(f"Collection '{data.collection_name}' not found")

    # Get all records
    record_repo = RecordRepository(db, data.collection_name)
    records = await record_repo.get_all()

    # Convert records to dicts
    documents = []
    for record in records:
        doc = {"id": record.id}
        for key in dir(record):
            if not key.startswith("_") and key not in [
                "id",
                "created",
                "updated",
                "metadata",
                "registry",
            ]:
                value = getattr(record, key)
                if not callable(value):
                    doc[key] = value
        documents.append(doc)

    # Index documents
    vector_service = VectorStoreService(data.collection_name)

    try:
        if data.rebuild:
            await vector_service.rebuild_index(documents)
        else:
            await vector_service.load_or_create()
            await vector_service.add_documents(documents)

        return IndexCollectionResponse(
            success=True,
            message=f"Collection '{data.collection_name}' indexed successfully",
            documents_indexed=len(documents),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {str(e)}",
        )


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat with AI assistant",
    dependencies=[Depends(check_ai_enabled)],
)
async def chat(
    data: ChatRequest,
    user_context: UserContext = Depends(require_auth),
) -> ChatResponse:
    """
    Chat with AI assistant about FastCMS usage.
    Requires authentication.
    """
    ai_service = AIService()

    try:
        response = await ai_service.chat(
            message=data.message,
            history=data.history,
        )

        return ChatResponse(
            message=response,
            model=settings.AI_PROVIDER,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}",
        )
