# fastCMS User Guide

Welcome to **fastCMS** - a complete, modern Backend-as-a-Service platform! 🚀

This guide will help you get started and make the most of your fastCMS installation.

## Table of Contents

- [Getting Started](#getting-started)
- [First-Time Setup](#first-time-setup)
- [Core Concepts](#core-concepts)
- [Working with Collections](#working-with-collections)
- [Managing Records](#managing-records)
- [Authentication](#authentication)
- [File Management](#file-management)
- [Full-Text Search](#full-text-search)
- [Real-Time Subscriptions](#real-time-subscriptions)
- [Advanced Features](#advanced-features)
- [API Reference](#api-reference)
- [TypeScript SDK](#typescript-sdk)
- [Troubleshooting](#troubleshooting)

---

## Getting Started

### Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd fastCMS
   ```

2. **Install dependencies**:
   ```bash
   pip install -e .
   ```

3. **Verify installation**:
   ```bash
   fastcms --version
   ```

### System Requirements

- Python 3.10 or higher
- SQLite (built-in) or PostgreSQL
- 100MB free disk space (minimum)

---

## First-Time Setup

Welcome! Let's get your fastCMS instance up and running in just a few steps.

### Step 1: Initialize Your Project

```bash
fastcms init my-app --database sqlite
```

This creates a new fastCMS project with:
- ✅ Database configuration
- ✅ Default settings
- ✅ Sample environment file
- ✅ Initial directory structure

**Output**:
```
✨ Initializing fastCMS project: my-app
✅ Created project structure
✅ Created .env file
✅ Database configured (sqlite)

Next steps:
  1. cd my-app
  2. fastcms users create admin@example.com --password admin123 --admin
  3. fastcms dev
```

### Step 2: Create Your Admin User

This is an important step! Create your first admin user to manage the platform:

```bash
cd my-app
fastcms users create admin@example.com --password YourSecurePassword123! --admin
```

**Success Message**:
```
✅ Admin user created successfully!

Email: admin@example.com
Role: Administrator

You can now:
  • Access the API at http://localhost:8000
  • View API docs at http://localhost:8000/docs
  • Login with your credentials

Ready to start? Run: fastcms dev
```

**💡 Pro Tip**: Use a strong password! We recommend at least 8 characters with a mix of uppercase, lowercase, numbers, and special characters.

### Step 3: Start the Development Server

```bash
fastcms dev --port 8000 --reload
```

**Output**:
```
🚀 Starting fastCMS development server...
✅ Database connected
✅ Server ready at http://localhost:8000
✅ API documentation at http://localhost:8000/docs
✅ Auto-reload enabled

Press CTRL+C to stop
```

### Step 4: Verify Everything Works

Open your browser and visit:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

You should see a healthy response like:
```json
{
  "status": "healthy",
  "service": "fastCMS",
  "version": "0.2.0",
  "environment": "development",
  "readonly": false
}
```

**🎉 Congratulations! Your fastCMS is now running!**

---

## Core Concepts

### Collections

Collections are like database tables. They define the structure of your data.

**Types of Collections**:
- **Base**: Standard data collections (posts, products, etc.)
- **Auth**: User collections with built-in authentication
- **View**: Read-only virtual collections (database views)

**Example Collection**:
```json
{
  "name": "posts",
  "type": "base",
  "schema": [
    {"name": "title", "type": "text", "required": true},
    {"name": "content", "type": "text", "required": false},
    {"name": "status", "type": "select", "options": ["draft", "published"]},
    {"name": "author", "type": "relation", "collection": "users"}
  ]
}
```

### Records

Records are individual entries in a collection. Think of them as rows in a database table.

### Authentication

fastCMS supports multiple authentication methods:
- **Email/Password**: Traditional authentication
- **OAuth2**: Google, GitHub, Microsoft
- **JWT Tokens**: Secure API access

### Access Rules

Control who can do what with your data:
- `list_rule`: Who can list records
- `view_rule`: Who can view individual records
- `create_rule`: Who can create records
- `update_rule`: Who can update records
- `delete_rule`: Who can delete records
- `manage_rule`: Who can manage the collection itself

**Example Rules**:
```
@request.auth != null  // Only authenticated users
@request.auth.id = author  // Only the author
@request.auth.role = "admin"  // Only admins
```

---

## Working with Collections

### Creating a Collection (CLI)

```bash
fastcms collections create posts --schema posts.json
```

**posts.json**:
```json
{
  "name": "posts",
  "type": "base",
  "schema": [
    {"name": "title", "type": "text", "required": true},
    {"name": "content", "type": "text"},
    {"name": "published", "type": "bool", "default": false}
  ],
  "list_rule": "@request.auth != null",
  "create_rule": "@request.auth != null"
}
```

**Success Message**:
```
✅ Collection 'posts' created successfully!

Schema: 3 fields
Access Rules: Configured
API Endpoints:
  • POST   /api/v1/posts/records
  • GET    /api/v1/posts/records
  • GET    /api/v1/posts/records/{id}
  • PATCH  /api/v1/posts/records/{id}
  • DELETE /api/v1/posts/records/{id}

Next: Create your first record!
```

### Creating a Collection (API)

**Request**:
```bash
curl -X POST http://localhost:8000/api/v1/collections \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "posts",
    "type": "base",
    "schema": [
      {"name": "title", "type": "text", "required": true},
      {"name": "content", "type": "text"}
    ]
  }'
```

**Success Response** (201 Created):
```json
{
  "id": "col_abc123",
  "name": "posts",
  "type": "base",
  "schema": [...],
  "created": "2025-11-10T12:00:00Z",
  "updated": "2025-11-10T12:00:00Z",
  "message": "✅ Collection 'posts' created successfully! You can now start adding records."
}
```

### Listing Collections

**CLI**:
```bash
fastcms collections list
```

**API**:
```bash
curl http://localhost:8000/api/v1/collections \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Success Response**:
```json
{
  "items": [
    {
      "id": "col_abc123",
      "name": "posts",
      "type": "base",
      "record_count": 42
    }
  ],
  "count": 1,
  "message": "✅ Retrieved 1 collection(s)"
}
```

### Updating a Collection

**Request**:
```bash
curl -X PATCH http://localhost:8000/api/v1/collections/col_abc123 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "list_rule": "@request.auth != null"
  }'
```

**Success Response** (200 OK):
```json
{
  "id": "col_abc123",
  "name": "posts",
  "list_rule": "@request.auth != null",
  "message": "✅ Collection updated successfully!"
}
```

### Deleting a Collection

**Request**:
```bash
curl -X DELETE http://localhost:8000/api/v1/collections/col_abc123 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Success Response** (200 OK):
```json
{
  "message": "✅ Collection 'posts' and all its records have been deleted successfully."
}
```

**⚠️ Warning**: Deleting a collection also deletes all its records. This action cannot be undone.

---

## Managing Records

### Creating a Record

**Request**:
```bash
curl -X POST http://localhost:8000/api/v1/posts/records \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Post",
    "content": "Hello, world!",
    "published": true
  }'
```

**Success Response** (201 Created):
```json
{
  "id": "rec_xyz789",
  "title": "My First Post",
  "content": "Hello, world!",
  "published": true,
  "created": "2025-11-10T12:00:00Z",
  "updated": "2025-11-10T12:00:00Z",
  "message": "✅ Record created successfully!"
}
```

**Error Examples**:

**Missing Required Field** (400 Bad Request):
```json
{
  "error": "Validation failed",
  "details": {
    "title": "This field is required"
  },
  "message": "❌ Please provide all required fields and try again."
}
```

**Unauthorized** (403 Forbidden):
```json
{
  "error": "Access denied",
  "message": "❌ You don't have permission to create records in this collection. Please check your access rules or contact an administrator."
}
```

### Listing Records

**Request**:
```bash
curl "http://localhost:8000/api/v1/posts/records?page=1&limit=20&sort=-created" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Success Response** (200 OK):
```json
{
  "items": [
    {
      "id": "rec_xyz789",
      "title": "My First Post",
      "content": "Hello, world!",
      "published": true,
      "created": "2025-11-10T12:00:00Z",
      "updated": "2025-11-10T12:00:00Z"
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 1,
  "message": "✅ Retrieved 1 record(s)"
}
```

**Filtering**:
```bash
# Filter by field
curl "http://localhost:8000/api/v1/posts/records?filter=published=true"

# Multiple filters
curl "http://localhost:8000/api/v1/posts/records?filter=published=true&filter=created>2025-01-01"
```

**Sorting**:
```bash
# Sort ascending
curl "http://localhost:8000/api/v1/posts/records?sort=title"

# Sort descending (prefix with -)
curl "http://localhost:8000/api/v1/posts/records?sort=-created"
```

### Getting a Single Record

**Request**:
```bash
curl http://localhost:8000/api/v1/posts/records/rec_xyz789 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Success Response** (200 OK):
```json
{
  "id": "rec_xyz789",
  "title": "My First Post",
  "content": "Hello, world!",
  "published": true,
  "created": "2025-11-10T12:00:00Z",
  "updated": "2025-11-10T12:00:00Z",
  "message": "✅ Record retrieved successfully!"
}
```

**Error - Not Found** (404):
```json
{
  "error": "Record not found",
  "message": "❌ The record you're looking for doesn't exist or you don't have permission to view it."
}
```

### Updating a Record

**Request**:
```bash
curl -X PATCH http://localhost:8000/api/v1/posts/records/rec_xyz789 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Title",
    "published": true
  }'
```

**Success Response** (200 OK):
```json
{
  "id": "rec_xyz789",
  "title": "Updated Title",
  "content": "Hello, world!",
  "published": true,
  "updated": "2025-11-10T13:00:00Z",
  "message": "✅ Record updated successfully!"
}
```

**Error - Validation Failed** (400):
```json
{
  "error": "Validation failed",
  "details": {
    "email": "Invalid email format"
  },
  "message": "❌ Please check your input and try again."
}
```

### Deleting a Record

**Request**:
```bash
curl -X DELETE http://localhost:8000/api/v1/posts/records/rec_xyz789 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Success Response** (200 OK):
```json
{
  "message": "✅ Record deleted successfully!"
}
```

**Error - Cannot Delete** (403):
```json
{
  "error": "Access denied",
  "message": "❌ You don't have permission to delete this record."
}
```

---

## Authentication

### Registering a New User

**Request**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "passwordConfirm": "SecurePass123!"
  }'
```

**Success Response** (201 Created):
```json
{
  "user": {
    "id": "user_abc123",
    "email": "user@example.com",
    "verified": false,
    "created": "2025-11-10T12:00:00Z"
  },
  "token": "eyJhbGc...",
  "refreshToken": "ref_xyz...",
  "message": "✅ Account created successfully! Welcome to fastCMS!"
}
```

**Error - Email Already Exists** (400):
```json
{
  "error": "Email already registered",
  "message": "❌ This email is already in use. Try logging in or use a different email address."
}
```

**Error - Weak Password** (400):
```json
{
  "error": "Password too weak",
  "message": "❌ Password must be at least 8 characters long and include uppercase, lowercase, and numbers."
}
```

### Logging In

**Request**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

**Success Response** (200 OK):
```json
{
  "user": {
    "id": "user_abc123",
    "email": "user@example.com",
    "role": "user"
  },
  "token": "eyJhbGc...",
  "refreshToken": "ref_xyz...",
  "message": "✅ Login successful! Welcome back!"
}
```

**Error - Invalid Credentials** (401):
```json
{
  "error": "Authentication failed",
  "message": "❌ Invalid email or password. Please check your credentials and try again."
}
```

### Getting Current User

**Request**:
```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Success Response** (200 OK):
```json
{
  "id": "user_abc123",
  "email": "user@example.com",
  "role": "user",
  "verified": true,
  "message": "✅ Profile retrieved successfully!"
}
```

### Refreshing Token

**Request**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refreshToken": "ref_xyz..."
  }'
```

**Success Response** (200 OK):
```json
{
  "token": "eyJhbGc...",
  "refreshToken": "ref_new...",
  "message": "✅ Token refreshed successfully!"
}
```

---

## File Management

### Uploading a File

**Request**:
```bash
curl -X POST http://localhost:8000/api/v1/files \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/image.jpg" \
  -F "collection=posts" \
  -F "record=rec_xyz789" \
  -F "field=cover_image"
```

**Success Response** (201 Created):
```json
{
  "id": "file_abc123",
  "filename": "image.jpg",
  "size": 204800,
  "mimetype": "image/jpeg",
  "url": "/api/v1/files/file_abc123/download",
  "created": "2025-11-10T12:00:00Z",
  "message": "✅ File uploaded successfully!"
}
```

**Error - File Too Large** (413):
```json
{
  "error": "File too large",
  "message": "❌ File size exceeds the maximum limit of 10MB. Please upload a smaller file."
}
```

**Error - Invalid File Type** (400):
```json
{
  "error": "Invalid file type",
  "message": "❌ File type '.exe' is not allowed. Allowed types: images, documents, videos."
}
```

### Downloading a File

**Request**:
```bash
curl http://localhost:8000/api/v1/files/file_abc123/download \
  -o downloaded_file.jpg
```

### Deleting a File

**Request**:
```bash
curl -X DELETE http://localhost:8000/api/v1/files/file_abc123 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Success Response** (200 OK):
```json
{
  "message": "✅ File deleted successfully!"
}
```

---

## Full-Text Search

### Creating a Search Index

**Request**:
```bash
curl -X POST http://localhost:8000/api/v1/search/indexes \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "collection": "posts",
    "fields": ["title", "content"]
  }'
```

**Success Response** (201 Created):
```json
{
  "id": "idx_abc123",
  "collection": "posts",
  "fields": ["title", "content"],
  "status": "active",
  "message": "✅ Search index created successfully! You can now search this collection."
}
```

### Searching Records

**Request**:
```bash
curl "http://localhost:8000/api/v1/search/posts?q=hello+world&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Success Response** (200 OK):
```json
{
  "items": [
    {
      "id": "rec_xyz789",
      "title": "My First Post",
      "content": "Hello, world!",
      "rank": 0.95
    }
  ],
  "total": 1,
  "query": "hello world",
  "message": "✅ Found 1 result(s)"
}
```

**No Results** (200 OK):
```json
{
  "items": [],
  "total": 0,
  "query": "nonexistent",
  "message": "No results found for your search. Try different keywords."
}
```

### Reindexing

**Request**:
```bash
curl -X POST http://localhost:8000/api/v1/search/indexes/posts/reindex \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Success Response** (200 OK):
```json
{
  "indexed": 42,
  "message": "✅ Successfully reindexed 42 records!"
}
```

---

## Real-Time Subscriptions

Subscribe to real-time updates using Server-Sent Events (SSE).

### Subscribing to a Collection

```javascript
const eventSource = new EventSource(
  'http://localhost:8000/api/v1/realtime/posts?token=YOUR_TOKEN'
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('New event:', data);
};

// Event data structure:
{
  "action": "create",  // create, update, delete
  "record": {
    "id": "rec_xyz789",
    "title": "New Post",
    ...
  }
}
```

**Success Connection**:
```
Connected to real-time updates for 'posts'. You'll receive notifications for all changes.
```

---

## Advanced Features

### Batch Operations

Execute multiple API requests in a single call:

**Request**:
```bash
curl -X POST http://localhost:8000/api/v1/batch \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "requests": [
      {
        "method": "POST",
        "url": "/api/v1/posts/records",
        "body": {"title": "Post 1"}
      },
      {
        "method": "POST",
        "url": "/api/v1/posts/records",
        "body": {"title": "Post 2"}
      }
    ]
  }'
```

**Success Response** (200 OK):
```json
{
  "count": 2,
  "results": [
    {
      "status": 201,
      "data": {"id": "rec_1", "title": "Post 1"},
      "success": true
    },
    {
      "status": 201,
      "data": {"id": "rec_2", "title": "Post 2"},
      "success": true
    }
  ],
  "message": "✅ Batch operation completed! 2/2 requests succeeded."
}
```

### Backups

Create and manage system backups:

**Create Backup**:
```bash
curl -X POST http://localhost:8000/api/v1/backups \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Success Response** (200 OK):
```json
{
  "id": "backup_abc123",
  "filename": "backup_2025-11-10_120000.zip",
  "size_bytes": 1048576,
  "status": "completed",
  "message": "✅ Backup created successfully! Your data is safe."
}
```

**List Backups**:
```bash
curl http://localhost:8000/api/v1/backups \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Restore Backup**:
```bash
curl -X POST http://localhost:8000/api/v1/backups/backup_abc123/restore \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Settings Management

Manage system settings:

**Get Settings**:
```bash
curl http://localhost:8000/api/v1/settings \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Update Setting**:
```bash
curl -X POST http://localhost:8000/api/v1/settings \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "app_name",
    "value": "My Awesome App",
    "category": "app"
  }'
```

**Success Response** (200 OK):
```json
{
  "key": "app_name",
  "value": "My Awesome App",
  "category": "app",
  "message": "✅ Setting updated successfully!"
}
```

### Request Logs

View API request logs (admin only):

**Get Logs**:
```bash
curl "http://localhost:8000/api/v1/logs?limit=50&method=POST" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Get Statistics**:
```bash
curl http://localhost:8000/api/v1/logs/statistics \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Success Response** (200 OK):
```json
{
  "total_requests": 1234,
  "avg_duration_ms": 45,
  "errors": 12,
  "success_rate": 99.03,
  "message": "✅ Statistics retrieved successfully!"
}
```

---

## API Reference

### Base URL

```
http://localhost:8000/api/v1
```

### Authentication Header

All authenticated requests require:
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Response Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid input or validation error
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource doesn't exist
- `413 Payload Too Large` - File or request too large
- `422 Unprocessable Entity` - Semantic error in request
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Server in read-only mode

### Common Error Response Format

```json
{
  "error": "Error type",
  "message": "❌ User-friendly error message with guidance",
  "details": {
    "field": "Specific field error"
  }
}
```

### Pagination

List endpoints support pagination:
```
?page=1&limit=20
```

Response includes:
```json
{
  "items": [...],
  "page": 1,
  "limit": 20,
  "total": 100
}
```

### Filtering

Use the `filter` parameter:
```
?filter=field=value
?filter=field>value
?filter=field<value
?filter=field!=value
?filter=field~value (contains)
```

### Sorting

Use the `sort` parameter:
```
?sort=field        (ascending)
?sort=-field       (descending)
?sort=field1,-field2 (multiple)
```

### Expanding Relations

Use the `expand` parameter to load related records:
```
?expand=author
?expand=author,comments
?expand=author.profile (nested)
```

---

## TypeScript SDK

### Installation

```bash
npm install fastcms-sdk
```

### Basic Usage

```typescript
import { FastCMS } from 'fastcms-sdk';

const client = new FastCMS('http://localhost:8000');

// Authenticate
await client.auth.login('user@example.com', 'password');

// Create a record
const post = await client.collection('posts').create({
  title: 'My Post',
  content: 'Hello!'
});

// List records
const posts = await client.collection('posts').list({
  page: 1,
  limit: 20,
  filter: 'published=true',
  sort: '-created'
});

// Update a record
await client.collection('posts').update('rec_xyz789', {
  title: 'Updated Title'
});

// Delete a record
await client.collection('posts').delete('rec_xyz789');

// Subscribe to real-time updates
client.collection('posts').subscribe((event) => {
  console.log('Change detected:', event);
});

// Search
const results = await client.collection('posts').search('hello world');
```

---

## Troubleshooting

### Common Issues

#### 1. "Database connection failed"

**Problem**: Cannot connect to the database.

**Solutions**:
- Check your `DATABASE_URL` in `.env`
- Ensure the database file exists (SQLite)
- Verify PostgreSQL is running (if using PostgreSQL)
- Run migrations: `fastcms migrate up`

#### 2. "Authentication failed"

**Problem**: Cannot login or access authenticated endpoints.

**Solutions**:
- Verify your credentials are correct
- Check if your token has expired (tokens expire after 24 hours)
- Use the refresh token endpoint to get a new token
- Ensure the `Authorization` header is properly formatted

#### 3. "Access denied"

**Problem**: 403 Forbidden error when accessing resources.

**Solutions**:
- Check the collection's access rules
- Verify you're authenticated as the right user
- Ensure your user has the required role (user/admin)
- Review the `@request.auth` rules for the collection

#### 4. "Service temporarily read-only"

**Problem**: Cannot perform write operations (POST, PATCH, DELETE).

**Solution**:
- The system is in read-only mode (usually during backup)
- Wait a few moments and try again
- Check `/health` endpoint for readonly status

#### 5. "File upload failed"

**Problem**: Cannot upload files.

**Solutions**:
- Check file size (default max: 10MB)
- Verify file type is allowed
- Ensure the `data/files` directory exists and is writable
- Check available disk space

#### 6. "Search not working"

**Problem**: Search returns no results or errors.

**Solutions**:
- Create a search index first: `POST /api/v1/search/indexes`
- Reindex the collection: `POST /api/v1/search/indexes/{collection}/reindex`
- Verify the search fields are included in the index
- Check that records exist in the collection

### Getting Help

1. **Check the logs**: Look at the server console for detailed error messages
2. **API Documentation**: Visit `/docs` for interactive API documentation
3. **Health Check**: Visit `/health/detailed` to see system status
4. **GitHub Issues**: Report bugs or ask questions on GitHub

### Performance Tips

1. **Use pagination**: Don't fetch all records at once
2. **Create indexes**: Use search indexes for full-text search
3. **Optimize access rules**: Simple rules perform better
4. **Use expand wisely**: Only expand relations you need
5. **Enable caching**: Configure Redis for better performance (optional)

---

## Next Steps

Now that you're familiar with fastCMS, here are some things to try:

1. **Build your first API**:
   - Create collections for your data model
   - Set up access rules
   - Test with the TypeScript SDK

2. **Add authentication**:
   - Configure OAuth providers
   - Customize email templates
   - Set up user roles

3. **Enable search**:
   - Create search indexes
   - Build a search UI
   - Test full-text search

4. **Set up backups**:
   - Configure automated backups
   - Test restore functionality
   - Set up S3 storage (optional)

5. **Go to production**:
   - Use PostgreSQL for production
   - Configure proper security settings
   - Set up monitoring and logs

---

## Support

- **Documentation**: You're reading it! 📖
- **API Docs**: http://localhost:8000/docs
- **GitHub**: Report issues and contribute
- **Community**: Join our Discord (coming soon)

---

**Happy building with fastCMS! 🚀**

*Version 0.2.0 - Last updated: November 11, 2025*
