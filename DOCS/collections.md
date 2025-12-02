# Collections

FastCMS supports three types of collections:

## 1. Base Collections

Standard collections for storing any type of data.

**Use cases:**
- Products
- Blog posts
- Comments
- Orders
- Any custom data

**Features:**
- Define custom schema with any field types
- Full CRUD operations via API
- Access control rules
- Automatic timestamps (created, updated)

## 2. Auth Collections

Special collections designed for user authentication. Auth collections automatically include authentication fields and endpoints.

**Automatically added fields:**
- `email` (unique, indexed)
- `password` (hashed with bcrypt)
- `verified` (boolean, email verification status)
- `role` (string, user role)
- `token_key` (string, for session invalidation)

**Automatically created endpoints:**
- `POST /api/v1/collections/{collection_name}/auth/register` - Register new users
- `POST /api/v1/collections/{collection_name}/auth/login` - Login users
- `POST /api/v1/collections/{collection_name}/auth/refresh` - Refresh access token

**Use cases:**
- Customer accounts
- Vendor portals
- Team member access
- Any user type requiring authentication

**Example:**
Create a "customers" auth collection to allow customers to register, login, and manage their data.

## 3. View Collections

Virtual collections that compute data from other collections. Views do not store data but execute SQL queries to aggregate or join data from existing collections.

**Features:**
- Define SQL SELECT queries
- Support for JOINs, GROUP BY, ORDER BY
- Configurable caching (TTL in seconds)
- Read-only (no create, update, delete)

**Use cases:**
- Sales reports
- User statistics
- Aggregated data
- Joined data from multiple collections

**Example:**
Create a "sales_summary" view to show total sales per product by aggregating order data.

## Creating Collections

### Via Admin Dashboard

1. Navigate to `http://localhost:8000/admin/collections`
2. Click "Create Collection"
3. Fill in the form:
   - **Name:** Collection name (lowercase, letters, numbers, underscores only)
   - **Type:** Choose base, auth, or view
   - **Schema:** Define fields (for base/auth types)
   - **Query Configuration:** Define SQL query (for view types only)
4. Click "Create Collection"

### Via API

```bash
curl -X POST http://localhost:8000/api/v1/collections \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "products",
    "type": "base",
    "schema": [
      {
        "name": "title",
        "type": "text",
        "validation": {"required": true}
      },
      {
        "name": "price",
        "type": "number",
        "validation": {"required": true}
      }
    ]
  }'
```

## Next Steps

- [Learn about Field Types](field-types.md)
- [Set up Access Control](access-control.md)
- [Use the API](api-reference.md)
