"""
Search API endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.services.search_service import SearchService
from app.core.security import require_admin

router = APIRouter()


class CreateSearchIndexRequest(BaseModel):
    collection_name: str
    fields: List[str]


class SearchIndexResponse(BaseModel):
    id: str
    collection_name: str
    indexed_fields: List[str]
    created: str
    updated: str


class SearchRequest(BaseModel):
    query: str
    limit: int = 20
    offset: int = 0


@router.post("/indexes", dependencies=[Depends(require_admin)])
async def create_search_index(
    request: CreateSearchIndexRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create full-text search index for a collection (Admin only)
    """
    service = SearchService(db)
    try:
        index = await service.create_search_index(request.collection_name, request.fields)
        import json

        return {
            "id": index.id,
            "collection_name": index.collection_name,
            "indexed_fields": json.loads(index.indexed_fields),
            "created": index.created.isoformat(),
            "updated": index.updated.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create search index: {str(e)}")


@router.delete("/indexes/{collection_name}", dependencies=[Depends(require_admin)])
async def delete_search_index(
    collection_name: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete full-text search index for a collection (Admin only)
    """
    service = SearchService(db)
    try:
        await service.delete_search_index(collection_name)
        return {"message": f"Search index for {collection_name} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete search index: {str(e)}")


@router.get("/indexes")
async def list_search_indexes(db: AsyncSession = Depends(get_db)):
    """
    List all search indexes
    """
    service = SearchService(db)
    indexes = await service.list_search_indexes()
    import json

    return [
        {
            "id": idx.id,
            "collection_name": idx.collection_name,
            "indexed_fields": json.loads(idx.indexed_fields),
            "created": idx.created.isoformat(),
            "updated": idx.updated.isoformat(),
        }
        for idx in indexes
    ]


@router.get("/indexes/{collection_name}")
async def get_search_index(
    collection_name: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get search index details
    """
    service = SearchService(db)
    index = await service.get_search_index(collection_name)
    if not index:
        raise HTTPException(status_code=404, detail="Search index not found")

    import json

    return {
        "id": index.id,
        "collection_name": index.collection_name,
        "indexed_fields": json.loads(index.indexed_fields),
        "created": index.created.isoformat(),
        "updated": index.updated.isoformat(),
    }


@router.post("/indexes/{collection_name}/reindex", dependencies=[Depends(require_admin)])
async def reindex_collection(
    collection_name: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Rebuild search index for a collection (Admin only)
    """
    service = SearchService(db)
    try:
        count = await service.reindex_collection(collection_name)
        return {
            "message": f"Reindexed {count} records",
            "collection_name": collection_name,
            "records_indexed": count,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reindex: {str(e)}")


@router.get("/{collection_name}")
async def search_collection(
    collection_name: str,
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Perform full-text search on a collection
    """
    service = SearchService(db)
    try:
        results = await service.search(collection_name, q, limit, offset)
        return {
            "items": results,
            "query": q,
            "limit": limit,
            "offset": offset,
            "count": len(results),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
