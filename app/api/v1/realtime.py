"""Real-time updates API using Server-Sent Events (SSE) and WebSockets."""
import asyncio
import uuid
import json
from typing import Optional
from fastapi import APIRouter, Request, Query, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import StreamingResponse

from app.core.events import event_manager, Event
from app.core.dependencies import get_optional_user_id
from app.core.websocket_manager import connection_manager
from app.core.security import decode_token
from app.core.logging import get_logger

logger = get_logger(__name__)


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
    # Generate unique client ID for this connection
    client_id = str(uuid.uuid4())

    # Subscribe to events
    queue = await event_manager.subscribe(collection_name, query_filter, user_id)

    try:
        # Send PB_CONNECT style initial connection event with client ID
        # This follows PocketBase's pattern for client identification
        connect_data = json.dumps({
            "clientId": client_id,
            "status": "connected",
            "subscriptions": {
                "collection": collection_name or "*",
                "hasFilter": query_filter is not None,
            }
        })
        yield f"event: PB_CONNECT\ndata: {connect_data}\n\n"

        # Also send legacy connected event for backwards compatibility
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


@router.websocket("/ws/realtime")
async def websocket_realtime(websocket: WebSocket, token: Optional[str] = Query(None)):
    """
    WebSocket endpoint for real-time updates.
    
    Supports bidirectional communication for subscriptions, presence, and events.
    
    Authentication:
    - Pass token as query parameter: /ws/realtime?token=YOUR_TOKEN
    - Or send auth message after connection: {"action": "auth", "token": "YOUR_TOKEN"}
    
    Client Messages:
    - Subscribe: {"action": "subscribe", "collection": "posts", "filter": {...}}
    - Unsubscribe: {"action": "unsubscribe", "collection": "posts"}
    - Auth: {"action": "auth", "token": "YOUR_TOKEN"}
    - Presence: {"action": "presence", "collection": "posts", "status": "typing"}
    - Ping: {"action": "ping"}
    
    Server Messages:
    - Connected: {"type": "connected", "data": {...}}
    - Event: {"type": "event", "data": {...}}
    - Presence: {"type": "presence", "data": {...}}
    - Error: {"type": "error", "data": {"message": "..."}}
    - Pong: {"type": "pong", "data": {}}
    """
    connection_id = str(uuid.uuid4())
    connection = None
    
    try:
        # Connect
        connection = await connection_manager.connect(websocket, connection_id)
        
        # Authenticate if token provided in query
        if token:
            payload = decode_token(token)
            if payload and "sub" in payload:
                user_id = payload["sub"]
                await connection_manager.authenticate(connection_id, user_id)
                await connection.send_json({
                    "type": "authenticated",
                    "data": {"user_id": user_id},
                    "timestamp": asyncio.get_event_loop().time()
                })
        
        # Message handling loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                action = message.get("action")
                
                if action == "ping":
                    # Heartbeat
                    connection.last_heartbeat = asyncio.get_event_loop().time()
                    await connection.send_json({"type": "pong", "data": {}})
                
                elif action == "auth":
                    # Authenticate connection
                    auth_token = message.get("token")
                    if auth_token:
                        payload = decode_token(auth_token)
                        if payload and "sub" in payload:
                            user_id = payload["sub"]
                            await connection_manager.authenticate(connection_id, user_id)
                            await connection.send_json({
                                "type": "authenticated",
                                "data": {"user_id": user_id}
                            })
                        else:
                            await connection.send_json({
                                "type": "error",
                                "data": {"message": "Invalid token"}
                            })
                
                elif action == "subscribe":
                    # Subscribe to collection
                    collection = message.get("collection")
                    filter_dict = message.get("filter")
                    
                    if collection:
                        await connection_manager.subscribe(
                            connection_id,
                            collection,
                            filter_dict
                        )
                        await connection.send_json({
                            "type": "subscribed",
                            "data": {
                                "collection": collection,
                                "filter": filter_dict
                            }
                        })
                    else:
                        # Subscribe globally
                        await connection_manager.subscribe_global(connection_id)
                        await connection.send_json({
                            "type": "subscribed",
                            "data": {"collection": "*"}
                        })
                
                elif action == "unsubscribe":
                    # Unsubscribe from collection
                    collection = message.get("collection")
                    if collection:
                        await connection_manager.unsubscribe(connection_id, collection)
                        await connection.send_json({
                            "type": "unsubscribed",
                            "data": {"collection": collection}
                        })
                
                elif action == "presence":
                    # Handle presence update (will be implemented with presence service)
                    await connection.send_json({
                        "type": "error",
                        "data": {"message": "Presence not yet implemented"}
                    })
                
                else:
                    await connection.send_json({
                        "type": "error",
                        "data": {"message": f"Unknown action: {action}"}
                    })
            
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await connection.send_json({
                    "type": "error",
                    "data": {"message": "Invalid JSON"}
                })
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                await connection.send_json({
                    "type": "error",
                    "data": {"message": str(e)}
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Cleanup
        if connection:
            await connection_manager.disconnect(connection_id)


@router.get(
    "/realtime/{collection_name}/{record_id}",
    summary="Subscribe to real-time updates (specific record)",
)
async def realtime_record(
    collection_name: str,
    record_id: str,
    request: Request,
    user_id: Optional[str] = Query(None, description="Optional user ID for presence tracking"),
):
    """
    Subscribe to real-time updates for a specific record.

    This endpoint uses Server-Sent Events (SSE) to push updates when the
    specific record is created, updated, or deleted.

    Args:
        collection_name: Name of the collection
        record_id: ID of the record to subscribe to
        user_id: Optional user ID for presence tracking

    Example usage (JavaScript):
    ```javascript
    const eventSource = new EventSource('/api/v1/realtime/posts/abc123');

    eventSource.addEventListener('record.updated', (e) => {
        const data = JSON.parse(e.data);
        console.log('Record updated:', data);
    });

    eventSource.addEventListener('record.deleted', (e) => {
        const data = JSON.parse(e.data);
        console.log('Record deleted:', data);
        eventSource.close(); // Close connection when record is deleted
    });
    ```
    """
    # Create a filter that only matches this specific record
    def record_filter(data):
        return data.get("id") == record_id

    return StreamingResponse(
        event_generator(request, collection_name, record_filter, user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/stats")
async def get_realtime_stats():
    """Get realtime connection statistics."""
    return connection_manager.get_stats()


# ===== Presence REST API =====

@router.get(
    "/presence",
    summary="Get all online users",
    response_model=dict,
)
async def get_presence():
    """
    Get a list of all currently online users.

    Returns presence information for all connected users including:
    - user_id: User's ID
    - user_name: User's display name (if provided)
    - last_seen: Last activity timestamp
    - connections: Number of active connections

    Example response:
    ```json
    {
        "users": [
            {
                "user_id": "user123",
                "user_name": "John Doe",
                "last_seen": "2024-01-15T10:30:00Z",
                "connections": 2
            }
        ],
        "total": 1
    }
    ```
    """
    users = event_manager.get_presence()
    return {
        "users": users,
        "total": len(users)
    }


@router.get(
    "/presence/{user_id}",
    summary="Get specific user's presence",
    response_model=dict,
)
async def get_user_presence(user_id: str):
    """
    Get presence information for a specific user.

    Args:
        user_id: The user ID to check

    Returns:
        Presence information if user is online, or {"online": false} if offline.

    Example response (online):
    ```json
    {
        "online": true,
        "user_id": "user123",
        "user_name": "John Doe",
        "last_seen": "2024-01-15T10:30:00Z",
        "connections": 2
    }
    ```

    Example response (offline):
    ```json
    {
        "online": false,
        "user_id": "user123"
    }
    ```
    """
    presence = event_manager.get_user_presence(user_id)
    if presence:
        return {
            "online": True,
            **presence
        }
    return {
        "online": False,
        "user_id": user_id
    }


@router.get(
    "/presence/collection/{collection_name}",
    summary="Get users viewing a collection",
    response_model=dict,
)
async def get_collection_presence(collection_name: str):
    """
    Get a list of users currently subscribed to a specific collection.

    This is useful for showing who is currently viewing/editing records
    in a collection (collaborative editing awareness).

    Args:
        collection_name: The collection to check

    Returns:
        List of users subscribed to the collection.
    """
    # Get subscribers from WebSocket manager
    stats = connection_manager.get_stats()
    collection_count = stats.get("collection_subscribers", {}).get(collection_name, 0)

    # For detailed user info, we'd need to track this in the connection manager
    # For now, return count and any presence info
    users = []
    for sub in event_manager._subscriptions:
        if sub.collection_name == collection_name and sub.user_id:
            presence = event_manager.get_user_presence(sub.user_id)
            if presence:
                users.append(presence)

    return {
        "collection": collection_name,
        "subscriber_count": collection_count + len(users),
        "users": users
    }
