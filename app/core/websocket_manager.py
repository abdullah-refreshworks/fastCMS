"""WebSocket connection manager for realtime features."""
import asyncio
import json
from typing import Dict, Set, Optional, Any, List
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from collections import defaultdict

from app.core.logging import get_logger
from app.core.events import Event

logger = get_logger(__name__)


class Connection:
    """Represents a WebSocket connection with metadata."""
    
    def __init__(self, websocket: WebSocket, connection_id: str):
        self.websocket = websocket
        self.connection_id = connection_id
        self.user_id: Optional[str] = None
        self.subscriptions: Set[str] = set()
        self.filters: Dict[str, Dict[str, Any]] = {}
        self.last_heartbeat = datetime.utcnow()
        self.authenticated = False
    
    async def send_json(self, data: Dict[str, Any]):
        """Send JSON data to the client."""
        try:
            await self.websocket.send_json(data)
        except Exception as e:
            logger.error(f"Error sending to connection {self.connection_id}: {e}")
            raise
    
    async def send_event(self, event: Event):
        """Send an event to the client."""
        await self.send_json({
            "type": "event",
            "data": event.to_dict(),
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def matches_filter(self, event: Event, collection: str) -> bool:
        """Check if event matches the connection's filter for a collection."""
        if collection not in self.filters:
            return True
        
        filter_dict = self.filters[collection]
        if not filter_dict:
            return True
        
        # Simple filter matching - can be enhanced
        for key, value in filter_dict.items():
            if key in event.data and event.data[key] != value:
                return False
        
        return True


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        # connection_id -> Connection
        self._connections: Dict[str, Connection] = {}
        
        # collection_name -> set of connection_ids
        self._collection_subscribers: Dict[str, Set[str]] = defaultdict(set)
        
        # user_id -> set of connection_ids
        self._user_connections: Dict[str, Set[str]] = defaultdict(set)
        
        # Global subscribers (all events)
        self._global_subscribers: Set[str] = set()
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, connection_id: str) -> Connection:
        """Register a new WebSocket connection."""
        await websocket.accept()
        
        connection = Connection(websocket, connection_id)
        
        async with self._lock:
            self._connections[connection_id] = connection
        
        logger.info(f"WebSocket connected: {connection_id}")
        
        # Send connection confirmation
        await connection.send_json({
            "type": "connected",
            "data": {
                "connection_id": connection_id,
                "status": "connected"
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return connection
    
    async def disconnect(self, connection_id: str):
        """Unregister a WebSocket connection."""
        async with self._lock:
            connection = self._connections.get(connection_id)
            if not connection:
                return
            
            # Remove from all subscriptions
            for collection in connection.subscriptions:
                self._collection_subscribers[collection].discard(connection_id)
                if not self._collection_subscribers[collection]:
                    del self._collection_subscribers[collection]
            
            # Remove from global subscribers
            self._global_subscribers.discard(connection_id)
            
            # Remove from user connections
            if connection.user_id:
                self._user_connections[connection.user_id].discard(connection_id)
                if not self._user_connections[connection.user_id]:
                    del self._user_connections[connection.user_id]
            
            # Remove connection
            del self._connections[connection_id]
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def authenticate(self, connection_id: str, user_id: str):
        """Authenticate a connection with a user ID."""
        async with self._lock:
            connection = self._connections.get(connection_id)
            if connection:
                connection.user_id = user_id
                connection.authenticated = True
                self._user_connections[user_id].add(connection_id)
                logger.info(f"Connection {connection_id} authenticated as user {user_id}")
    
    async def subscribe(
        self,
        connection_id: str,
        collection: str,
        filter_dict: Optional[Dict[str, Any]] = None
    ):
        """Subscribe a connection to a collection."""
        async with self._lock:
            connection = self._connections.get(connection_id)
            if not connection:
                return
            
            connection.subscriptions.add(collection)
            if filter_dict:
                connection.filters[collection] = filter_dict
            
            self._collection_subscribers[collection].add(connection_id)
        
        logger.info(f"Connection {connection_id} subscribed to {collection}")
    
    async def unsubscribe(self, connection_id: str, collection: str):
        """Unsubscribe a connection from a collection."""
        async with self._lock:
            connection = self._connections.get(connection_id)
            if not connection:
                return
            
            connection.subscriptions.discard(collection)
            connection.filters.pop(collection, None)
            
            self._collection_subscribers[collection].discard(connection_id)
            if not self._collection_subscribers[collection]:
                del self._collection_subscribers[collection]
        
        logger.info(f"Connection {connection_id} unsubscribed from {collection}")
    
    async def subscribe_global(self, connection_id: str):
        """Subscribe a connection to all events."""
        async with self._lock:
            self._global_subscribers.add(connection_id)
        
        logger.info(f"Connection {connection_id} subscribed globally")
    
    async def broadcast_event(self, event: Event):
        """Broadcast an event to all relevant subscribers."""
        # Get subscribers for this collection
        collection_subs = self._collection_subscribers.get(event.collection_name, set())
        
        # Combine with global subscribers
        all_subs = collection_subs | self._global_subscribers
        
        # Send to each subscriber
        disconnected = []
        for connection_id in all_subs:
            connection = self._connections.get(connection_id)
            if not connection:
                disconnected.append(connection_id)
                continue
            
            # Check if event matches filter
            if event.collection_name in connection.subscriptions:
                if not connection.matches_filter(event, event.collection_name):
                    continue
            
            try:
                await connection.send_event(event)
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_id}: {e}")
                disconnected.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected:
            await self.disconnect(connection_id)
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send a message to all connections of a specific user."""
        connection_ids = self._user_connections.get(user_id, set()).copy()
        
        disconnected = []
        for connection_id in connection_ids:
            connection = self._connections.get(connection_id)
            if not connection:
                disconnected.append(connection_id)
                continue
            
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected:
            await self.disconnect(connection_id)
    
    async def broadcast_to_collection(
        self,
        collection: str,
        message: Dict[str, Any]
    ):
        """Broadcast a message to all subscribers of a collection."""
        connection_ids = self._collection_subscribers.get(collection, set()).copy()
        
        disconnected = []
        for connection_id in connection_ids:
            connection = self._connections.get(connection_id)
            if not connection:
                disconnected.append(connection_id)
                continue
            
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected:
            await self.disconnect(connection_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "total_connections": len(self._connections),
            "authenticated_connections": sum(1 for c in self._connections.values() if c.authenticated),
            "collection_subscribers": {
                collection: len(subs)
                for collection, subs in self._collection_subscribers.items()
            },
            "global_subscribers": len(self._global_subscribers),
            "unique_users": len(self._user_connections)
        }
    
    async def heartbeat_check(self, max_idle_seconds: int = 300):
        """Check for idle connections and disconnect them."""
        now = datetime.utcnow()
        to_disconnect = []
        
        for connection_id, connection in self._connections.items():
            idle_seconds = (now - connection.last_heartbeat).total_seconds()
            if idle_seconds > max_idle_seconds:
                to_disconnect.append(connection_id)
        
        for connection_id in to_disconnect:
            logger.warning(f"Disconnecting idle connection: {connection_id}")
            await self.disconnect(connection_id)


# Global connection manager instance
connection_manager = ConnectionManager()
