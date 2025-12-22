# Records API

Records are the data entries stored within collections. This guide covers all operations for creating, reading, updating, and deleting records.

## Quick Start

```bash
# Create a record
curl -X POST http://localhost:8000/api/v1/collections/posts/records \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"data": {"title": "Hello World", "content": "My first post"}}'

# List records
curl http://localhost:8000/api/v1/collections/posts/records \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get single record
curl http://localhost:8000/api/v1/collections/posts/records/RECORD_ID \
  -H "Authorization: Bearer YOUR_TOKEN"

# Update record
curl -X PATCH http://localhost:8000/api/v1/collections/posts/records/RECORD_ID \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"data": {"title": "Updated Title"}}'

# Delete record
curl -X DELETE http://localhost:8000/api/v1/collections/posts/records/RECORD_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Create a Record

```http
POST /api/v1/collections/{collection_name}/records
Authorization: Bearer <token>
Content-Type: application/json

{
  "data": {
    "title": "My Post",
    "content": "Post content here",
    "published": true,
    "tags": ["news", "tech"]
  }
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "title": "My Post",
    "content": "Post content here",
    "published": true,
    "tags": ["news", "tech"]
  },
  "created": "2025-12-22T10:30:00Z",
  "updated": "2025-12-22T10:30:00Z"
}
```

## List Records

```http
GET /api/v1/collections/{collection_name}/records
Authorization: Bearer <token>
```

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `per_page` | int | 20 | Items per page (max: 100) |
| `sort` | string | - | Sort fields (see Sorting section) |
| `filter` | string | - | Filter expression (see Filtering section) |
| `search` | string | - | Full-text search across text fields |
| `expand` | string | - | Relations to expand (see Expand section) |
| `fields` | string | - | Fields to return |
| `skipTotal` | bool | false | Skip total count for faster queries |

**Response:**
```json
{
  "items": [
    {
      "id": "uuid-1",
      "data": {"title": "Post 1", "published": true},
      "created": "2025-12-22T10:00:00Z",
      "updated": "2025-12-22T10:00:00Z"
    },
    {
      "id": "uuid-2",
      "data": {"title": "Post 2", "published": false},
      "created": "2025-12-22T09:00:00Z",
      "updated": "2025-12-22T09:00:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "per_page": 20,
  "total_pages": 3
}
```

## Get Single Record

```http
GET /api/v1/collections/{collection_name}/records/{record_id}
Authorization: Bearer <token>
```

### With Expanded Relations

```http
GET /api/v1/collections/posts/records/abc123?expand=author,category
```

## Update a Record

Use `PATCH` for partial updates (only send fields you want to change):

```http
PATCH /api/v1/collections/{collection_name}/records/{record_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "data": {
    "title": "Updated Title",
    "views": 100
  }
}
```

## Delete a Record

```http
DELETE /api/v1/collections/{collection_name}/records/{record_id}
Authorization: Bearer <token>
```

**Response:** `204 No Content`

---

## Filtering

Filter records using powerful query expressions.

### Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `=` | Equal | `status=active` |
| `!=` | Not equal | `status!=deleted` |
| `>` | Greater than | `age>18` |
| `>=` | Greater or equal | `views>=100` |
| `<` | Less than | `price<100` |
| `<=` | Less or equal | `stock<=10` |
| `~` | Contains (case-insensitive) | `title~hello` |
| `!~` | Does not contain | `title!~spam` |
| `?=` | Any in array | `tags?=[news,tech]` |
| `?!=` | Not in array | `category?!=[spam,ads]` |

### Combining Filters

```bash
# AND: Both conditions must be true
?filter=published=true&&views>100

# OR: Either condition can be true
?filter=featured=true||popular=true

# Complex: Combine AND and OR
?filter=(status=active||status=pending)&&verified=true
```

### DateTime Macros

| Macro | Description |
|-------|-------------|
| `@now` | Current datetime |
| `@today` | Start of today |
| `@yesterday` | Start of yesterday |
| `@tomorrow` | Start of tomorrow |
| `@monthStart` | Start of current month |
| `@monthEnd` | End of current month |
| `@day+7` | 7 days from now |
| `@hour-2` | 2 hours ago |

**Examples:**
```bash
# Records created today
?filter=created>=@today

# Records from the last 7 days
?filter=created>@day-7

# Records updated in the last hour
?filter=updated>@hour-1
```

---

## Sorting

### Single Field Sort

```bash
# Ascending (oldest first)
?sort=created

# Descending (newest first)
?sort=-created
```

### Multi-Field Sort

```bash
# Sort by created (desc), then by title (asc)
?sort=-created,+title
```

### Random Order

```bash
# Random order each request
?sort=@random
```

---

## Field Selection

Return only specific fields to reduce response size:

```bash
# Only return id, title, and created
?fields=id,title,created
```

**Response:**
```json
{
  "items": [
    {"id": "uuid-1", "title": "Post 1", "created": "2025-12-22T10:00:00Z"},
    {"id": "uuid-2", "title": "Post 2", "created": "2025-12-22T09:00:00Z"}
  ]
}
```

---

## Expanding Relations

When a collection has relation fields, expand them to include full related records.

### Single Relation

```bash
# Expand author field
?expand=author
```

**Response:**
```json
{
  "id": "post-uuid",
  "data": {
    "title": "My Post",
    "author": {
      "id": "user-uuid",
      "data": {"name": "John Doe", "email": "john@example.com"},
      "created": "2025-01-01T00:00:00Z"
    }
  }
}
```

### Multiple Relations

```bash
?expand=author,category,tags
```

### Nested Relations

```bash
# Expand author, then expand the author's company
?expand=author.company

# Deep nesting
?expand=author.company.ceo
```

---

## Full-Text Search

Search across all text fields in records:

```bash
?search=hello world
```

This searches `title`, `content`, `description`, and other text fields.

---

## Pagination

### Standard Pagination

```bash
?page=2&per_page=50
```

### Performance Optimization

For large datasets, skip the total count:

```bash
?skipTotal=true
```

This returns `-1` for `total` and `total_pages` but is significantly faster.

---

## JavaScript Examples

### Fetch Records

```javascript
const response = await fetch(
  'http://localhost:8000/api/v1/collections/posts/records?page=1&per_page=10&sort=-created',
  {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }
);
const data = await response.json();
console.log(data.items);
```

### Create Record

```javascript
const response = await fetch(
  'http://localhost:8000/api/v1/collections/posts/records',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      data: {
        title: 'New Post',
        content: 'Content here',
        published: true
      }
    })
  }
);
const record = await response.json();
```

### Update Record

```javascript
const response = await fetch(
  `http://localhost:8000/api/v1/collections/posts/records/${recordId}`,
  {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      data: {
        title: 'Updated Title'
      }
    })
  }
);
```

### Delete Record

```javascript
await fetch(
  `http://localhost:8000/api/v1/collections/posts/records/${recordId}`,
  {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }
);
```

### Complex Query

```javascript
const params = new URLSearchParams({
  page: '1',
  per_page: '20',
  sort: '-created,+title',
  filter: 'published=true&&views>100',
  expand: 'author,category',
  fields: 'id,title,author,views,created'
});

