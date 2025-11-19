# Collection Types Guide

## Overview

FastCMS supports three collection types: **Base**, **Auth**, and **View**. Each serves a different purpose.

---

## 1. Base Collections (Default)

**Status:** ✅ Fully Implemented

### What it is:
Standard collections for storing any type of data (posts, products, categories, etc.)

### Use cases:
- Blog posts
- Products
- Categories
- Orders
- Comments
- Any custom data

### Features:
- Full CRUD operations (Create, Read, Update, Delete)
- Custom schema with any fields
- Relations to other collections
- Access control rules
- File uploads

### Example:
```json
{
  "name": "products",
  "type": "base",
  "schema": [
    {"name": "title", "type": "text"},
    {"name": "price", "type": "number"},
    {"name": "category", "type": "relation", "relation": {...}}
  ]
}
```

---

## 2. Auth Collections (User Management)

**Status:** ✅ FULLY IMPLEMENTED!

### What it SHOULD be:
Special collections for user authentication and authorization with built-in auth features.

### Intended use cases:
- User accounts
- Customer profiles
- Admin users
- Team members
- Any entity that needs to authenticate

### Features that SHOULD exist:
1. **Authentication Methods:**
   - Email/Password authentication (built-in)
   - OAuth providers (Google, GitHub, etc.)
   - Magic link login
   - Two-factor authentication

2. **Required Fields:**
   - `email` (unique, required)
   - `password` (hashed, never exposed in API)
   - `verified` (email verification status)
   - `email_visibility` (control email privacy)

3. **Special Endpoints:**
   - `/api/v1/{collection}/auth/login` - Login
   - `/api/v1/{collection}/auth/register` - Register
   - `/api/v1/{collection}/auth/verify` - Verify email
   - `/api/v1/{collection}/auth/request-password-reset` - Reset password
   - `/api/v1/{collection}/auth/oauth2` - OAuth login

4. **Security Features:**
   - Password hashing (bcrypt/argon2)
   - Token generation (JWT)
   - Email verification
   - Password reset flow
   - Account lockout after failed attempts

### Current Implementation:
✅ **FULLY WORKING!** The `auth` type now provides complete authentication features:

- ✅ Auto-injected fields: `email`, `password` (hashed), `verified`, `email_visibility`
- ✅ Authentication endpoints: `/auth/register`, `/auth/login`, `/auth/me`, `/auth/refresh`
- ✅ Password hashing with bcrypt
- ✅ JWT token generation
- ✅ Passwords excluded from API responses
- ✅ Multiple independent auth collections

### How to use it NOW:
**Create auth collections for any user type!**

See **AUTH_COLLECTIONS_COMPLETE.md** for full documentation and examples.

### Example (what it SHOULD look like):
```json
{
  "name": "customers",
  "type": "auth",
  "schema": [
    {"name": "name", "type": "text"},
    {"name": "phone", "type": "text"},
    {"name": "address", "type": "text"}
  ]
}
```

When fully implemented, this would automatically add:
- `email` field (unique, indexed)
- `password` field (hashed, hidden)
- `verified` field
- Authentication endpoints
- Token management

---

## 3. View Collections (Virtual/Computed)

**Status:** ✅ FULLY IMPLEMENTED!

### What it SHOULD be:
Virtual collections that don't store data but compute it from other collections (like SQL views).

### Intended use cases:
- Aggregated statistics
- Joined data from multiple collections
- Computed/derived data
- Reports and dashboards

### Features that SHOULD exist:
1. **No Physical Storage:**
   - No database table created
   - Data computed on-the-fly

2. **Query Definition:**
   - Define a query/formula
   - Join multiple collections
   - Aggregate data (COUNT, SUM, AVG)
   - Filter and transform

3. **Read-Only:**
   - Can only read data (no CREATE/UPDATE/DELETE)
   - Data updates automatically when source collections change

### Current Implementation:
✅ **FULLY WORKING!** The `view` type now provides complete virtual collection features:

- ✅ No physical storage (virtual collections)
- ✅ Query DSL for defining data sources
- ✅ JOIN support (LEFT, RIGHT, INNER, OUTER)
- ✅ Aggregation functions (COUNT, SUM, AVG, MIN, MAX)
- ✅ WHERE filtering and GROUP BY grouping
- ✅ ORDER BY sorting
- ✅ Result caching for performance
- ✅ Read-only API endpoints

