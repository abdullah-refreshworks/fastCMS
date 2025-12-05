# FastCMS API Reference

Complete API documentation for FastCMS - AI-Native Backend-as-a-Service.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

FastCMS uses JWT (JSON Web Token) authentication.

### Register a New User

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "created": "2025-12-05T00:00:00Z"
}
```

### Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1...",
  "refresh_token": "eyJhbGciOiJIUzI1...",
  "token_type": "bearer"
}
```

### Using Authentication

Include the access token in the Authorization header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1...
```

### Refresh Token

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1..."
}
```

---

## Collections

Collections are dynamic database tables that store your application data.

### List All Collections

```http
GET /api/v1/collections
Authorization: Bearer <token>
```

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "posts",
      "type": "base",
      "schema": {...},
      "created": "2025-12-05T00:00:00Z",
      "updated": "2025-12-05T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20,
  "total_pages": 1
}
```

### Create a Collection

```http
POST /api/v1/collections
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "posts",
  "type": "base",
  "schema": {
    "fields": [
      {
        "name": "title",
        "type": "text",
        "validation": {
          "required": true,
          "min_length": 1,
          "max_length": 200
        }
      },
      {
        "name": "content",
        "type": "editor",
        "validation": {
          "required": true
        }
      },
      {
        "name": "published",
        "type": "bool",
        "validation": {
          "required": false
        }
      },
      {
        "name": "views",
        "type": "number",
        "validation": {
          "min": 0
        }
      }
    ]
  },
  "list_rule": "",
  "view_rule": "",
  "create_rule": "@request.auth.id != ''",
  "update_rule": "@request.auth.id != ''",
  "delete_rule": "@request.auth.role = 'admin'"
}
```

### Collection Types

| Type | Description |
|------|-------------|
| `base` | Standard collection for storing records |
| `auth` | Special collection for user authentication |
| `view` | Read-only collection based on SQL query |

### Field Types

| Type | Description | Validation Options |
|------|-------------|-------------------|
| `text` | String field | `required`, `min_length`, `max_length`, `pattern` |
| `number` | Integer or float | `required`, `min`, `max` |
| `bool` | Boolean true/false | `required` |
| `email` | Email address | `required` |
| `url` | URL string | `required` |
| `date` | Date/datetime | `required` |
| `select` | Single select | `required`, `values` (array of options) |
| `file` | File attachment | `required`, `max_size`, `mime_types` |
| `relation` | Reference to another collection | `required`, `collection` |
| `json` | JSON object | `required` |
| `editor` | Rich text content | `required` |
| `geopoint` | Geographic coordinates | `require_altitude`, `min_lat`, `max_lat`, `min_lng`, `max_lng` |

### GeoPoint Field

Store geographic coordinates with optional altitude:

```json
{
  "name": "location",
  "type": "geopoint",
  "geopoint": {
    "require_altitude": false,
    "min_lat": -90,
    "max_lat": 90,
    "min_lng": -180,
    "max_lng": 180
  }
}
```

**Data format:**
```json
{"lat": 40.7128, "lng": -74.0060}
{"lat": 40.7128, "lng": -74.0060, "alt": 10.5}
```

### Get a Collection

```http
GET /api/v1/collections/{collection_id}
Authorization: Bearer <token>
```

### Update a Collection

```http
PATCH /api/v1/collections/{collection_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "schema": {
    "fields": [...]
  }
}
```

### Delete a Collection

```http
DELETE /api/v1/collections/{collection_id}
Authorization: Bearer <token>
```

### Custom Indexes

#### List Indexes

```http
GET /api/v1/collections/{collection_id}/indexes
Authorization: Bearer <token>
```

#### Create Index

```http
POST /api/v1/collections/{collection_id}/indexes
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "idx_title_created",
  "fields": [
    {"name": "title", "order": "asc"},
    {"name": "created", "order": "desc"}
  ],
  "unique": false
}
```

#### Get Index Details

```http
GET /api/v1/collections/{collection_id}/indexes/{index_name}
Authorization: Bearer <token>
```

#### Delete Index

```http
DELETE /api/v1/collections/{collection_id}/indexes/{index_name}
Authorization: Bearer <token>
```

---

## Records

Records are entries in a collection.

### List Records

```http
GET /api/v1/collections/{collection_name}/records
Authorization: Bearer <token>
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | int | Page number (default: 1) |
| `per_page` | int | Items per page (default: 20, max: 100) |
| `sort` | string | Sort fields: `-created`, `-created,+title`, `@random` |
| `filter` | string | Filter expression (see Filtering section) |
| `search` | string | Full-text search across text fields |
| `expand` | string | Comma-separated relation fields to expand (supports nested: `author.company`) |
| `fields` | string | Comma-separated fields to return: `id,title,created` |
| `skipTotal` | bool | Skip total count for faster queries (default: false) |

