# Real-time Features

FastCMS provides a production-ready real-time engine using WebSockets and a Pub/Sub backend. This architecture enables:

- **Horizontal Scaling**: Run multiple server instances behind a load balancer
- **Low Latency**: WebSocket connections provide instant event delivery
- **Filtered Subscriptions**: Subscribe to specific data with filters (live queries)
- **Presence Tracking**: Know when users join and leave
- **Automatic Fallback**: Works in single-server mode without Redis

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Your Application                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐                 │
│   │ Client 1 │    │ Client 2 │    │ Client 3 │                 │
│   └────┬─────┘    └────┬─────┘    └────┬─────┘                 │
│        │               │               │                        │
│        │ WebSocket     │ WebSocket     │ WebSocket              │
│        ▼               ▼               ▼                        │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │                    FastCMS Server(s)                     │  │
│   │  ┌─────────────────────────────────────────────────┐    │  │
│   │  │           Connection Manager                     │    │  │
│   │  │  • Heartbeat monitoring                         │    │  │
│   │  │  • Subscription management                      │    │  │
│   │  │  • Filter-based event delivery                  │    │  │
│   │  └─────────────────────────────────────────────────┘    │  │
│   └─────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │                    Pub/Sub Backend                       │  │
│   │         (Redis for multi-server / In-memory)             │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Connect via WebSocket

```javascript
// Connect to FastCMS real-time endpoint
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/realtime');

ws.onopen = () => {
  console.log('Connected to FastCMS');

  // Subscribe to posts collection
  ws.send(JSON.stringify({
    action: 'subscribe',
    collection: 'posts'
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};
```

### 2. Handle Events

```javascript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  switch (message.type) {
    case 'connected':
      console.log('Connection ID:', message.data.connection_id);
      break;

    case 'subscribed':
      console.log('Subscribed to:', message.data.collection);
      break;

    case 'event':
      const eventData = message.data;
      console.log(`${eventData.type} on ${eventData.collection}:`, eventData.data);
      break;

    case 'ping':
      // Respond to server heartbeat
      ws.send(JSON.stringify({ action: 'pong' }));
      break;

    case 'error':
      console.error('Error:', message.data.message);
      break;
  }
};
```

## Client-Server Communication

### Client Actions

| Action | Description | Example |
|--------|-------------|---------|
| `subscribe` | Subscribe to a collection | `{"action": "subscribe", "collection": "posts"}` |
| `subscribe` (with filter) | Subscribe with filter | `{"action": "subscribe", "collection": "posts", "filter": {"published": true}}` |
| `subscribe` (global) | Subscribe to all events | `{"action": "subscribe", "collection": "*"}` |
| `unsubscribe` | Unsubscribe from collection | `{"action": "unsubscribe", "collection": "posts"}` |
| `auth` | Authenticate connection | `{"action": "auth", "token": "YOUR_JWT"}` |
| `pong` | Respond to server ping | `{"action": "pong"}` |

### Server Messages

| Type | Description | Payload Example |
|------|-------------|-----------------|
| `connected` | Connection established | `{"connection_id": "uuid", "server_time": "..."}` |
| `authenticated` | Auth successful | `{"user_id": "...", "email": "..."}` |
| `subscribed` | Subscription confirmed | `{"collection": "posts", "filter": {...}}` |
| `unsubscribed` | Unsubscription confirmed | `{"collection": "posts"}` |
| `event` | Data change event | `{"type": "record.created", "collection": "posts", "data": {...}}` |
| `ping` | Server heartbeat | `{"timestamp": "..."}` |
| `error` | Error occurred | `{"message": "Description"}` |

## Event Types

| Event | When Triggered |
|-------|----------------|
| `record.created` | New record inserted |
| `record.updated` | Record modified |
| `record.deleted` | Record removed |
| `collection.created` | New collection created |
| `collection.updated` | Collection schema changed |
| `collection.deleted` | Collection removed |
| `user.joined` | User authenticated |
| `user.left` | User disconnected |

## Authentication

### Option 1: Token in URL (Recommended)

```javascript
const token = 'YOUR_JWT_TOKEN';
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/realtime?token=${token}`);
```

### Option 2: Authenticate After Connect

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/realtime');

ws.onopen = () => {
  // Authenticate after connection
  ws.send(JSON.stringify({
    action: 'auth',
    token: 'YOUR_JWT_TOKEN'
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  if (message.type === 'authenticated') {
    console.log('Logged in as:', message.data.user_id);

    // Now subscribe to collections
    ws.send(JSON.stringify({
      action: 'subscribe',
      collection: 'posts'
    }));
  }
};
```

## Filtered Subscriptions (Live Queries)

Subscribe to receive only events matching specific criteria:

