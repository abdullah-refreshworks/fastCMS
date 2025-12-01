# FastCMS Documentation

FastCMS is a headless CMS built with FastAPI and SQLite. It provides dynamic collection management, authentication, and access control through a web-based admin interface and REST API.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Collection Types](#collection-types)
3. [Creating Collections](#creating-collections)
4. [Authentication System](#authentication-system)
5. [Email Verification & Password Reset](#email-verification--password-reset)
6. [CSV Import/Export](#csv-importexport)
7. [Access Control Rules](#access-control-rules)
8. [API Usage](#api-usage)
9. [Field Types](#field-types)

---

## Getting Started

### Installation

```bash
# Install dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Access the Admin Dashboard

Navigate to `http://localhost:8000/admin` in your browser. On first run, you will be prompted to create an admin account.

---

## Collection Types

FastCMS supports three types of collections:

### 1. Base Collections

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

### 2. Auth Collections

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

### 3. View Collections

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

---

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

---

## Authentication System

FastCMS has two authentication systems:

### 1. Built-in Admin Authentication

The `users` table is for admin dashboard access only.

**Roles:**
- `admin` - Full access to admin dashboard and all collections
- `user` - Limited access (typically not used)

**Endpoints:**
- `POST /api/v1/auth/login` - Admin login
- `POST /api/v1/auth/register` - Create admin users (requires admin token)
- `POST /api/v1/auth/refresh` - Refresh admin access token

### 2. Auth Collections (Custom User Systems)

Create auth collections for your own user systems (customers, vendors, etc.).

**Example: Customer Authentication**

1. Create "customers" auth collection
2. Customers can register at: `POST /api/v1/collections/customers/auth/register`
3. Customers can login at: `POST /api/v1/collections/customers/auth/login`

**Registration Example:**

```bash
curl -X POST http://localhost:8000/api/v1/collections/customers/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "customer@example.com",
    "password": "securepassword123"
  }'
```

**Login Example:**

```bash
curl -X POST http://localhost:8000/api/v1/collections/customers/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "customer@example.com",
    "password": "securepassword123"
  }'
```

**Response:**

```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "customer@example.com",
    "verified": false,
    "role": "user"
  }
}
```

---

## Email Verification & Password Reset

FastCMS includes a complete email verification and password reset system for both admin users and auth collection users.

### SMTP Configuration

First, configure your SMTP settings in the `.env` file:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@fastcms.dev
SMTP_FROM_NAME=FastCMS
```

**Gmail Setup:**
1. Enable 2-factor authentication on your Google account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the app password in `SMTP_PASSWORD`

**Other SMTP Providers:**
- **SendGrid**: Use `smtp.sendgrid.net` on port 587
- **Mailgun**: Use `smtp.mailgun.org` on port 587
- **AWS SES**: Use your SES SMTP endpoint

### Email Verification Flow

When a user registers, they receive a verification email with a token.

**1. User Registration (Email Sent Automatically)**

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "name": "John Doe"
  }'
```

The user will receive an email with a verification link like:
```
http://localhost:8000/verify?token=abc123...
```

**2. Verify Email**

```bash
curl -X POST http://localhost:8000/api/v1/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{
    "token": "abc123..."
  }'
```

**Response:**
```json
{
  "message": "Email verified successfully",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "verified": true
  }
}
```

**3. Resend Verification Email**

If the token expires (valid for 24 hours), users can request a new one:

```bash
curl -X POST http://localhost:8000/api/v1/auth/resend-verification \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### Password Reset Flow

**1. Request Password Reset**

```bash
curl -X POST http://localhost:8000/api/v1/auth/request-password-reset \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

**Response:**
```json
{
  "message": "If the email exists, a password reset link has been sent"
}
```

The user will receive an email with a reset link like:
```
http://localhost:8000/reset-password?token=xyz789...
```

**2. Reset Password**

```bash
curl -X POST http://localhost:8000/api/v1/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "xyz789...",
    "new_password": "NewSecurePass456!",
    "password_confirm": "NewSecurePass456!"
  }'
```

**Response:**
```json
{
  "message": "Password reset successfully"
}
```

### Auth Collections Email Support

Email verification and password reset also work for auth collections (customers, vendors, etc.):

**Registration (Sends Verification Email):**
```bash
curl -X POST http://localhost:8000/api/v1/collections/customers/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "customer@example.com",
    "password": "SecurePass123!"
  }'
```

**Request Password Reset:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/request-password-reset \
  -H "Content-Type: application/json" \
  -d '{
    "email": "customer@example.com",
    "collection": "customers"
  }'
```

### Email Templates

Email templates are HTML-based and include:
- **Verification Email**: Welcome message with verification button
- **Password Reset Email**: Security notice with reset button

Templates are located in `app/services/email_service.py` and can be customized.

### Token Security

- **Verification Tokens**: Valid for 24 hours, single-use
- **Password Reset Tokens**: Valid for 1 hour, single-use
- Tokens are cryptographically secure random strings
- Used tokens are marked and cannot be reused

### Troubleshooting

**Email Not Sending:**
1. Check SMTP credentials in `.env`
2. Verify SMTP host/port are correct
3. Check firewall allows outbound SMTP connections
4. Review server logs for SMTP errors

**Gmail "Less Secure Apps" Error:**
- Don't use "less secure apps" - use App Passwords instead
- Enable 2FA and generate an app-specific password

**Email Goes to Spam:**
- Configure SPF/DKIM records for your domain
- Use a professional email service (SendGrid, Mailgun)
- Avoid localhost/development domains in production

---

## CSV Import/Export

FastCMS allows you to easily import and export data from collections in CSV (Comma-Separated Values) format. This is useful for data migration, backups, bulk editing, and integration with spreadsheet applications like Excel or Google Sheets.

### What is CSV Import/Export?

**CSV Export** downloads all records from a collection into a CSV file that can be opened in Excel, Google Sheets, or any text editor.

**CSV Import** uploads a CSV file to create multiple records in a collection at once. This is much faster than creating records one by one.

### Via Admin Dashboard

The easiest way to use CSV import/export is through the admin dashboard.

#### Exporting Records to CSV

1. Navigate to any collection's records page (e.g., `http://localhost:8000/admin/collections/products/records`)
2. Click the **"Export CSV"** button at the top of the page
3. Your browser will download a CSV file named `{collection_name}_export.csv`
4. Open the file in Excel, Google Sheets, or any text editor

The exported CSV will include:
- System fields: `id`, `created`, `updated`
- All custom fields defined in the collection schema
- Proper formatting for dates, numbers, and boolean values

#### Importing Records from CSV

1. Navigate to the collection's records page
2. Click the **"Import CSV"** button at the top of the page
3. Select your CSV file in the modal dialog
4. Optionally check **"Skip validation"** if you want to import all data as text without type checking
5. Click **"Import"**

The import will show:
- Number of records successfully imported
- Total records in the CSV file
- Any errors that occurred (with row numbers)

**Important Notes:**
- The first row of your CSV must contain field names matching your collection schema
- System fields (`id`, `created`, `updated`) will be ignored if present
- Empty values will be skipped
- Invalid data types will cause errors (unless "Skip validation" is checked)

### Via API

You can also use CSV import/export programmatically through the REST API.

#### Export Records to CSV

```bash
curl -X GET "http://localhost:8000/api/v1/collections/products/records/export/csv" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -o products_export.csv
```

The response will be a CSV file that you can save or process.

**With Filters and Sorting:**

```bash
# Export only active products, sorted by price
curl -X GET "http://localhost:8000/api/v1/collections/products/records/export/csv?filter=active=true&sort=-price" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -o active_products.csv
```

**Query Parameters:**
- `filter` - Filter expression (e.g., `price>=100&&active=true`)
- `sort` - Sort field (prefix with `-` for descending)

**Export Limit:** Maximum 10,000 records per export

#### Import Records from CSV

```bash
curl -X POST "http://localhost:8000/api/v1/collections/products/records/import/csv" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@products.csv"
```

**Response:**
```json
{
  "imported": 95,
  "total": 100,
  "errors": [
    {
      "row": 23,
      "error": "Row 23, field 'price': Cannot convert 'invalid' to number"
    },
    {
      "row": 45,
      "error": "Row 45, field 'email': Invalid email format"
    }
  ]
}
```

**With Skip Validation:**

```bash
# Import all data as text, skip type validation
curl -X POST "http://localhost:8000/api/v1/collections/products/records/import/csv?skip_validation=true" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@products.csv"
```

### CSV Format Examples

#### Simple Example: Products

**CSV File (products.csv):**
```csv
name,price,active
Laptop,999.99,true
Mouse,29.99,true
Keyboard,79.99,false
Monitor,299.99,true
```

**Import Result:** 4 records created

#### Example with Different Field Types

**Collection Schema:**
- `title` (text)
- `quantity` (number)
- `published` (bool)
- `publish_date` (date)
- `tags` (select, multi-select)

**CSV File:**
```csv
title,quantity,published,publish_date,tags
"First Product",100,true,2025-01-15T10:00:00,"[""electronics"", ""sale""]"
"Second Product",50,false,2025-02-01T14:30:00,"[""clothing""]"
```

**Notes:**
- Dates should be in ISO 8601 format
- Boolean values: `true/false`, `1/0`, `yes/no`, `y/n`
- Multi-select and arrays: Use JSON array format `["value1", "value2"]`
- Text with commas: Wrap in double quotes `"text, with comma"`

### Export-Import Workflow (Data Migration)

A common use case is to export data from one collection and import it into another:

**Step 1: Export from source collection**
```bash
curl -X GET "http://localhost:8000/api/v1/collections/old_products/records/export/csv" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o products_backup.csv
```

**Step 2: Create target collection with matching schema**

Create a new collection with the same field names and types as the source.

**Step 3: Import to target collection**
```bash
curl -X POST "http://localhost:8000/api/v1/collections/new_products/records/import/csv" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@products_backup.csv"
```

**Step 4: Verify import**
```bash
curl -X GET "http://localhost:8000/api/v1/collections/new_products/records" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Handling Large Datasets

For collections with more than 10,000 records:

1. **Export in batches using filters:**
```bash
# Export first 10,000
curl "http://localhost:8000/api/v1/collections/products/records/export/csv?filter=id>0&sort=id"

# Export next batch
curl "http://localhost:8000/api/v1/collections/products/records/export/csv?filter=id>last_id&sort=id"
```

2. **Import in batches:**
   - Split your CSV file into smaller files (e.g., 5,000 records each)
   - Import each file separately
   - Check for errors after each batch

### Troubleshooting

**Import Fails with "Invalid CSV format":**
- Ensure the first row contains field names
- Check that the CSV is properly formatted (use a CSV validator)
- Try opening the file in Excel to verify structure

**Import Partially Succeeds:**
- Check the `errors` array in the response for specific row errors
- Fix the problematic rows in your CSV
- Re-import the corrected CSV (duplicates will be created unless you delete first)

**Boolean Values Not Working:**
- Use accepted formats: `true/false`, `1/0`, `yes/no`, `y/n`
- Values are case-insensitive

**Date Fields Import as Text:**
- Ensure dates are in ISO 8601 format: `2025-01-15T10:00:00`
- Or use simple date format: `2025-01-15`

**Special Characters Cause Issues:**
- Ensure your CSV is UTF-8 encoded
- Wrap text with special characters in double quotes
- Escape double quotes inside text by doubling them: `"He said ""hello"""`

### Access Control

CSV import/export respects collection access control rules:

- **Export**: Requires list permission on the collection
- **Import**: Requires create permission on the collection

If you get a 403 error:
- Check the collection's `list_rule` for export
- Check the collection's `create_rule` for import
- Verify your access token has the necessary permissions

---

## Bulk Operations

FastCMS provides bulk operations to efficiently update or delete multiple records at once. Instead of making individual API calls for each record, you can process up to 100 records in a single request.

### Features

- **Bulk Delete**: Delete multiple records in one operation
- **Bulk Update**: Update the same field(s) across multiple records
- **Partial Success Handling**: Operations continue even if some records fail
- **Detailed Error Reporting**: Get specific error messages for failed operations
- **Access Control**: Respects collection permissions for each record

### Via Admin UI

#### Selecting Records

1. Navigate to any collection's records page
2. Use checkboxes to select records:
   - **Select individual records**: Click the checkbox next to each record
   - **Select all records**: Click the checkbox in the table header
3. Selected count is displayed in the header

#### Bulk Delete

1. Select the records you want to delete
2. Click the **Delete Selected** button
3. Confirm the deletion in the dialog
4. See the operation summary (successful and failed counts)

#### Bulk Update

1. Select the records you want to update
2. Click the **Update Selected** button
3. In the modal:
   - Choose which field to update from the dropdown
   - Enter the new value for that field
   - Click **Update Records**
4. See the operation summary (successful and failed counts)

### Via API

#### Bulk Delete Records

Delete multiple records in a single request.

**Endpoint:** `POST /api/v1/collections/{collection_name}/records/bulk-delete`

**Request Body:**
```json
{
  "record_ids": [
    "record_id_1",
    "record_id_2",
    "record_id_3"
  ]
}
```

**Response:**
```json
{
  "success": 2,
  "failed": 1,
  "errors": [
    {
      "record_id": "record_id_3",
      "error": "Record not found"
    }
  ]
}
```

**Example - cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/collections/posts/records/bulk-delete" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "record_ids": ["abc123", "def456", "ghi789"]
  }'
```

**Example - Python:**
```python
import requests

response = requests.post(
    'http://localhost:8000/api/v1/collections/posts/records/bulk-delete',
    json={
        'record_ids': ['abc123', 'def456', 'ghi789']
    },
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)

result = response.json()
print(f"Successfully deleted: {result['success']}")
print(f"Failed: {result['failed']}")
if result['errors']:
    print(f"Errors: {result['errors']}")
```

**Example - JavaScript:**
```javascript
const response = await fetch('http://localhost:8000/api/v1/collections/posts/records/bulk-delete', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN'
  },
  body: JSON.stringify({
    record_ids: ['abc123', 'def456', 'ghi789']
  })
});

const result = await response.json();
console.log(`Successfully deleted: ${result.success}`);
console.log(`Failed: ${result.failed}`);
if (result.errors) {
  console.log('Errors:', result.errors);
}
```

#### Bulk Update Records

Update the same field(s) across multiple records.

**Endpoint:** `POST /api/v1/collections/{collection_name}/records/bulk-update`

**Request Body:**
```json
{
  "record_ids": [
    "record_id_1",
    "record_id_2",
    "record_id_3"
  ],
  "data": {
    "status": "published",
    "priority": 1
  }
}
```

**Response:**
```json
{
  "success": 3,
  "failed": 0,
  "errors": null
}
```

**Example - cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/collections/posts/records/bulk-update" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "record_ids": ["abc123", "def456"],
    "data": {
      "status": "published",
      "featured": true
    }
  }'
```

**Example - Python:**
```python
import requests

response = requests.post(
    'http://localhost:8000/api/v1/collections/posts/records/bulk-update',
    json={
        'record_ids': ['abc123', 'def456'],
        'data': {
            'status': 'published',
            'featured': True
        }
    },
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)

result = response.json()
print(f"Successfully updated: {result['success']}")
print(f"Failed: {result['failed']}")
```

**Example - JavaScript:**
```javascript
const response = await fetch('http://localhost:8000/api/v1/collections/posts/records/bulk-update', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN'
  },
  body: JSON.stringify({
    record_ids: ['abc123', 'def456'],
    data: {
      status: 'published',
      featured: true
    }
  })
});

const result = await response.json();
console.log(`Successfully updated: ${result.success}`);
console.log(`Failed: ${result.failed}`);
```

### Limitations

- **Maximum 100 records per request** - If you need to process more, split into multiple requests
- **At least 1 record required** - You must provide at least one record ID
- **Authentication required** - Bulk operations require a valid access token
- **Sequential processing** - Records are processed one by one, not in parallel

### Error Handling

Bulk operations use **partial success** - if some records fail, the operation continues processing the remaining records.

**Success Response (all succeeded):**
```json
{
  "success": 5,
  "failed": 0,
  "errors": null
}
```

**Partial Success Response:**
```json
{
  "success": 3,
  "failed": 2,
  "errors": [
    {
      "record_id": "abc123",
      "error": "Record not found"
    },
    {
      "record_id": "def456",
      "error": "Insufficient permissions"
    }
  ]
}
```

**Common Error Scenarios:**

**Record Not Found:**
- The record ID doesn't exist in the collection
- The record was already deleted
- **Solution**: Verify the record ID is correct

**Insufficient Permissions:**
- User doesn't have delete/update permission on that record
- Collection access rules deny the operation
- **Solution**: Check collection access rules and user permissions

**Validation Errors:**
- Update data doesn't match field types
- Required fields are missing
- **Solution**: Ensure update data matches collection schema

### Best Practices

**1. Check Results**
Always check the response to see if any operations failed:
```python
result = bulk_delete(record_ids)
if result['failed'] > 0:
    print(f"Warning: {result['failed']} records failed")
    for error in result['errors']:
        print(f"  - {error['record_id']}: {error['error']}")
```

**2. Batch Large Operations**
For more than 100 records, split into batches:
```python
def bulk_delete_all(record_ids, batch_size=100):
    for i in range(0, len(record_ids), batch_size):
        batch = record_ids[i:i + batch_size]
        result = bulk_delete(batch)
        print(f"Batch {i//batch_size + 1}: {result['success']} deleted")
```

**3. Validate Before Bulk Update**
Ensure your update data is valid:
```python
# Get collection schema first
collection = get_collection('posts')

# Validate update data matches schema
update_data = {'status': 'published'}
# Then perform bulk update
bulk_update(record_ids, update_data)
```

**4. Use Transactions for Critical Operations**
For important operations, consider processing records individually with proper error handling instead of bulk operations if you need transactional guarantees.

### Access Control

Bulk operations respect collection access control rules:

- **Bulk Delete**: Requires delete permission on each individual record
- **Bulk Update**: Requires update permission on each individual record

**How It Works:**
- Each record is checked against the collection's access rules
- Records the user doesn't have permission for will fail
- Permitted records will be processed successfully

**Example:**
If a collection has `delete_rule = "@request.auth.id = @record.user_id"`:
- User can only delete their own records
- Bulk delete of 10 records where user owns 7 will succeed for 7, fail for 3

### Performance Considerations

- **API overhead**: One request instead of N requests saves significant overhead
- **Database operations**: Still performs N individual database operations
- **Best for**: 10-100 records at a time
- **Not ideal for**: Thousands of records (consider background jobs instead)

**Estimated Performance:**
- 10 records: ~100-200ms
- 50 records: ~500ms-1s
- 100 records: ~1-2s

---

## Access Control Rules

Every collection has five access control rules that determine who can perform which operations.

### Rule Types

1. **list_rule** - Who can list/search records
2. **view_rule** - Who can view a single record
3. **create_rule** - Who can create new records
4. **update_rule** - Who can update records
5. **delete_rule** - Who can delete records

### Rule Syntax

**Available Variables:**
- `@request.auth.id` - Current logged-in user's ID
- `@request.auth.role` - Current user's role
- `@request.auth.email` - Current user's email
- `@record.field_name` - Value of any field in the record

**Operators:**
- `=` equals
- `!=` not equals
- `&&` AND
- `||` OR

### Common Rule Patterns

#### Public Access
```
list_rule: null
```
Everyone can access (no authentication required).

#### Authenticated Users Only
```
list_rule: "@request.auth.id != ''"
```
Only logged-in users can list records.

#### Admin Only
```
list_rule: "@request.auth.role = 'admin'"
create_rule: "@request.auth.role = 'admin'"
delete_rule: "@request.auth.role = 'admin'"
```
Only admin users can access.

#### Owner Only
```
list_rule: "@request.auth.id = @record.user_id"
update_rule: "@request.auth.id = @record.user_id"
```
Users can only see/edit records they own.

#### Owner OR Admin
```
update_rule: "@request.auth.id = @record.user_id || @request.auth.role = 'admin'"
delete_rule: "@request.auth.id = @record.user_id || @request.auth.role = 'admin'"
```
Record owner OR admin can update/delete.

### Real-World Example: Vendor System

**Scenario:** You want vendors to manage their own products but not see other vendors' products.

**Step 1: Create "vendors" auth collection**
```json
{
  "name": "vendors",
  "type": "auth"
}
```

**Step 2: Create "products" base collection**
```json
{
  "name": "products",
  "type": "base",
  "schema": [
    {
      "name": "vendor_id",
      "type": "text",
      "validation": {"required": true}
    },
    {
      "name": "name",
      "type": "text",
      "validation": {"required": true}
    },
    {
      "name": "price",
      "type": "number",
      "validation": {"required": true}
    }
  ],
  "list_rule": "@request.auth.id = @record.vendor_id",
  "view_rule": "@request.auth.id = @record.vendor_id",
  "create_rule": "@request.auth.id != ''",
  "update_rule": "@request.auth.id = @record.vendor_id",
  "delete_rule": "@request.auth.id = @record.vendor_id || @request.auth.role = 'admin'"
}
```

**Result:**
- Vendors can only see their own products
- Vendors can create new products
- Vendors can only update/delete their own products
- Admins can delete any product

---

## API Usage

All API endpoints are available at `http://localhost:8000/api/v1`

### Collections API

#### List Collections
```bash
GET /api/v1/collections
```

#### Get Collection
```bash
GET /api/v1/collections/{collection_id}
```

#### Create Collection
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

#### Update Collection
```bash
PUT /api/v1/collections/{collection_id}
Authorization: Bearer ADMIN_TOKEN
```

#### Delete Collection
```bash
DELETE /api/v1/collections/{collection_id}
Authorization: Bearer ADMIN_TOKEN
```

### Records API

#### List Records
```bash
GET /api/v1/collections/{collection_name}/records
```

**Query Parameters:**
- `page` - Page number (default: 1)
- `per_page` - Records per page (default: 30, max: 100)
- `sort` - Sort field (prefix with `-` for descending)
- `filter` - Filter expression

**Example:**
```bash
GET /api/v1/collections/products/records?page=1&per_page=20&sort=-created
```

#### Get Record
```bash
GET /api/v1/collections/{collection_name}/records/{record_id}
```

#### Create Record
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

#### Update Record
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

#### Delete Record
```bash
DELETE /api/v1/collections/{collection_name}/records/{record_id}
Authorization: Bearer USER_TOKEN
```

### Authentication Headers

Include the access token in the Authorization header for protected endpoints:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Field Types

### Text Field
```json
{
  "name": "title",
  "type": "text",
  "validation": {
    "required": true,
    "min_length": 3,
    "max_length": 100
  }
}
```

### Number Field
```json
{
  "name": "price",
  "type": "number",
  "validation": {
    "required": true,
    "min": 0
  }
}
```

### Boolean Field
```json
{
  "name": "published",
  "type": "bool",
  "validation": {
    "required": false
  }
}
```

### Email Field
```json
{
  "name": "contact_email",
  "type": "email",
  "validation": {
    "required": true
  }
}
```

### URL Field
```json
{
  "name": "website",
  "type": "url",
  "validation": {
    "required": false
  }
}
```

### Date Field
```json
{
  "name": "publish_date",
  "type": "date",
  "validation": {
    "required": false
  }
}
```

### Select Field
```json
{
  "name": "status",
  "type": "select",
  "select": {
    "values": ["draft", "published", "archived"],
    "max_select": 1
  },
  "validation": {
    "required": true
  }
}
```

### Relation Field
```json
{
  "name": "category",
  "type": "relation",
  "relation": {
    "collection_id": "categories_collection_id",
    "type": "many-to-one",
    "cascade_delete": false,
    "display_fields": ["id", "name"]
  },
  "validation": {
    "required": false
  }
}
```

### File Field
```json
{
  "name": "image",
  "type": "file",
  "file": {
    "max_files": 1,
    "max_size": 5242880,
    "mime_types": ["image/jpeg", "image/png", "image/gif"],
    "thumbs": ["100x100", "500x500"]
  },
  "validation": {
    "required": false
  }
}
```

### JSON Field
```json
{
  "name": "metadata",
  "type": "json",
  "validation": {
    "required": false
  }
}
```

### Editor Field (Rich Text)
```json
{
  "name": "content",
  "type": "editor",
  "validation": {
    "required": false
  }
}
```

---

## Interactive API Documentation

FastCMS provides interactive API documentation powered by Swagger UI.

Access it at: `http://localhost:8000/docs`

This interface allows you to:
- Browse all available endpoints
- Test API calls directly from the browser
- View request/response schemas
- Authenticate and test protected endpoints

---

## Database

FastCMS uses SQLite with WAL (Write-Ahead Logging) mode for better concurrency.

**Database Location:** `data/app.db`

**Important Notes:**
- All collections are stored as dynamic tables
- The `collections` table stores metadata and schemas
- The `users` table is for admin authentication only
- Auth collections create their own tables with authentication fields

---

## Environment Variables

Create a `.env` file in the project root:

```env
# Application
ENV=development
DEBUG=true

# Database
DATABASE_URL=sqlite:///./data/app.db

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

---

## Best Practices

### Security

1. Always use strong SECRET_KEY in production
2. Use HTTPS in production
3. Set appropriate access control rules on collections
4. Validate user input on the client side
5. Use refresh tokens for long-lived sessions

### Performance

1. Add indexes to frequently queried fields
2. Use pagination for large datasets
3. Set appropriate cache TTL for view collections
4. Use view collections for complex queries instead of client-side joins

### Data Modeling

1. Use auth collections for any user type requiring authentication
2. Use base collections for standard data
3. Use view collections for reports and aggregations
4. Use relation fields to link collections
5. Set cascade_delete appropriately on relations

---

## Troubleshooting

### Collection Creation Fails

**Issue:** "An invalid form control with name='' is not focusable"

**Solution:** This occurs when hidden required fields (relation/view fields) are present. Ensure you're creating the correct collection type and all visible required fields are filled.

### Authentication Fails

**Issue:** 401 Unauthorized

**Solution:**
- Ensure access token is included in Authorization header
- Check if token has expired (access tokens expire in 15 minutes by default)
- Use refresh token to get a new access token

### Access Denied to Records

**Issue:** Cannot view/edit records despite being authenticated

**Solution:**
- Check the access control rules on the collection
- Ensure your user meets the rule criteria
- Verify the record data matches the rules (e.g., user_id field)

---

## Support

For issues and questions:
- GitHub: https://github.com/yourusername/fastCMS
- Issues: https://github.com/yourusername/fastCMS/issues

---

## License

MIT License - see LICENSE file for details
