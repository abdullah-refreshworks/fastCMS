# CSV Import/Export

FastCMS allows you to easily import and export data from collections in CSV (Comma-Separated Values) format. This is useful for data migration, backups, bulk editing, and integration with spreadsheet applications like Excel or Google Sheets.

## What is CSV Import/Export?

**CSV Export** downloads all records from a collection into a CSV file that can be opened in Excel, Google Sheets, or any text editor.

**CSV Import** uploads a CSV file to create multiple records in a collection at once. This is much faster than creating records one by one.

## Via Admin Dashboard

### Exporting Records to CSV

1. Navigate to any collection's records page (e.g., `http://localhost:8000/admin/collections/products/records`)
2. Click the **"Export CSV"** button at the top of the page
3. Your browser will download a CSV file named `{collection_name}_export.csv`
4. Open the file in Excel, Google Sheets, or any text editor

The exported CSV will include:
- System fields: `id`, `created`, `updated`
- All custom fields defined in the collection schema
- Proper formatting for dates, numbers, and boolean values

### Importing Records from CSV

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

## Via API

### Export Records to CSV

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

### Import Records from CSV

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

## CSV Format Examples

### Simple Example: Products

**CSV File (products.csv):**
```csv
name,price,active
Laptop,999.99,true
Mouse,29.99,true
Keyboard,79.99,false
Monitor,299.99,true
```

**Import Result:** 4 records created

### Example with Different Field Types

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

## Export-Import Workflow (Data Migration)

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

## Handling Large Datasets

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

## Troubleshooting

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

## Access Control

CSV import/export respects collection access control rules:

- **Export**: Requires list permission on the collection
- **Import**: Requires create permission on the collection

If you get a 403 error:
- Check the collection's `list_rule` for export
- Check the collection's `create_rule` for import
- Verify your access token has the necessary permissions
