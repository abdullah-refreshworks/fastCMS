# FastCMS User Guide

Welcome to FastCMS! This guide will help you get started with using FastCMS as an end user.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Admin Dashboard](#admin-dashboard)
3. [User Management](#user-management)
4. [Collections Management](#collections-management)
5. [Records Management](#records-management)
6. [File Management](#file-management)
7. [API Usage](#api-usage)
8. [OAuth Authentication](#oauth-authentication)

---

## Getting Started

### Accessing FastCMS

1. **Start the Server**
   ```bash
   python app/main.py
   ```
   The server will start at `http://localhost:8000`

2. **Access Points**
   - API Documentation: `http://localhost:8000/docs`
   - Admin Dashboard: `http://localhost:8000/admin/`
   - Health Check: `http://localhost:8000/health`

### First-Time Setup

1. **Create Your First User**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "yourname@example.com",
       "password": "YourSecurePass123",
       "password_confirm": "YourSecurePass123",
       "name": "Your Name"
     }'
   ```

2. **Make Yourself Admin** (requires database access)
   ```bash
   # Using Python
   python3 << EOF
   import sqlite3
   conn = sqlite3.connect('data/app.db')
   cursor = conn.cursor()
   cursor.execute("UPDATE users SET role = 'admin' WHERE email = 'yourname@example.com'")
   conn.commit()
   conn.close()
   EOF
   ```

---

## Admin Dashboard

The Admin Dashboard provides a visual interface to manage your FastCMS instance.

### Accessing the Dashboard

1. Navigate to `http://localhost:8000/admin/`
2. Login with your admin credentials
3. Store your access token in browser localStorage:
   ```javascript
   localStorage.setItem('access_token', 'YOUR_TOKEN_HERE');
   ```

### Dashboard Overview

The main dashboard shows:
- **Total Users**: Number of registered users
- **Admin Count**: Number of admin users
- **New Users (7d)**: Recently registered users
- **Total Collections**: Number of collections created
- **Quick Actions**: Links to manage users, collections, and API docs

---

## User Management

### Viewing Users

1. Go to **Admin Dashboard** → **Users**
2. View all registered users with their:
   - Email address
   - Name
   - Role (user/admin)
   - Verification status
   - Registration date

### Managing User Roles

**Promote to Admin:**
1. Find the user in the users list
2. Click "Promote" button
3. Confirm the action

**Demote to User:**
1. Find the admin user
2. Click "Demote" button
3. Confirm the action

### Deleting Users

1. Find the user in the users list
2. Click "Delete" button
3. Confirm the action (this cannot be undone)

---

## Collections Management

Collections are like database tables with dynamic schemas.

### Creating a Collection

**Via Admin Dashboard:**
1. Go to **Collections** tab
2. Click "Create Collection" button
3. Fill in:
   - **Name**: Unique identifier (letters, numbers, underscore)
   - **Type**: base, auth, or view
   - **Schema**: Define your fields

**Via API:**
```bash
curl -X POST "http://localhost:8000/api/v1/collections" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "posts",
    "type": "base",
    "schema": [
      {
        "name": "title",
        "type": "text",
        "validation": {"required": true}
      },
      {
        "name": "content",
        "type": "editor",
        "validation": {}
      },
      {
        "name": "published",
        "type": "bool",
        "validation": {}
      }
    ]
  }'
```

### Field Types

FastCMS supports these field types:

| Type | Description | Example Use |
|------|-------------|-------------|
| `text` | Short text string | Titles, names |
| `editor` | Rich text HTML | Article content |
| `number` | Numeric value | Age, price, count |
| `bool` | True/false | Published, active |
| `email` | Email address | Contact email |
| `url` | Web URL | Website links |
| `date` | Date only | Birth date |
| `datetime` | Date and time | Created timestamp |
| `select` | Dropdown | Category, status |
| `file` | File upload | Images, documents |
| `relation` | Link to another collection | Author, category |
| `json` | Structured data | Metadata, settings |

### Viewing Collection Details

1. Go to **Collections** tab
2. Click "View Details" on any collection
3. See:
   - Schema fields
   - Field types and validation
   - Access control rules

### Deleting Collections

1. Find the collection
2. Click "Delete" button
3. Confirm (this deletes all records too!)

**Note:** System collections cannot be deleted.

---

## Records Management

Records are the actual data entries in your collections.

### Creating a Record

```bash
curl -X POST "http://localhost:8000/api/v1/posts/records" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "title": "My First Post",
      "content": "<p>Hello World!</p>",
      "published": true
    }
  }'
```

### Listing Records

```bash
curl -X GET "http://localhost:8000/api/v1/posts/records" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**With Pagination:**
```bash
curl -X GET "http://localhost:8000/api/v1/posts/records?page=1&per_page=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Filtering Records

FastCMS uses PocketBase-style filter syntax:

**Examples:**
```bash
# Greater than or equal
curl "http://localhost:8000/api/v1/products/records?filter=price>=100"

# Multiple conditions (AND)
curl "http://localhost:8000/api/v1/users/records?filter=age>=18&&status=active"

# Text search (contains)
curl "http://localhost:8000/api/v1/posts/records?filter=title~FastCMS"

# Sorting (descending with -)
curl "http://localhost:8000/api/v1/posts/records?sort=-created"
```

**Supported Operators:**
- `=` Equal
- `!=` Not equal
- `>` Greater than
- `<` Less than
- `>=` Greater than or equal
- `<=` Less than or equal
- `~` Contains (like)
- `&&` AND condition

### Updating a Record

```bash
curl -X PATCH "http://localhost:8000/api/v1/posts/records/RECORD_ID" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "title": "Updated Title",
      "published": false
    }
  }'
```

### Deleting a Record

```bash
curl -X DELETE "http://localhost:8000/api/v1/posts/records/RECORD_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## File Management

### Uploading Files

**Via Admin Dashboard:**
1. Go to **Files** tab
2. Click "Upload File" button
3. Select your file
4. Click "Upload"

**Via API:**
```bash
curl -X POST "http://localhost:8000/api/v1/files" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/your/file.jpg"
```

### Viewing Files

1. Go to **Files** tab in Admin Dashboard
2. Browse uploaded files
3. Click on images to preview
4. See file details (name, size, type)

### Downloading Files

Access files via:
```
http://localhost:8000/api/v1/files/FILE_ID
```

### Deleting Files

1. Go to **Files** tab
2. Hover over the file
3. Click the trash icon
4. Confirm deletion

---

## API Usage

### Authentication

FastCMS uses JWT tokens for authentication.

**1. Register:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123",
    "password_confirm": "SecurePass123",
    "name": "John Doe"
  }'
```

**2. Login:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123"
  }'
```

Response includes:
- `access_token`: Use for API requests (expires in 15 min)
- `refresh_token`: Use to get new access token (expires in 30 days)

**3. Using Tokens:**
```bash
curl -X GET "http://localhost:8000/api/v1/collections" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**4. Refreshing Tokens:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

### Access Control Rules

Collections can have permission rules:

**Rule Syntax:**
- `null` or `""`: Public (anyone can access)
- `@request.auth.id != ''`: Authenticated users only
- `@request.auth.id = @record.user_id`: Owner only
- `@request.auth.role = 'admin'`: Admin only
- Multiple conditions: `@request.auth.id = @record.user_id || @request.auth.role = 'admin'`

**Rule Types:**
- `list_rule`: Who can list records
- `view_rule`: Who can view a single record
- `create_rule`: Who can create records
- `update_rule`: Who can update records
- `delete_rule`: Who can delete records

**Example:**
```json
{
  "name": "posts",
  "list_rule": "",
  "view_rule": "",
  "create_rule": "@request.auth.id != ''",
  "update_rule": "@request.auth.id = @record.user_id || @request.auth.role = 'admin'",
  "delete_rule": "@request.auth.role = 'admin'"
}
```

---

## OAuth Authentication

FastCMS supports social login with Google, GitHub, and Microsoft.

### Setup OAuth Providers

**1. Google:**
- Go to [Google Cloud Console](https://console.cloud.google.com)
- Create OAuth 2.0 credentials
- Add redirect URI: `http://localhost:8000/api/v1/oauth/callback/google`
- Add to `.env`:
  ```
  GOOGLE_CLIENT_ID=your_client_id
  GOOGLE_CLIENT_SECRET=your_client_secret
  ```

**2. GitHub:**
- Go to GitHub Settings → Developer settings → OAuth Apps
- Create new OAuth App
- Callback URL: `http://localhost:8000/api/v1/oauth/callback/github`
- Add to `.env`:
  ```
  GITHUB_CLIENT_ID=your_client_id
  GITHUB_CLIENT_SECRET=your_client_secret
  ```

**3. Microsoft:**
- Go to [Azure Portal](https://portal.azure.com)
- Register application
- Redirect URI: `http://localhost:8000/api/v1/oauth/callback/microsoft`
- Add to `.env`:
  ```
  MICROSOFT_CLIENT_ID=your_client_id
  MICROSOFT_CLIENT_SECRET=your_client_secret
  ```

### Using OAuth

**Login with OAuth:**
Visit in your browser:
```
http://localhost:8000/api/v1/oauth/login/google
http://localhost:8000/api/v1/oauth/login/github
http://localhost:8000/api/v1/oauth/login/microsoft
```

The flow will:
1. Redirect to OAuth provider
2. You authorize the app
3. Redirect back with tokens
4. Returns same JWT tokens as regular login

**List Linked Accounts:**
```bash
curl -X GET "http://localhost:8000/api/v1/oauth/accounts" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Unlink OAuth Account:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/oauth/accounts/google" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Tips and Best Practices

### Security

1. **Use Strong Passwords**: At least 8 characters with letters and numbers
2. **Keep Tokens Secret**: Never share your access tokens
3. **Use HTTPS in Production**: Always use SSL/TLS in production
4. **Regular Backups**: Backup your database regularly
5. **Update Dependencies**: Keep FastCMS and dependencies updated

### Performance

1. **Use Pagination**: Always paginate large result sets
2. **Filter at Query Time**: Use filters instead of fetching all records
3. **Index Your Fields**: Add validation.unique for frequently queried fields
4. **Optimize Images**: Compress images before uploading

### Best Practices

1. **Plan Your Schema**: Design your collections before creating them
2. **Use Relations**: Link collections instead of duplicating data
3. **Set Access Rules**: Always configure appropriate access control
4. **Test in Development**: Test changes in development before production
5. **Document Your API**: Keep track of your custom collections and fields

---

## Troubleshooting

### Common Issues

**Cannot Login to Admin Dashboard:**
- Ensure you're an admin: Check `role` field in database
- Check you're using correct email/password
- Verify token is stored in localStorage

**Collection Creation Fails:**
- Check collection name is unique
- Ensure name uses only letters, numbers, underscore
- Verify schema is valid JSON

**Record Creation Fails:**
- Check required fields are provided
- Verify data types match schema
- Ensure you have create permission

**File Upload Fails:**
- Check file size (default max: 10MB)
- Verify file type is allowed
- Ensure you're authenticated

### Getting Help

- **API Documentation**: http://localhost:8000/docs
- **GitHub Issues**: Report bugs on GitHub
- **Logs**: Check console output for error details

---

## Summary

You now know how to:
- ✓ Access the admin dashboard
- ✓ Manage users and roles
- ✓ Create and manage collections
- ✓ Perform CRUD operations on records
- ✓ Upload and manage files
- ✓ Use the REST API
- ✓ Set up OAuth authentication
- ✓ Configure access control rules

Happy building with FastCMS! 🚀
