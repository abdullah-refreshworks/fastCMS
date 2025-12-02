# Bulk Operations

FastCMS provides bulk operations to efficiently update or delete multiple records at once. Instead of making individual API calls for each record, you can process up to 100 records in a single request.

## Features

- **Bulk Delete**: Delete multiple records in one operation
- **Bulk Update**: Update the same field(s) across multiple records
- **Partial Success Handling**: Operations continue even if some records fail
- **Detailed Error Reporting**: Get specific error messages for failed operations
- **Access Control**: Respects collection permissions for each record

## Via Admin UI

### Selecting Records

1. Navigate to any collection's records page
2. Use checkboxes to select records:
   - **Select individual records**: Click the checkbox next to each record
   - **Select all records**: Click the checkbox in the table header
3. Selected count is displayed in the header

### Bulk Delete

1. Select the records you want to delete
2. Click the **Delete Selected** button
3. Confirm the deletion in the dialog
4. See the operation summary (successful and failed counts)

### Bulk Update

1. Select the records you want to update
2. Click the **Update Selected** button
3. In the modal:
   - Choose which field to update from the dropdown
   - Enter the new value for that field
   - Click **Update Records**
4. See the operation summary (successful and failed counts)

## Via API

### Bulk Delete Records

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

### Bulk Update Records

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

## Limitations

- **Maximum 100 records per request** - If you need to process more, split into multiple requests
- **At least 1 record required** - You must provide at least one record ID
- **Authentication required** - Bulk operations require a valid access token
- **Sequential processing** - Records are processed one by one, not in parallel

## Error Handling

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

## Best Practices

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

## Access Control

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

## Performance Considerations

- **API overhead**: One request instead of N requests saves significant overhead
- **Database operations**: Still performs N individual database operations
- **Best for**: 10-100 records at a time
- **Not ideal for**: Thousands of records (consider background jobs instead)

**Estimated Performance:**
- 10 records: ~100-200ms
- 50 records: ~500ms-1s
- 100 records: ~1-2s