**Example:**
```http
GET /api/v1/collections/posts/records?page=1&per_page=10&sort=-created,+title&filter=published=true&fields=id,title&skipTotal=true
```

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "data": {
        "title": "My First Post",
        "content": "<p>Hello World</p>",
        "published": true,
        "views": 42
      },
      "created": "2025-12-05T00:00:00Z",
      "updated": "2025-12-05T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 10,
  "total_pages": 1
}
```

### Create a Record

```http
POST /api/v1/collections/{collection_name}/records
Authorization: Bearer <token>
Content-Type: application/json

{
  "data": {
    "title": "My First Post",
    "content": "<p>Hello World</p>",
    "published": true
  }
}
```

### Get a Record

```http
GET /api/v1/collections/{collection_name}/records/{record_id}
Authorization: Bearer <token>
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `expand` | string | Comma-separated relation fields to expand |

### Update a Record

```http
PATCH /api/v1/collections/{collection_name}/records/{record_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "data": {
    "title": "Updated Title"
  }
}
```

### Delete a Record

```http
DELETE /api/v1/collections/{collection_name}/records/{record_id}
Authorization: Bearer <token>
```

---

## Filtering

FastCMS supports powerful filter expressions for querying records.

### Filter Syntax

```
field operator value
```

Multiple filters can be combined with:
- `&&` - AND (both conditions must be true)
- `||` - OR (either condition can be true)

### Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `=` | Equal | `status=active` |
| `!=` | Not equal | `status!=deleted` |
| `>` | Greater than | `age>18` |
| `<` | Less than | `price<100` |
| `>=` | Greater than or equal | `views>=100` |
| `<=` | Less than or equal | `stock<=10` |
| `~` | Contains (case-insensitive) | `title~hello` |
| `!~` | Does not contain | `title!~spam` |
| `?=` | Any equal (array check) | `tags?=[news, tech]` |
| `?!=` | Not any equal | `category?!=[spam, ads]` |
| `?>` | Any greater than | `scores?>[80, 90]` |
| `?>=` | Any greater than or equal | `grades?>=[A, B]` |
| `?<` | Any less than | `prices?<[50, 100]` |
| `?<=` | Any less than or equal | `ratings?<=[3, 2]` |
| `?~` | Any like | `tags?~[tech, code]` |
| `?!~` | Any not like | `tags?!~[spam, ads]` |

### DateTime Macros

Use these macros for dynamic date filtering:

| Macro | Description |
|-------|-------------|
| `@now` | Current datetime |
| `@today` | Start of current day (00:00:00) |
| `@yesterday` | Start of yesterday |
| `@tomorrow` | Start of tomorrow |
| `@todayStart` | Same as @today |
| `@todayEnd` | End of current day (23:59:59) |
| `@monthStart` | Start of current month |
| `@monthEnd` | End of current month |
| `@yearStart` | Start of current year |
| `@yearEnd` | End of current year |

**Relative Offsets:**

| Macro | Description |
|-------|-------------|
| `@second+N` / `@second-N` | Add/subtract N seconds |
| `@minute+N` / `@minute-N` | Add/subtract N minutes |
| `@hour+N` / `@hour-N` | Add/subtract N hours |
| `@day+N` / `@day-N` | Add/subtract N days |
| `@week+N` / `@week-N` | Add/subtract N weeks |
| `@month+N` / `@month-N` | Add/subtract N months |
| `@year+N` / `@year-N` | Add/subtract N years |

### Filter Examples

```http
# Get active posts
GET /records?filter=published=true

# Get posts created in the last 7 days
GET /records?filter=created>@day-7

# Get posts with more than 100 views AND published
GET /records?filter=views>100&&published=true

# Get posts that are either featured OR have high views
GET /records?filter=featured=true||views>1000

# Get posts created today
GET /records?filter=created>=@todayStart&&created<=@todayEnd

# Search for posts containing "tutorial" but not "beginner"
GET /records?filter=title~tutorial&&title!~beginner
```

---

## Sorting

### Syntax

Use the `sort` parameter with a field name. Prefix with `-` for descending order, `+` for ascending.

```http
# Sort by created date, newest first
GET /records?sort=-created

# Sort by title alphabetically
GET /records?sort=title

# Sort by views descending
GET /records?sort=-views

# Multi-field sort: first by created desc, then by title asc
GET /records?sort=-created,+title

# Random order
GET /records?sort=@random
```

