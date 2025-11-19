"""
Schema definitions for view collections.
View collections are virtual collections that compute data from other collections.
"""

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


class ViewJoin(BaseModel):
    """Join configuration for view queries."""

    type: Literal["LEFT", "RIGHT", "INNER", "OUTER"] = Field(
        default="LEFT",
        description="Type of join"
    )
    collection: str = Field(..., description="Collection to join with")
    on: str = Field(..., description="Join condition (e.g., 'posts.id = comments.post_id')")
    alias: Optional[str] = Field(None, description="Alias for the joined collection")


class ViewAggregation(BaseModel):
    """Aggregation function configuration."""

    function: Literal["COUNT", "SUM", "AVG", "MIN", "MAX"] = Field(
        ...,
        description="Aggregation function"
    )
    field: str = Field(..., description="Field to aggregate")
    alias: str = Field(..., description="Alias for the result")


class ViewSelect(BaseModel):
    """Field selection configuration."""

    field: str = Field(..., description="Field path (e.g., 'posts.title' or 'COUNT(comments.id)')")
    alias: Optional[str] = Field(None, description="Alias for the field")
    aggregation: Optional[ViewAggregation] = Field(None, description="Aggregation function if applicable")


class ViewQuery(BaseModel):
    """Query definition for view collections."""

    source: str = Field(..., description="Primary source collection")
    select: List[Union[str, ViewSelect]] = Field(
        default_factory=list,
        description="Fields to select (can be simple strings or ViewSelect objects)"
    )
    joins: List[ViewJoin] = Field(
        default_factory=list,
        description="Join configurations"
    )
    where: Optional[str] = Field(None, description="Filter condition (SQL-like)")
    group_by: List[str] = Field(
        default_factory=list,
        description="Fields to group by"
    )
    order_by: List[str] = Field(
        default_factory=list,
        description="Fields to order by (prefix with - for descending)"
    )
    limit: Optional[int] = Field(None, description="Maximum number of results")


class ViewOptions(BaseModel):
    """Options for view collections."""

    query: ViewQuery = Field(..., description="Query definition for the view")
    cache_ttl: Optional[int] = Field(
        default=300,
        description="Cache time-to-live in seconds (0 to disable caching)"
    )
    refresh_on_write: bool = Field(
        default=False,
        description="Whether to refresh cache when source collections are modified"
    )


class ViewCollectionCreate(BaseModel):
    """Schema for creating a view collection."""

    name: str = Field(..., min_length=1, max_length=100, description="Collection name")
    options: ViewOptions = Field(..., description="View configuration")
    list_rule: Optional[str] = Field(None, description="List access rule")
    view_rule: Optional[str] = Field(None, description="View access rule")


class ViewResult(BaseModel):
    """Single result from a view collection."""

    data: Dict[str, Any] = Field(..., description="Result data")


class ViewResultList(BaseModel):
    """List of results from a view collection."""

    items: List[Dict[str, Any]] = Field(..., description="Result items")
    total: int = Field(..., description="Total number of results")
    page: int = Field(default=1, description="Current page number")
    per_page: int = Field(default=30, description="Items per page")