const response = await fetch(
  `http://localhost:8000/api/v1/collections/posts/records?${params}`,
  {
    headers: { 'Authorization': `Bearer ${token}` }
  }
);
```

---

## React Hook Example

```jsx
import { useState, useEffect } from 'react';

function useRecords(collection, options = {}) {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({});

  useEffect(() => {
    const fetchRecords = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams({
          page: options.page || 1,
          per_page: options.perPage || 20,
          ...(options.sort && { sort: options.sort }),
          ...(options.filter && { filter: options.filter }),
          ...(options.expand && { expand: options.expand }),
          ...(options.search && { search: options.search }),
        });

        const res = await fetch(
          `http://localhost:8000/api/v1/collections/${collection}/records?${params}`,
          {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
          }
        );

        if (!res.ok) throw new Error('Failed to fetch');

        const data = await res.json();
        setRecords(data.items);
        setPagination({
          total: data.total,
          page: data.page,
          perPage: data.per_page,
          totalPages: data.total_pages
        });
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchRecords();
  }, [collection, JSON.stringify(options)]);

  return { records, loading, error, pagination };
}

// Usage
function PostsList() {
  const { records, loading, pagination } = useRecords('posts', {
    page: 1,
    perPage: 10,
    sort: '-created',
    filter: 'published=true',
    expand: 'author'
  });

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      {records.map(post => (
        <div key={post.id}>
          <h2>{post.data.title}</h2>
          <p>By: {post.data.author?.data?.name}</p>
        </div>
      ))}
      <p>Page {pagination.page} of {pagination.totalPages}</p>
    </div>
  );
}
```

---

## Bulk Operations

See [Bulk Operations](bulk-operations.md) for batch create, update, and delete.

## CSV Import/Export

See [CSV Import/Export](csv-import-export.md) for importing and exporting records as CSV.

## Related Documentation

- [Collections](collections.md) - Managing collection schemas
- [Field Types](field-types.md) - Available field types and validation
- [Access Control](access-control.md) - Permission rules for records
- [Real-time](realtime.md) - Subscribe to record changes