---

## Relation Expansion

Expand related records inline using the `expand` parameter. Supports nested expansion up to 3 levels.

```http
# Expand author relation
GET /records?expand=author

# Expand multiple relations
GET /records?expand=author,category,tags

# Nested expand: get author and author's company
GET /records?expand=author.company

# Deep nested expand
GET /records?expand=author.company.ceo
```

**Response with expansion:**
```json
{
  "id": "post-123",
  "data": {
    "title": "My Post",
    "author": "user-456"
  },
  "expand": {
    "author": {
      "id": "user-456",
      "data": {
        "name": "John Doe",
        "email": "john@example.com",
        "company": "company-789"
      },
      "expand": {
        "company": {
          "id": "company-789",
          "data": {
            "name": "Acme Corp"
          }
        }
      }
    }
  }
}
```

---

## Real-time Subscriptions

FastCMS supports real-time updates via Server-Sent Events (SSE) and WebSockets.

### SSE Endpoints

#### Subscribe to All Events

```http
GET /api/v1/realtime
```

Receives all record AND collection events.

#### Subscribe to Collection Events

```http
GET /api/v1/realtime/{collection_name}
```

Receives events only for the specified collection.

#### Subscribe to Single Record

```http
GET /api/v1/realtime/{collection_name}/{record_id}
```

Receives events only for a specific record.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | string | Optional user ID for presence tracking |
| `query` | string | Optional filter (e.g., `status=published`) |

### WebSocket Endpoint

```
ws://localhost:8000/api/v1/ws/realtime?token=YOUR_JWT
```

**Client Messages:**

```json
// Subscribe to collection
{"action": "subscribe", "collection": "posts", "filter": {"published": true}}

// Unsubscribe
{"action": "unsubscribe", "collection": "posts"}

// Authentication
{"action": "auth", "token": "YOUR_JWT"}

// Heartbeat
{"action": "ping"}
```

**Server Messages:**

```json
// Event notification
{"type": "event", "data": {...}, "timestamp": "..."}

// Subscription confirmed
{"type": "subscribed", "data": {"collection": "posts"}}

// Pong response
{"type": "pong", "data": {}}
```

### Event Types

| Event | Description |
|-------|-------------|
| `record.created` | New record created in a collection |
| `record.updated` | Record updated |
| `record.deleted` | Record deleted |
| `collection.created` | New collection created |
| `collection.updated` | Collection schema/rules updated |
| `collection.deleted` | Collection deleted |
| `user.joined` | User connected to realtime |
| `user.left` | User disconnected |
| `presence.update` | User presence changed |

### JavaScript Example

```javascript
// Subscribe to all events (records + collections)
const eventSource = new EventSource('/api/v1/realtime');

// Record events
eventSource.addEventListener('record.created', (e) => {
    console.log('New record:', JSON.parse(e.data));
});

eventSource.addEventListener('record.updated', (e) => {
    console.log('Record updated:', JSON.parse(e.data));
});

// Collection events
eventSource.addEventListener('collection.created', (e) => {
    console.log('New collection:', JSON.parse(e.data));
});

eventSource.addEventListener('collection.updated', (e) => {
    console.log('Collection updated:', JSON.parse(e.data));
});

eventSource.addEventListener('collection.deleted', (e) => {
    console.log('Collection deleted:', JSON.parse(e.data));
});

// Subscribe to specific collection
const postsEvents = new EventSource('/api/v1/realtime/posts');

// Subscribe to specific record
const recordEvents = new EventSource('/api/v1/realtime/posts/abc123');
```

---

## Presence API

Track online users and who is viewing what.

### Get All Online Users

```http
GET /api/v1/presence
```

**Response:**
```json
{
  "users": [
    {
      "user_id": "user123",
      "user_name": "John Doe",
      "last_seen": "2025-12-05T10:30:00Z",
      "connections": 2
    }
  ],
  "total": 1
}
```

### Get User Presence

```http
GET /api/v1/presence/{user_id}
```

**Response (online):**
```json
{
  "online": true,
  "user_id": "user123",
  "user_name": "John Doe",
  "last_seen": "2025-12-05T10:30:00Z",
  "connections": 2
}
```

**Response (offline):**
```json
{
  "online": false,
  "user_id": "user123"
}
```

### Get Collection Viewers

```http
GET /api/v1/presence/collection/{collection_name}
```

**Response:**
```json
{
  "collection": "posts",
  "subscriber_count": 5,
  "users": [
    {"user_id": "user123", "user_name": "John", "last_seen": "..."}
  ]
}
```

### Realtime Stats

```http
GET /api/v1/stats
```

