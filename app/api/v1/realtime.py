"""Real-time updates API using Server-Sent Events (SSE)."""
import asyncio
import json
from typing import Optional, Dict, Any
from fastapi import APIRouter, Request, Query, Depends
from fastapi.responses import StreamingResponse, JSONResponse

from app.core.events import event_manager, Event
from app.core.dependencies import get_optional_user_id


router = APIRouter()


def parse_query_filter(query: Optional[str]) -> Optional[callable]:
    """
    Parse a simple query filter into a callable.

    Supports simple filters like:
    - field=value (equality)
    - field>value (greater than)
    - field<value (less than)
    - field!=value (not equal)

    Args:
        query: Query string

    Returns:
        Callable filter function or None
    """
    if not query:
        return None

    try:
        # Parse simple query format: field operator value
        if "!=" in query:
            field, value = query.split("!=", 1)
            return lambda data: str(data.get(field.strip())) != value.strip()
        elif ">=" in query:
            field, value = query.split(">=", 1)
            return lambda data: float(data.get(field.strip(), 0)) >= float(value.strip())
        elif "<=" in query:
            field, value = query.split("<=", 1)
            return lambda data: float(data.get(field.strip(), 0)) <= float(value.strip())
        elif ">" in query:
            field, value = query.split(">", 1)
            return lambda data: float(data.get(field.strip(), 0)) > float(value.strip())
        elif "<" in query:
            field, value = query.split("<", 1)
            return lambda data: float(data.get(field.strip(), 0)) < float(value.strip())
        elif "=" in query:
            field, value = query.split("=", 1)
            return lambda data: str(data.get(field.strip())) == value.strip()
    except Exception:
        pass

    return None


async def event_generator(
    request: Request,
    collection_name: Optional[str] = None,
    query_filter: Optional[callable] = None,
    user_id: Optional[str] = None,
):
    """
    Generate Server-Sent Events.

    Args:
        request: FastAPI request (to detect client disconnect)
        collection_name: Optional collection to subscribe to
        query_filter: Optional filter function
        user_id: Optional user ID for presence tracking

    Yields:
        SSE formatted messages
    """
    # Subscribe to events
    queue = await event_manager.subscribe(collection_name, query_filter, user_id)

    try:
        # Send initial connection message
        yield "event: connected\ndata: {\"status\": \"connected\"}\n\n"

        while True:
            # Check if client is still connected
            if await request.is_disconnected():
                break

            try:
                # Wait for events with timeout to allow disconnect detection
                event: Event = await asyncio.wait_for(queue.get(), timeout=1.0)
                yield event.to_sse_message()
            except asyncio.TimeoutError:
                # Send keep-alive comment to prevent connection timeout
                yield ": keep-alive\n\n"
                continue

    finally:
        # Cleanup on disconnect
        await event_manager.unsubscribe(queue, user_id)


@router.get(
    "/realtime",
    summary="Subscribe to real-time updates (all collections)",
)
async def realtime_all(
    request: Request,
    user_id: Optional[str] = Query(None, description="Optional user ID for presence tracking"),
    query: Optional[str] = Query(None, description="Optional query filter (e.g., status=published)"),
):
    """
    Subscribe to real-time updates for all collections with optional Live Query filtering.

    This endpoint uses Server-Sent Events (SSE) to push updates to the client.

    Args:
        user_id: Optional user ID for presence tracking
        query: Optional query filter to receive only matching events
               Supports: field=value, field!=value, field>value, field<value

    Example usage (JavaScript):
    ```javascript
    // Basic subscription
    const eventSource = new EventSource('/api/v1/realtime');

    // With user tracking
    const eventSource = new EventSource('/api/v1/realtime?user_id=user123');

    // With live query filter (only published posts)
    const eventSource = new EventSource('/api/v1/realtime?query=status=published');

    eventSource.addEventListener('record.created', (e) => {
        const data = JSON.parse(e.data);
        console.log('Record created:', data);
    });

    eventSource.addEventListener('record.updated', (e) => {
        const data = JSON.parse(e.data);
        console.log('Record updated:', data);
    });

    eventSource.addEventListener('record.deleted', (e) => {
        const data = JSON.parse(e.data);
        console.log('Record deleted:', data);
    });

    // Listen to presence events
    eventSource.addEventListener('user.joined', (e) => {
        const data = JSON.parse(e.data);
        console.log('User joined:', data);
    });

    eventSource.addEventListener('user.left', (e) => {
        const data = JSON.parse(e.data);
        console.log('User left:', data);
    });
    ```
    """
    query_filter = parse_query_filter(query)
    return StreamingResponse(
        event_generator(request, None, query_filter, user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get(
    "/realtime/{collection_name}",
    summary="Subscribe to real-time updates (specific collection)",
)
async def realtime_collection(
    collection_name: str,
    request: Request,
    user_id: Optional[str] = Query(None, description="Optional user ID for presence tracking"),
    query: Optional[str] = Query(None, description="Optional query filter (e.g., status=published)"),
):
    """
    Subscribe to real-time updates for a specific collection with optional Live Query filtering.

    This endpoint uses Server-Sent Events (SSE) to push updates to the client.

    Args:
        collection_name: Name of the collection to subscribe to
        user_id: Optional user ID for presence tracking
        query: Optional query filter to receive only matching events
               Supports: field=value, field!=value, field>value, field<value

    Example usage (JavaScript):
    ```javascript
    // Basic subscription
    const eventSource = new EventSource('/api/v1/realtime/posts');

    // With user tracking
    const eventSource = new EventSource('/api/v1/realtime/posts?user_id=user123');

    // With live query filter (only published posts)
    const eventSource = new EventSource('/api/v1/realtime/posts?query=status=published');

    // With multiple filters (price > 100)
    const eventSource = new EventSource('/api/v1/realtime/products?query=price>100');

    eventSource.addEventListener('record.created', (e) => {
        const data = JSON.parse(e.data);
        console.log('New post created:', data);
    });

    eventSource.addEventListener('record.updated', (e) => {
        const data = JSON.parse(e.data);
        console.log('Post updated:', data);
    });

    eventSource.addEventListener('record.deleted', (e) => {
        const data = JSON.parse(e.data);
        console.log('Post deleted:', data);
    });
    ```
    """
    query_filter = parse_query_filter(query)
    return StreamingResponse(
        event_generator(request, collection_name, query_filter, user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get(
    "/presence",
    summary="Get active users",
    response_model=Dict[str, Any],
)
async def get_presence():
    """
    Get all currently active users.

    Returns list of users currently connected to real-time endpoints.

    Example usage (JavaScript):
    ```javascript
    const response = await fetch('/api/v1/presence');
    const data = await response.json();
    console.log('Active users:', data.users);
    ```

    Example usage (curl):
    ```bash
    curl http://localhost:8000/api/v1/presence
    ```
    """
    presence = event_manager.get_presence()
    return {
        "users": presence,
        "count": len(presence),
    }


@router.get(
    "/presence/{user_id}",
    summary="Get user presence",
    response_model=Dict[str, Any],
)
async def get_user_presence(user_id: str):
    """
    Get presence information for a specific user.

    Args:
        user_id: User ID to check

    Returns user presence info if user is active, otherwise null.

    Example usage (JavaScript):
    ```javascript
    const response = await fetch('/api/v1/presence/user123');
    const data = await response.json();
    if (data.presence) {
        console.log('User is online:', data.presence);
    } else {
        console.log('User is offline');
    }
    ```
    """
    presence = event_manager.get_user_presence(user_id)
    return {
        "user_id": user_id,
        "presence": presence,
        "online": presence is not None,
    }
