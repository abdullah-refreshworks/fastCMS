"""Event manager for real-time updates using Server-Sent Events (SSE)."""
import asyncio
import json
from typing import Dict, Set, Optional, Any, Callable
from datetime import datetime
from enum import Enum
import re

from app.core.logging import get_logger

logger = get_logger(__name__)


class EventType(str, Enum):
    """Types of events that can be broadcast."""

    RECORD_CREATED = "record.created"
    RECORD_UPDATED = "record.updated"
    RECORD_DELETED = "record.deleted"
    COLLECTION_CREATED = "collection.created"
    COLLECTION_UPDATED = "collection.updated"
    COLLECTION_DELETED = "collection.deleted"
    USER_JOINED = "user.joined"
    USER_LEFT = "user.left"
    PRESENCE_UPDATE = "presence.update"


class Event:
    """Event data structure."""

    def __init__(
        self,
        event_type: EventType,
        collection_name: str,
        data: Dict[str, Any],
        record_id: Optional[str] = None,
    ):
        self.event_type = event_type
        self.collection_name = collection_name
        self.data = data
        self.record_id = record_id
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "type": self.event_type,
            "collection": self.collection_name,
            "record_id": self.record_id,
            "data": self.data,
            "timestamp": self.timestamp,
        }

    def to_sse_message(self) -> str:
        """Format as SSE message."""
        data = json.dumps(self.to_dict())
        return f"event: {self.event_type}\ndata: {data}\n\n"


class Subscription:
    """Represents a subscription with optional query filter."""

    def __init__(
        self,
        queue: asyncio.Queue,
        collection_name: Optional[str] = None,
        query_filter: Optional[Callable[[Dict[str, Any]], bool]] = None,
        user_id: Optional[str] = None,
        user_role: str = "user",
    ):
        self.queue = queue
        self.collection_name = collection_name
        self.query_filter = query_filter
        self.user_id = user_id
        self.user_role = user_role
        self.created_at = datetime.utcnow()


class PresenceInfo:
    """User presence information."""

    def __init__(self, user_id: str, user_name: Optional[str] = None):
        self.user_id = user_id
        self.user_name = user_name
        self.last_seen = datetime.utcnow()
        self.connections = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "last_seen": self.last_seen.isoformat(),
            "connections": self.connections,
        }