```javascript
// Only published posts
ws.send(JSON.stringify({
  action: 'subscribe',
  collection: 'posts',
  filter: { published: true }
}));

// Only products in a category
ws.send(JSON.stringify({
  action: 'subscribe',
  collection: 'products',
  filter: {
    category: 'electronics',
    in_stock: true
  }
}));

// Comments for a specific post
ws.send(JSON.stringify({
  action: 'subscribe',
  collection: 'comments',
  filter: { post_id: 'abc123' }
}));
```

## Complete Examples

### Vanilla JavaScript

```javascript
class FastCMSRealtime {
  constructor(baseUrl, token = null) {
    this.baseUrl = baseUrl.replace('http', 'ws');
    this.token = token;
    this.ws = null;
    this.listeners = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect() {
    const url = this.token
      ? `${this.baseUrl}/api/v1/ws/realtime?token=${this.token}`
      : `${this.baseUrl}/api/v1/ws/realtime`;

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('FastCMS: Connected');
      this.reconnectAttempts = 0;
      this.emit('connected');
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.type === 'ping') {
        this.ws.send(JSON.stringify({ action: 'pong' }));
        return;
      }

      if (message.type === 'event') {
        const { type, collection, data } = message.data;
        this.emit(`${collection}:${type}`, data);
        this.emit(type, { collection, data });
      }

      this.emit(message.type, message.data);
    };

    this.ws.onclose = () => {
      console.log('FastCMS: Disconnected');
      this.emit('disconnected');
      this.attemptReconnect();
    };

    this.ws.onerror = (error) => {
      console.error('FastCMS: Error', error);
      this.emit('error', error);
    };

    return this;
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
      console.log(`FastCMS: Reconnecting in ${delay}ms...`);
      setTimeout(() => this.connect(), delay);
    }
  }

  subscribe(collection, filter = null) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        action: 'subscribe',
        collection,
        filter
      }));
    }
    return this;
  }

  unsubscribe(collection) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        action: 'unsubscribe',
        collection
      }));
    }
    return this;
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
    return this;
  }

  off(event, callback) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index > -1) callbacks.splice(index, 1);
    }
    return this;
  }

  emit(event, data) {
    const callbacks = this.listeners.get(event) || [];
    callbacks.forEach(cb => cb(data));
  }

  disconnect() {
    this.maxReconnectAttempts = 0;
    this.ws?.close();
  }
}

// Usage
const realtime = new FastCMSRealtime('http://localhost:8000', 'YOUR_JWT_TOKEN');

realtime
  .connect()
  .on('connected', () => {
    realtime.subscribe('posts', { published: true });
    realtime.subscribe('comments');
  })
  .on('posts:record.created', (data) => {
    console.log('New post:', data);
  })
  .on('record.updated', ({ collection, data }) => {
    console.log(`Updated in ${collection}:`, data);
  });
```

### React Hook

```jsx
import { useState, useEffect, useRef, useCallback } from 'react';

export function useRealtime(baseUrl, token = null) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState(null);
  const wsRef = useRef(null);
  const listenersRef = useRef(new Map());

  useEffect(() => {
    const wsUrl = baseUrl.replace('http', 'ws');
    const url = token
      ? `${wsUrl}/api/v1/ws/realtime?token=${token}`
      : `${wsUrl}/api/v1/ws/realtime`;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      // Respond to server pings
      if (message.type === 'ping') {
        ws.send(JSON.stringify({ action: 'pong' }));
        return;
      }

      // Handle events
      if (message.type === 'event') {
        setLastEvent(message.data);

        // Notify collection-specific listeners
        const key = `${message.data.collection}:${message.data.type}`;
        listenersRef.current.get(key)?.forEach(cb => cb(message.data));
      }
    };

    return () => {
      ws.close();
    };
  }, [baseUrl, token]);

  const subscribe = useCallback((collection, filter = null) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'subscribe',
        collection,
        filter
      }));
    }
  }, []);

  const unsubscribe = useCallback((collection) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'unsubscribe',
        collection
      }));
    }
  }, []);

  const onEvent = useCallback((collection, eventType, callback) => {
    const key = `${collection}:${eventType}`;
    if (!listenersRef.current.has(key)) {
      listenersRef.current.set(key, []);
    }
    listenersRef.current.get(key).push(callback);

    // Return cleanup function
    return () => {
      const listeners = listenersRef.current.get(key);
      const index = listeners?.indexOf(callback);
      if (index > -1) listeners.splice(index, 1);
    };
  }, []);

  return { isConnected, lastEvent, subscribe, unsubscribe, onEvent };
}

// Usage Example
function PostsList() {
  const [posts, setPosts] = useState([]);
  const { isConnected, subscribe, onEvent } = useRealtime(
    'http://localhost:8000',
    localStorage.getItem('token')
  );

  useEffect(() => {
    // Fetch initial data
    fetch('/api/v1/collections/posts/records')
      .then(res => res.json())
      .then(data => setPosts(data.items));
  }, []);

  useEffect(() => {
    if (!isConnected) return;

    // Subscribe to posts
    subscribe('posts');

    // Listen for events
    const cleanupCreated = onEvent('posts', 'record.created', (event) => {
      setPosts(prev => [event.data, ...prev]);
    });

    const cleanupUpdated = onEvent('posts', 'record.updated', (event) => {
      setPosts(prev => prev.map(p =>
        p.id === event.record_id ? event.data : p
      ));
    });

    const cleanupDeleted = onEvent('posts', 'record.deleted', (event) => {
      setPosts(prev => prev.filter(p => p.id !== event.record_id));
    });

    return () => {
      cleanupCreated();
      cleanupUpdated();
      cleanupDeleted();
    };
  }, [isConnected, subscribe, onEvent]);

  return (
    <div>
      <p>Status: {isConnected ? 'Connected' : 'Disconnected'}</p>
      <ul>
        {posts.map(post => (
          <li key={post.id}>{post.title}</li>
        ))}
      </ul>
    </div>
  );
}
```

