# API Reference

All API endpoints are available at `http://localhost:8000/api/v1`

## Collections API

### List Collections
```bash
GET /api/v1/collections
```

### Get Collection
```bash
GET /api/v1/collections/{collection_id}
```

### Create Collection
```bash
POST /api/v1/collections
Authorization: Bearer ADMIN_TOKEN
Content-Type: application/json

{
  "name": "posts",
  "type": "base",
  "schema": [...]
}
```

### Update Collection
```bash
PUT /api/v1/collections/{collection_id}
Authorization: Bearer ADMIN_TOKEN
```

### Delete Collection
```bash
DELETE /api/v1/collections/{collection_id}
Authorization: Bearer ADMIN_TOKEN
```

## Records API

### List Records
```bash
GET /api/v1/collections/{collection_name}/records
```

**Query Parameters:**
- `page` - Page number (default: 1)
- `per_page` - Records per page (default: 30, max: 100)
- `sort` - Sort field (prefix with `-` for descending)
- `filter` - Filter expression
- `search` - Search term for full-text search across text fields

**Example:**
```bash
GET /api/v1/collections/products/records?page=1&per_page=20&sort=-created
```

### Search Records

Full-text search allows you to search across all text, editor, email, and URL fields in a collection using a single search term.

**Endpoint:**
```bash
GET /api/v1/collections/{collection_name}/records?search={query}
```

**How It Works:**
- Searches across all text-based fields (text, editor, email, url)
- Uses case-insensitive partial matching (LIKE operator)
- Results match if the search term appears anywhere in any searchable field
- Can be combined with filters and sorting

**Basic Search Example:**
```bash
GET /api/v1/collections/posts/records?search=fastcms
```

**Search with Filters:**
```bash
GET /api/v1/collections/posts/records?search=fastcms&filter=status=published
```

**Search with Sorting:**
```bash
GET /api/v1/collections/posts/records?search=fastcms&sort=-created
```

### Get Record
```bash
GET /api/v1/collections/{collection_name}/records/{record_id}
```

### Create Record
```bash
POST /api/v1/collections/{collection_name}/records
Authorization: Bearer USER_TOKEN
Content-Type: application/json

{
  "data": {
    "title": "Product Name",
    "price": 99.99
  }
}
```

### Update Record
```bash
PATCH /api/v1/collections/{collection_name}/records/{record_id}
Authorization: Bearer USER_TOKEN
Content-Type: application/json

{
  "data": {
    "price": 89.99
  }
}
```

### Delete Record
```bash
DELETE /api/v1/collections/{collection_name}/records/{record_id}
Authorization: Bearer USER_TOKEN
```

## Authentication Headers

Include the access token in the Authorization header for protected endpoints:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Interactive Documentation

For complete API documentation with interactive testing, visit:

**Swagger UI:** `http://localhost:8000/docs`

This interface allows you to:
- Browse all available endpoints
- Test API calls directly from the browser
- View request/response schemas
- Authenticate and test protected endpoints