**Response:**
```json
{
  "total_connections": 10,
  "authenticated_connections": 8,
  "collection_subscribers": {
    "posts": 5,
    "users": 3
  },
  "global_subscribers": 2,
  "unique_users": 6
}
```

---

## Batch Operations

### Batch Create (up to 100 records)

```http
POST /api/v1/collections/{collection_name}/records/batch
Authorization: Bearer <token>
Content-Type: application/json

{
  "records": [
    {"title": "Post 1", "content": "..."},
    {"title": "Post 2", "content": "..."},
    {"title": "Post 3", "content": "..."}
  ]
}
```

**Response:**
```json
{
  "created": 3,
  "failed": 0,
  "records": [...],
  "errors": null
}
```

### Batch Upsert (Create or Update)

```http
POST /api/v1/collections/{collection_name}/records/upsert
Authorization: Bearer <token>
Content-Type: application/json

{
  "records": [
    {"title": "New Post"},
    {"id": "existing-id-123", "title": "Updated Post"}
  ]
}
```

Include `id` to update existing records, omit to create new ones.

**Response:**
```json
{
  "created": 1,
  "updated": 1,
  "failed": 0,
  "records": [...],
  "errors": null
}
```

### Bulk Update

```http
POST /api/v1/collections/{collection_name}/records/bulk-update
Authorization: Bearer <token>
Content-Type: application/json

{
  "record_ids": ["id1", "id2", "id3"],
  "data": {
    "published": true
  }
}
```

### Bulk Delete

```http
POST /api/v1/collections/{collection_name}/records/bulk-delete
Authorization: Bearer <token>
Content-Type: application/json

{
  "record_ids": ["id1", "id2", "id3"]
}
```

### Generic Batch API

Execute multiple API requests in a single call:

```http
POST /api/v1/batch
Authorization: Bearer <token>
Content-Type: application/json

{
  "requests": [
    {"method": "POST", "url": "/api/v1/collections/posts/records", "body": {"data": {"title": "Post 1"}}},
    {"method": "POST", "url": "/api/v1/collections/posts/records", "body": {"data": {"title": "Post 2"}}},
    {"method": "PATCH", "url": "/api/v1/collections/posts/records/abc123", "body": {"data": {"views": 100}}}
  ]
}
```

---

## Webhooks

Configure webhooks to receive notifications about events.

### Create Webhook

```http
POST /api/v1/webhooks
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Notify on new post",
  "url": "https://your-server.com/webhook",
  "collection": "posts",
  "events": ["record.created", "record.updated"],
  "enabled": true
}
```

### Webhook Payload

```json
{
  "event": "record.created",
  "collection": "posts",
  "record_id": "uuid",
  "data": {...},
  "timestamp": "2025-12-05T00:00:00Z"
}
```

---

## File Upload

### Upload a File

```http
POST /api/v1/files/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <binary>
collection: posts
field: attachment
```

**Response:**
```json
{
  "id": "file-uuid",
  "filename": "document.pdf",
  "size": 12345,
  "mime_type": "application/pdf",
  "url": "/api/v1/files/file-uuid"
}
```

### Download a File

```http
GET /api/v1/files/{file_id}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": "Error type",
  "message": "Human-readable error message",
  "details": {...}
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (successful delete) |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Validation Error |
| 500 | Internal Server Error |

---

## Access Rules

Control access to collections using rule expressions.

### Rule Syntax

Rules are expressions that evaluate to true/false:

| Expression | Description |
|------------|-------------|
| `""` | Allow all (empty string) |
| `@request.auth.id != ''` | Require authentication |
| `@request.auth.role = 'admin'` | Require admin role |
| `@request.auth.id = @record.user_id` | Owner only |

### Available Variables

| Variable | Description |
|----------|-------------|
| `@request.auth.id` | Current user's ID |
| `@request.auth.email` | Current user's email |
| `@request.auth.role` | Current user's role |
| `@request.auth.verified` | Whether user is authenticated (bool) |
| `@request.data.*` | Request body data |
| `@request.headers.*` | Request headers (lowercase) |
| `@request.query.*` | Query parameters |
| `@request.method` | HTTP method (GET, POST, etc.) |
| `@record.*` | Current record data (for update/delete) |

### Examples

```
# Only allow POST requests
@request.method = 'POST'

# Check custom header
@request.headers.x-api-key = 'secret123'

# Check query parameter
@request.query.admin = 'true'

# Combine with auth
@request.auth.id != '' && @request.headers.x-tenant = 'company1'
```

---

## Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "FastCMS",
  "version": "0.1.0",
  "environment": "development"
}
```