class EventManager:
    """Manages SSE connections and event broadcasting."""

    def __init__(self):
        # All subscriptions with query filters
        self._subscriptions: Set[Subscription] = set()
        # Presence tracking: user_id -> PresenceInfo
        self._presence: Dict[str, PresenceInfo] = {}

    async def subscribe(
        self,
        collection_name: Optional[str] = None,
        query_filter: Optional[Callable[[Dict[str, Any]], bool]] = None,
        user_id: Optional[str] = None,
        user_role: str = "user",
    ) -> asyncio.Queue:
        """
        Subscribe to events with optional query filter.

        Args:
            collection_name: Subscribe to specific collection, or None for all events
            query_filter: Optional filter function to filter events
            user_id: Optional user ID for presence tracking
            user_role: User role for permission checking (admin, user, etc.)

        Returns:
            Queue that will receive events
        """
        queue = asyncio.Queue()
        subscription = Subscription(queue, collection_name, query_filter, user_id, user_role)
        self._subscriptions.add(subscription)

        # Update presence if user_id provided
        if user_id:
            await self._update_presence(user_id, joined=True)

        return queue

    async def unsubscribe(
        self, queue: asyncio.Queue, user_id: Optional[str] = None
    ):
        """Unsubscribe from events."""
        # Find and remove subscription
        subscription_to_remove = None
        for sub in self._subscriptions:
            if sub.queue == queue:
                subscription_to_remove = sub
                break

        if subscription_to_remove:
            self._subscriptions.discard(subscription_to_remove)

            # Update presence if user_id provided
            if user_id:
                await self._update_presence(user_id, joined=False)

    async def broadcast(self, event: Event):
        """
        Broadcast an event to all relevant subscribers and trigger webhooks.

        Args:
            event: Event to broadcast
        """
        dead_subscriptions = set()

        # Send to all matching SSE subscribers
        for subscription in self._subscriptions.copy():
            try:
                # Check if this subscription should receive the event
                if self._subscription_matches(subscription, event):
                    await subscription.queue.put(event)
            except Exception as e:
                logger.warning(f"Error sending to subscriber: {e}")
                dead_subscriptions.add(subscription)

        # Clean up dead subscriptions
        for dead_sub in dead_subscriptions:
            self._subscriptions.discard(dead_sub)

        # Broadcast to WebSocket connections
        try:
            from app.core.websocket_manager import connection_manager
            await connection_manager.broadcast_event(event)
        except Exception as e:
            logger.error(f"Error broadcasting to WebSocket: {e}")

        # Trigger webhooks asynchronously (fire and forget)
        asyncio.create_task(self._trigger_webhooks(event))

    def _subscription_matches(self, sub: Subscription, event: Event) -> bool:
        """Check if a subscription should receive this event."""
        # Check collection filter
        if sub.collection_name and sub.collection_name != event.collection_name:
            return False

        # Check query filter
        if sub.query_filter:
            try:
                if not sub.query_filter(event.data):
                    return False
            except Exception as e:
                logger.warning(f"Query filter error: {e}")
                return False

        return True

    async def _check_permission(
        self,
        sub: Subscription,
        event: Event,
        collection_rules: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Check if subscriber has permission to see this event.

        Args:
            sub: The subscription
            event: The event to check
            collection_rules: Collection's access rules (list_rule, view_rule)

        Returns:
            True if subscriber can see the event
        """
        # System/internal events always pass
        if event.collection_name.startswith("__"):
            return True

        # Admins can see everything
        if sub.user_role == "admin":
            return True

        # If no rules provided, skip permission check
        if not collection_rules:
            return True

        # Get the appropriate rule based on event type
        # For record events, use list_rule (determines who can see records)
        rule = collection_rules.get("list_rule")

        if not rule:
            # No rule means public access
            return True

        # Empty string rule means only admins (already handled above)
        if rule.strip() == "":
            return False

        # Try to evaluate the rule
        try:
            from app.core.access_control import access_control, AccessContext

            context = AccessContext(
                user_id=sub.user_id,
                user_role=sub.user_role,
                record_data=event.data,
            )

            # Check if the rule passes
            return access_control.evaluate(rule, context)
        except Exception as e:
            logger.warning(f"Permission check failed: {e}")
            # Default to denying access on error
            return False

    async def broadcast_with_permissions(
        self,
        event: Event,
        collection_rules: Optional[Dict[str, str]] = None
    ):
        """
        Broadcast an event with permission checking.

        Args:
            event: Event to broadcast
            collection_rules: Collection's access rules for permission checking
        """
        dead_subscriptions = set()

        # Send to all matching SSE subscribers
        for subscription in self._subscriptions.copy():
            try:
                # Check if this subscription should receive the event
                if self._subscription_matches(subscription, event):
                    # Check permissions
                    if await self._check_permission(subscription, event, collection_rules):
                        await subscription.queue.put(event)
            except Exception as e:
                logger.warning(f"Error sending to subscriber: {e}")
                dead_subscriptions.add(subscription)

        # Clean up dead subscriptions
        for dead_sub in dead_subscriptions:
            self._subscriptions.discard(dead_sub)

        # Broadcast to WebSocket connections
        try:
            from app.core.websocket_manager import connection_manager
            await connection_manager.broadcast_event(event)
        except Exception as e:
            logger.error(f"Error broadcasting to WebSocket: {e}")

        # Trigger webhooks asynchronously (fire and forget)
        asyncio.create_task(self._trigger_webhooks(event))

    def get_subscriber_count(self, collection_name: Optional[str] = None) -> int:
        """Get number of active subscribers."""
        if collection_name:
            count = 0
            for sub in self._subscriptions:
                if sub.collection_name == collection_name:
                    count += 1
            return count
        return len(self._subscriptions)

    async def _update_presence(self, user_id: str, joined: bool, user_name: Optional[str] = None):
        """Update user presence and broadcast presence event."""
        if joined:
            if user_id in self._presence:
                # User already present, increment connection count
                self._presence[user_id].connections += 1
                self._presence[user_id].last_seen = datetime.utcnow()
            else:
                # New user joining
                self._presence[user_id] = PresenceInfo(user_id, user_name)
                # Broadcast user joined event
                event = Event(
                    event_type=EventType.USER_JOINED,
                    collection_name="__presence__",
                    data=self._presence[user_id].to_dict(),
                )
                await self.broadcast(event)
        else:
            if user_id in self._presence:
                # Decrement connection count
                self._presence[user_id].connections -= 1
                self._presence[user_id].last_seen = datetime.utcnow()

                # If no more connections, remove user
                if self._presence[user_id].connections <= 0:
                    presence_data = self._presence[user_id].to_dict()
                    del self._presence[user_id]
                    # Broadcast user left event
                    event = Event(
                        event_type=EventType.USER_LEFT,
                        collection_name="__presence__",
                        data=presence_data,
                    )
                    await self.broadcast(event)

    def get_presence(self) -> list[Dict[str, Any]]:
        """Get all active users."""
        return [info.to_dict() for info in self._presence.values()]

    def get_user_presence(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get presence info for a specific user."""
        if user_id in self._presence:
            return self._presence[user_id].to_dict()
        return None

    async def _trigger_webhooks(self, event: Event):
        """Trigger webhook deliveries for an event (internal)."""
        try:
            from app.db.session import async_session_maker
            from app.services.webhook_service import WebhookService

            # Create a new database session for webhook delivery
            async with async_session_maker() as db:
                service = WebhookService(db)
                await service.deliver_event(
                    collection_name=event.collection_name,
                    event_type=event.event_type,
                    record_id=event.record_id or "",
                    data=event.data,
                )
        except Exception as e:
            logger.error(f"Error triggering webhooks: {str(e)}")


# Global event manager instance
event_manager = EventManager()