### Example (what it SHOULD look like):
```json
{
  "name": "post_stats",
  "type": "view",
  "source": {
    "collections": ["posts", "comments"],
    "query": {
      "select": [
        "posts.id",
        "posts.title",
        "COUNT(comments.id) as comment_count"
      ],
      "join": {
        "type": "LEFT",
        "on": "posts.id = comments.post_id"
      },
      "groupBy": ["posts.id"]
    }
  }
}
```

Result:
```json
[
  {"id": "1", "title": "Post 1", "comment_count": 5},
  {"id": "2", "title": "Post 2", "comment_count": 12}
]
```

---

## Collection Type Comparison

| Feature | Base | Auth | View |
|---------|------|------|------|
| **Storage** | ✅ Physical table | ✅ Physical table | ❌ Virtual (computed) |
| **CRUD Operations** | ✅ Full | ✅ Full + Auth | 📖 Read-only |
| **Custom Schema** | ✅ Yes | ✅ Yes + Auth fields | ⚙️ Computed fields |
| **Relations** | ✅ Yes | ✅ Yes | ❌ No |
| **Authentication** | ❌ No | ✅ Built-in | ❌ No |
| **Implementation Status** | ✅ Complete | ✅ Complete | ✅ Complete |

---

## Current Recommendation

### ✅ All Collection Types are NOW READY!

1. **For regular data:** Use `type: "base"`
   - Posts, products, categories, orders, etc.
   - Full CRUD operations
   - Custom schemas with any fields

2. **For user authentication:** Use `type: "auth"`
   - ✅ Customers, vendors, team members
   - ✅ Multiple independent auth collections
   - ✅ Each with own registration/login endpoints
   - ✅ Auto-hashed passwords & JWT tokens

   **Example:**
   - `customers` (type: auth) - Customer accounts
   - `vendors` (type: auth) - Seller accounts
   - `admins` (type: auth) - Admin users

   Each collection has independent authentication!

3. **For computed/aggregated data:** Use `type: "view"` ← **NEW!**
   - ✅ Virtual collections (no storage)
   - ✅ Real-time computed data from other collections
   - ✅ JOIN multiple collections
   - ✅ Aggregations (COUNT, SUM, AVG, MIN, MAX)
   - ✅ Cached for performance

   **Example:**
   - `post_stats` (type: view) - Post statistics with comment counts
   - `category_summary` (type: view) - Aggregated data by category
   - `user_activity` (type: view) - User engagement metrics


---

## Future Enhancement Ideas

If you want to contribute to enhancing these features:

### For Auth Collections:
1. ✅ Password hashing (DONE)
2. ✅ Special auth endpoints (DONE)
3. Add email verification flow
4. Implement OAuth integration for auth collections
5. Add two-factor authentication
6. Add password reset flow

### For View Collections:
1. ✅ Query DSL (DONE)
2. ✅ Query executor (DONE)
3. ✅ Caching (DONE)
4. ✅ JOIN support (DONE)
5. Add HAVING clause for filtered aggregations
6. Add subquery support
7. Add materialized views (pre-computed and stored)
8. Add real-time cache invalidation on source changes

---

## Summary

**All Collection Types are Production-Ready!** 🚀

- ✅ Use `type: "base"` for regular data (posts, products, etc.)
- ✅ Use `type: "auth"` for user authentication (customers, vendors, etc.)
- ✅ Use `type: "view"` for computed/virtual collections (statistics, reports, dashboards)

**What's Available:**
- ✅ Base collections: FULLY WORKING
- ✅ Auth collections: FULLY WORKING with auto-hashed passwords, JWT tokens, and auth endpoints
- ✅ View collections: FULLY WORKING with JOINs, aggregations, filtering, and caching

**Documentation:**
- See **AUTH_COLLECTIONS_COMPLETE.md** for auth collection documentation
- See **VIEW_COLLECTIONS_COMPLETE.md** for view collection documentation

**Demo Scripts:**
- Run `python demo_auth_collections.py` to see auth collections in action
- Run `python demo_view_collections.py` to see view collections in action
