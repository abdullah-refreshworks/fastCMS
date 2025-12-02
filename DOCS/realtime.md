# Real-time Features

FastCMS provides comprehensive real-time capabilities using Server-Sent Events (SSE), including Live Queries, Presence Tracking, and Real-time Collection Updates.

## Overview

Real-time features enable your applications to:
- **Live Queries**: Subscribe to filtered data changes with query-based subscriptions
- **Presence Tracking**: Track which users are currently active in your application
- **Real-time Collections**: Automatically sync collection changes across all connected clients

## Quick Start

**Basic Connection (JavaScript):**
```javascript
// Connect to real-time updates
const eventSource = new EventSource('/api/v1/realtime');

// Listen to record events
eventSource.addEventListener('record.created', (e) => {
  const data = JSON.parse(e.data);
  console.log('New record:', data);
});

eventSource.addEventListener('record.updated', (e) => {
  const data = JSON.parse(e.data);
  console.log('Record updated:', data);
});

eventSource.addEventListener('record.deleted', (e) => {
  const data = JSON.parse(e.data);
  console.log('Record deleted:', data);
});
```

## Live Queries

Subscribe to data changes with query filters to receive only relevant updates.

**Supported Operators:**
- `field=value` - Equality
- `field!=value` - Not equal
- `field>value` - Greater than
- `field<value` - Less than
- `field>=value` - Greater than or equal
- `field<=value` - Less than or equal

**Examples:**

```javascript
// Subscribe to published posts only
const eventSource = new EventSource('/api/v1/realtime?query=status=published');

// Subscribe to products over $100
const eventSource = new EventSource('/api/v1/realtime/products?query=price>100');

// Subscribe to active users
const eventSource = new EventSource('/api/v1/realtime/users?query=active=true');
```

**Collection-Specific Subscription:**
```javascript
// Subscribe to a specific collection
const eventSource = new EventSource('/api/v1/realtime/posts');

// With query filter
const eventSource = new EventSource('/api/v1/realtime/posts?query=author=john');
```

## Presence Tracking

Track active users in your application in real-time.

**Enable Presence Tracking:**
```javascript
// Connect with user ID for presence tracking
const userId = 'user-123';
const eventSource = new EventSource(`/api/v1/realtime?user_id=${userId}`);

// Listen to presence events
eventSource.addEventListener('user.joined', (e) => {
  const data = JSON.parse(e.data);
  console.log('User joined:', data.data);
  // { user_id, user_name, connections, last_seen }
});

eventSource.addEventListener('user.left', (e) => {
  const data = JSON.parse(e.data);
  console.log('User left:', data.data);
});
```

**Get Active Users:**
```bash
# Get all active users
curl http://localhost:8000/api/v1/presence

# Response
{
  "users": [
    {
      "user_id": "user-123",
      "user_name": "John Doe",
      "connections": 2,
      "last_seen": "2025-01-15T10:30:00"
    }
  ],
  "count": 1
}
```

## Event Types

- `record.created` - New record created
- `record.updated` - Record updated
- `record.deleted` - Record deleted
- `collection.created` - New collection created
- `collection.updated` - Collection schema updated
- `collection.deleted` - Collection deleted
- `user.joined` - User connected
- `user.left` - User disconnected

**Event Data Structure:**
```json
{
  "type": "record.created",
  "collection": "posts",
  "record_id": "abc123",
  "data": {
    "id": "abc123",
    "title": "New Post",
    "content": "Post content...",
    "created": "2025-01-15T10:30:00"
  },
  "timestamp": "2025-01-15T10:30:00"
}
```

## React Example

```javascript
import { useEffect, useState } from 'react';

function useRealtime(collection, query = '') {
  const [events, setEvents] = useState([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    let url = `/api/v1/realtime`;
    if (collection) {
      url = `/api/v1/realtime/${collection}`;
    }
    if (query) {
      url += `?query=${encodeURIComponent(query)}`;
    }

    const eventSource = new EventSource(url);

    eventSource.addEventListener('connected', () => {
      setConnected(true);
    });

    eventSource.addEventListener('record.created', (e) => {
      const data = JSON.parse(e.data);
      setEvents(prev => [...prev, data]);
    });

    eventSource.addEventListener('record.updated', (e) => {
      const data = JSON.parse(e.data);
      setEvents(prev => [...prev, data]);
    });

    eventSource.addEventListener('record.deleted', (e) => {
      const data = JSON.parse(e.data);
      setEvents(prev => [...prev, data]);
    });

    eventSource.onerror = () => {
      setConnected(false);
    };

    return () => {
      eventSource.close();
    };
  }, [collection, query]);

  return { events, connected };
}

// Usage
function PostsList() {
  const { events, connected } = useRealtime('posts', 'status=published');

  return (
    <div>
      <div>Status: {connected ? 'Connected' : 'Disconnected'}</div>
      <ul>
        {events.map((event, i) => (
          <li key={i}>{event.type}: {event.data.title}</li>
        ))}
      </ul>
    </div>
  );
}
```

## Performance Considerations

**Connection Limits:**
- Each SSE connection is lightweight but persistent
- Browsers typically limit 6 concurrent connections per domain
- Consider using a single connection for multiple collections when possible

**Best Practices:**
1. **Use Query Filters**: Reduce unnecessary events by filtering at the source
2. **Debounce UI Updates**: Don't update UI on every event if receiving high frequency
3. **Connection Pooling**: Reuse connections across components when possible
4. **Handle Disconnections**: Implement reconnection logic with exponential backoff
5. **Clean Up**: Always close connections when components unmount

## Security

**Authentication:**
Real-time endpoints respect the same authentication as REST APIs. Include tokens as query parameters:

```javascript
const token = 'your-auth-token';
const eventSource = new EventSource(
  `/api/v1/realtime?token=${token}&user_id=123`
);
```

**Access Control:**
Real-time events respect collection-level access control rules. Users only receive events for collections they have access to.

## Troubleshooting

**Connection won't establish:**
- Check that the server is running
- Verify firewall/proxy settings allow SSE connections
- Some proxies buffer SSE; configure to pass through

**Events not received:**
- Verify you're listening to the correct event types
- Check that records match your query filter
- Ensure the collection name is correct

**High CPU usage:**
- Reduce number of active connections
- Implement proper debouncing for UI updates
- Use query filters to reduce event volume

**Connection keeps dropping:**
- Some networks have aggressive timeouts
- Implement reconnection logic
- Consider using a reverse proxy with keep-alive configured
