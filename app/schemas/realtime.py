"""Realtime schemas for WebSocket messages."""
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field


class SubscribeMessage(BaseModel):
    """Client message to subscribe to a collection."""
    action: str = Field(..., description="Action type: 'subscribe'")
    collection: str = Field(..., description="Collection name to subscribe to")
    filter: Optional[Dict[str, Any]] = Field(None, description="Optional filter for events")


class UnsubscribeMessage(BaseModel):
    """Client message to unsubscribe from a collection."""
    action: str = Field(..., description="Action type: 'unsubscribe'")
    collection: str = Field(..., description="Collection name to unsubscribe from")


class AuthMessage(BaseModel):
    """Client message to authenticate the connection."""
    action: str = Field(..., description="Action type: 'auth'")
    token: str = Field(..., description="JWT access token")


class PresenceMessage(BaseModel):
    """Client message to update presence status."""
    action: str = Field(..., description="Action type: 'presence'")
    collection: str = Field(..., description="Collection name")
    status: str = Field(..., description="Presence status: 'typing', 'idle', etc.")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional presence data")


class ClientMessage(BaseModel):
    """Union of all possible client messages."""
    action: str
    collection: Optional[str] = None
    token: Optional[str] = None
    filter: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class ServerMessage(BaseModel):
    """Server message sent to clients."""
    type: str = Field(..., description="Message type: 'event', 'presence', 'error', 'connected'")
    data: Dict[str, Any] = Field(..., description="Message payload")
    timestamp: Optional[str] = Field(None, description="ISO timestamp")


class PresenceUpdate(BaseModel):
    """Presence update data."""
    user_id: str
    collection: str
    status: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str
