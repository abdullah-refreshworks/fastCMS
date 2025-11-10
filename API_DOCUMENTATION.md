# FastCMS API Documentation

Complete guide for integrating with the FastCMS API from your frontend application.

## Base URL
```
http://localhost:8000
```

## Authentication

All admin endpoints require authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

To get a token, use the authentication endpoints:

### POST /api/v1/auth/login
Login to get access token.

**Request:**
```json
{
  "email": "admin@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "user": {
    "id": "user_id",
    "email": "admin@example.com",
    "role": "admin",
    "verified": true,
    "created": "2025-11-10T00:00:00Z",
    "updated": "2025-11-10T00:00:00Z"
  },
  "token": {
    "access_token": "eyJhbGc...",
    "refresh_token": "eyJhbGc...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

---

## Admin Endpoints

### Collections Management

#### 1. List Collections
**GET** `/api/v1/admin/collections?page=1&per_page=12`

Returns all collections with pagination (including system collections).

**Query Parameters:**
- `page` (optional, default: 1) - Page number
- `per_page` (optional, default: 20, max: 100) - Items per page

**Response:**
```json
{
  "items": [
    {
      "id": "collection_id",
      "name": "posts",
      "type": "base",
      "schema": [
        {
          "name": "title",
          "type": "text",
          "validation": {
            "required": true,
            "max_length": 200
          },
          "label": "Post Title",
          "hidden": false,
          "system": false
        },
        {
          "name": "content",
          "type": "editor",
          "validation": {
            "required": true
          }
        },
        {
          "name": "author",
          "type": "relation",
          "validation": {
            "required": true
          },
          "relation": {
            "collection_id": "users_collection_id",
            "cascade_delete": false,
            "display_fields": ["name", "email"]
          }
        }
      ],
      "options": {},
      "list_rule": null,
      "view_rule": null,
      "create_rule": "@request.auth.id != ''",
      "update_rule": "@request.auth.id == author",
      "delete_rule": "@request.auth.id == author",
      "system": false,
      "created": "2025-11-10T00:00:00Z",
      "updated": "2025-11-10T00:00:00Z"
    }
  ],
  "total": 10,
  "page": 1,
  "per_page": 12,
  "total_pages": 1
}
```

#### 2. Get Collection
**GET** `/api/v1/admin/collections/{collection_id}`

Get a single collection by ID.

**Response:** Same as individual collection object above.

#### 3. Create Collection
**POST** `/api/v1/admin/collections`

Create a new collection.

**Request:**
```json
{
  "name": "posts",
  "type": "base",
  "schema": [
    {
      "name": "title",
      "type": "text",
      "validation": {
        "required": true,
        "min_length": 1,
        "max_length": 200
      },
      "label": "Post Title",
      "hint": "Enter the post title"
    },
    {
      "name": "content",
      "type": "editor",
      "validation": {
        "required": true
      },
      "label": "Content"
    },
    {
      "name": "status",
      "type": "select",
      "validation": {
        "required": true
      },
      "select": {
        "values": ["draft", "published", "archived"],
        "max_select": 1
      },
      "label": "Status"
    },
    {
      "name": "author",
      "type": "relation",
      "validation": {
        "required": true
      },
      "relation": {
        "collection_id": "users_collection_id",
        "cascade_delete": false,
        "display_fields": ["name", "email"]
      },
      "label": "Author"
    },
    {
      "name": "tags",
      "type": "select",
      "select": {
        "values": ["tech", "business", "lifestyle", "travel"],
        "max_select": 5
      },
      "label": "Tags"
    },
    {
      "name": "featured_image",
      "type": "file",
      "file": {
        "max_size": 5242880,
        "max_files": 1,
        "mime_types": ["image/jpeg", "image/png", "image/webp"],
        "thumbs": ["100x100", "500x500"]
      }
    }
  ],
  "options": {},
  "create_rule": "@request.auth.id != ''",
  "update_rule": "@request.auth.id == author",
  "delete_rule": "@request.auth.id == author"
}
```

**Response:** Returns the created collection object.

**Field Types Available:**
- `text` - Text field
- `number` - Numeric field
- `bool` - Boolean field
- `email` - Email field with validation
- `url` - URL field with validation
- `date` - Date field (ISO format)
- `datetime` - DateTime field (ISO format)
- `select` - Select/dropdown field (requires `select` options)
- `file` - File upload field (requires `file` options)
- `relation` - Relation to another collection (requires `relation` options)
- `json` - JSON field
- `editor` - Rich text editor field

#### 4. Update Collection
**PATCH** `/api/v1/admin/collections/{collection_id}`

Update an existing collection.

**Request:**
```json
{
  "name": "blog_posts",
  "schema": [
    {
      "name": "title",
      "type": "text",
      "validation": {
        "required": true,
        "max_length": 250
      }
    }
  ],
  "update_rule": "@request.auth.role == 'admin'"
}
```

**Note:** All fields are optional. Only send the fields you want to update.

**Response:** Returns the updated collection object.

#### 5. Delete Collection
**DELETE** `/api/v1/admin/collections/{collection_id}`

Delete a collection (cannot delete system collections).

**Response:** 204 No Content

---

### Users Management

#### 1. List Users
**GET** `/api/v1/admin/users?page=1&per_page=20`

Returns all users with pagination.

**Query Parameters:**
- `page` (optional, default: 1) - Page number
- `per_page` (optional, default: 20, max: 100) - Items per page

**Response:**
```json
{
  "items": [
    {
      "id": "user_id",
      "email": "user@example.com",
      "name": "John Doe",
      "avatar": "https://example.com/avatar.jpg",
      "role": "user",
      "verified": true,
      "created": "2025-11-10T00:00:00Z",
      "updated": "2025-11-10T00:00:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "per_page": 20,
  "total_pages": 3
}
```

#### 2. Get User
**GET** `/api/v1/admin/users/{user_id}`

Get a single user by ID.

**Response:** Returns user object.

#### 3. Create User
**POST** `/api/v1/admin/users`

Create a new user (admin only).

**Request:**
```json
{
  "email": "newuser@example.com",
  "password": "SecurePass123",
  "name": "Jane Doe",
  "role": "user",
  "verified": false
}
```

**Response:** Returns the created user object.

#### 4. Update User
**PATCH** `/api/v1/admin/users/{user_id}`

Update a user (admin only).

**Request:**
```json
{
  "email": "updated@example.com",
  "name": "Updated Name",
  "role": "admin",
  "verified": true,
  "password": "NewPassword123"
}
```

**Note:** All fields are optional. Password is hashed automatically.

**Response:** Returns the updated user object.

#### 5. Update User Role (Shortcut)
**PATCH** `/api/v1/admin/users/{user_id}/role?role=admin`

Quick endpoint to update just the user's role.

**Query Parameters:**
- `role` (required) - Either "user" or "admin"

**Response:** Returns the updated user object.

#### 6. Delete User
**DELETE** `/api/v1/admin/users/{user_id}`

Delete a user (admin only).

**Response:** 204 No Content

---

### System Statistics

#### Get Stats
**GET** `/api/v1/admin/stats`

Get system statistics.

**Response:**
```json
{
  "users": {
    "total": 150,
    "admins": 5,
    "recent": 12
  },
  "collections": {
    "total": 10
  }
}
```

---

## Public Collection Endpoints

These endpoints work with the collections you create.

### List Records
**GET** `/api/v1/collections/{collection_name}/records?page=1&per_page=30`

List all records from a collection (subject to list_rule).

**Query Parameters:**
- `page` (optional, default: 1)
- `per_page` (optional, default: 30, max: 100)
- `sort` (optional) - Sort by field (prefix with `-` for descending, e.g., `-created`)
- `filter` (optional) - Filter expression

**Response:**
```json
{
  "items": [
    {
      "id": "record_id",
      "title": "My First Post",
      "content": "<p>Content here</p>",
      "status": "published",
      "author": "user_id",
      "tags": ["tech", "business"],
      "created": "2025-11-10T00:00:00Z",
      "updated": "2025-11-10T00:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "per_page": 30
}
```

### Get Record
**GET** `/api/v1/collections/{collection_name}/records/{record_id}`

Get a single record (subject to view_rule).

**Response:** Returns the record object.

### Create Record
**POST** `/api/v1/collections/{collection_name}/records`

Create a new record (subject to create_rule).

**Request:**
```json
{
  "title": "My New Post",
  "content": "<p>This is the content</p>",
  "status": "draft",
  "author": "current_user_id",
  "tags": ["tech"]
}
```

**Response:** Returns the created record object.

### Update Record
**PATCH** `/api/v1/collections/{collection_name}/records/{record_id}`

Update a record (subject to update_rule).

**Request:**
```json
{
  "title": "Updated Title",
  "status": "published"
}
```

**Response:** Returns the updated record object.

### Delete Record
**DELETE** `/api/v1/collections/{collection_name}/records/{record_id}`

Delete a record (subject to delete_rule).

**Response:** 204 No Content

---

## Frontend Integration Examples

### Example: Fetch Collections

```javascript
// Using fetch API
async function getCollections() {
  const response = await fetch('http://localhost:8000/api/v1/admin/collections?page=1&per_page=12', {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    }
  });

  const data = await response.json();
  return data;
}
```

### Example: Create a Collection

```javascript
async function createCollection() {
  const collectionData = {
    name: "products",
    type: "base",
    schema: [
      {
        name: "name",
        type: "text",
        validation: { required: true, max_length: 200 },
        label: "Product Name"
      },
      {
        name: "price",
        type: "number",
        validation: { required: true, min: 0 },
        label: "Price"
      },
      {
        name: "category",
        type: "select",
        select: {
          values: ["electronics", "clothing", "books"],
          max_select: 1
        },
        label: "Category"
      }
    ],
    create_rule: "@request.auth.role == 'admin'"
  };

  const response = await fetch('http://localhost:8000/api/v1/admin/collections', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(collectionData)
  });

  return await response.json();
}
```

### Example: Create a Record

```javascript
async function createProduct() {
  const recordData = {
    name: "Laptop",
    price: 999.99,
    category: "electronics"
  };

  const response = await fetch('http://localhost:8000/api/v1/collections/products/records', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(recordData)
  });

  return await response.json();
}
```

### Example: Update a Record

```javascript
async function updateProduct(recordId) {
  const updateData = {
    price: 899.99
  };

  const response = await fetch(`http://localhost:8000/api/v1/collections/products/records/${recordId}`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(updateData)
  });

  return await response.json();
}
```

### Example: Delete a Record

```javascript
async function deleteProduct(recordId) {
  const response = await fetch(`http://localhost:8000/api/v1/collections/products/records/${recordId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });

  return response.status === 204; // true if successful
}
```

### Example: Using with React

```javascript
import { useState, useEffect } from 'react';

function CollectionsList() {
  const [collections, setCollections] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchCollections() {
      try {
        const response = await fetch('http://localhost:8000/api/v1/admin/collections', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
          }
        });
        const data = await response.json();
        setCollections(data.items);
      } catch (error) {
        console.error('Error fetching collections:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchCollections();
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h1>Collections</h1>
      {collections.map(collection => (
        <div key={collection.id}>
          <h2>{collection.name}</h2>
          <p>Type: {collection.type}</p>
          <p>Fields: {collection.schema.length}</p>
        </div>
      ))}
    </div>
  );
}
```

---

## Access Control Rules

You can use access control rules to restrict operations:

- `null` - Anyone can access
- `""` - No one can access
- `"@request.auth.id != ''"` - Authenticated users only
- `"@request.auth.role == 'admin'"` - Admin users only
- `"@request.auth.id == author"` - Only the record owner (where author is a field)

### Rule Variables:
- `@request.auth.id` - Current user's ID
- `@request.auth.email` - Current user's email
- `@request.auth.role` - Current user's role
- `@request.auth.verified` - Current user's verified status
- Field names (e.g., `author`, `user_id`) - Access record fields

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message here"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `201` - Created
- `204` - No Content (successful deletion)
- `400` - Bad Request (validation error)
- `401` - Unauthorized (missing or invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `409` - Conflict (duplicate resource)
- `500` - Internal Server Error

---

## Best Practices

1. **Always use HTTPS in production**
2. **Store tokens securely** (localStorage, sessionStorage, or httpOnly cookies)
3. **Handle token expiration** (use refresh token to get new access token)
4. **Validate data on the frontend** before sending to API
5. **Use proper error handling** for all API calls
6. **Implement loading states** for better UX
7. **Cache responses** when appropriate to reduce API calls
8. **Use pagination** for large datasets
9. **Implement proper CORS** settings in production

---

## Rate Limiting

Currently, there are no rate limits, but it's recommended to:
- Implement debouncing for search/filter inputs
- Use pagination for large datasets
- Cache responses when appropriate
- Avoid unnecessary API calls

---

## Webhook Support

Webhooks are not currently implemented but are planned for future releases.

---

## Support

For issues or questions:
- Check the error message in the API response
- Review the field validation rules
- Ensure you have proper authentication
- Verify your user has the required role/permissions