### Vue 3 Composable

```javascript
import { ref, onMounted, onUnmounted } from 'vue';

export function useRealtime(baseUrl, token = null) {
  const isConnected = ref(false);
  const lastEvent = ref(null);
  let ws = null;
  const listeners = new Map();

  const connect = () => {
    const wsUrl = baseUrl.replace('http', 'ws');
    const url = token
      ? `${wsUrl}/api/v1/ws/realtime?token=${token}`
      : `${wsUrl}/api/v1/ws/realtime`;

    ws = new WebSocket(url);

    ws.onopen = () => {
      isConnected.value = true;
    };

    ws.onclose = () => {
      isConnected.value = false;
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.type === 'ping') {
        ws.send(JSON.stringify({ action: 'pong' }));
        return;
      }

      if (message.type === 'event') {
        lastEvent.value = message.data;
        const key = `${message.data.collection}:${message.data.type}`;
        listeners.get(key)?.forEach(cb => cb(message.data));
      }
    };
  };

  const subscribe = (collection, filter = null) => {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'subscribe', collection, filter }));
    }
  };

  const unsubscribe = (collection) => {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'unsubscribe', collection }));
    }
  };

  const onEvent = (collection, eventType, callback) => {
    const key = `${collection}:${eventType}`;
    if (!listeners.has(key)) listeners.set(key, []);
    listeners.get(key).push(callback);
  };

  onMounted(connect);
  onUnmounted(() => ws?.close());

  return { isConnected, lastEvent, subscribe, unsubscribe, onEvent };
}
```

## Configuration

### Environment Variables

```env
# Redis for multi-server deployments
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=true

# When REDIS_ENABLED=false, in-memory Pub/Sub is used (single-server mode)
```

### Connection Settings

The connection manager has configurable timeouts (in `app/core/websocket_manager.py`):

```python
HEARTBEAT_INTERVAL = 30  # Server sends ping every 30 seconds
HEARTBEAT_TIMEOUT = 90   # Connection considered dead after 90 seconds
CLEANUP_INTERVAL = 60    # Stale connection cleanup runs every 60 seconds
```

## API Reference

### WebSocket Endpoint

```
GET ws://localhost:8000/api/v1/ws/realtime
GET ws://localhost:8000/api/v1/ws/realtime?token=JWT_TOKEN
```

### Statistics Endpoint

```
GET /api/v1/stats
```

Returns connection statistics for the current server instance:

```json
{
  "total_connections": 10,
  "authenticated_connections": 8,
  "unique_users": 6,
  "pubsub_backend": "redis",
  "subscriptions": {
    "conn-id-1": ["posts", "comments"],
    "conn-id-2": ["*"]
  }
}
```

## Troubleshooting

### Connection Issues

| Problem | Solution |
|---------|----------|
| Connection closes immediately | Check if token is valid (if using auth) |
| No messages received | Ensure you sent a `subscribe` action |
| Connection drops frequently | Client should respond to `ping` with `pong` |
| Events not matching filter | Verify filter keys match record fields |

### Server Logs

Enable debug logging to see real-time activity:

```env
LOG_LEVEL=DEBUG
```

### Testing Connection

```bash
# Using wscat (npm install -g wscat)
wscat -c "ws://localhost:8000/api/v1/ws/realtime"

# Then send:
{"action": "subscribe", "collection": "posts"}
```

## Performance Tips

1. **Use Filters**: Subscribe with filters to reduce unnecessary events
2. **Respond to Pings**: Always respond to `ping` with `pong` to prevent disconnection
3. **Handle Reconnection**: Implement exponential backoff for reconnection
4. **Batch Updates**: On the client, debounce UI updates for high-frequency events
5. **Scale with Redis**: For production with multiple servers, always enable Redis
