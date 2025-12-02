# Access Control Rules

Every collection has five access control rules that determine who can perform which operations.

## Rule Types

1. **list_rule** - Who can list/search records
2. **view_rule** - Who can view a single record
3. **create_rule** - Who can create new records
4. **update_rule** - Who can update records
5. **delete_rule** - Who can delete records

## Rule Syntax

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

## Common Rule Patterns

### Public Access
```
list_rule: null
```
Everyone can access (no authentication required).

### Authenticated Users Only
```
list_rule: "@request.auth.id != ''"
```
Only logged-in users can list records.

### Admin Only
```
list_rule: "@request.auth.role = 'admin'"
create_rule: "@request.auth.role = 'admin'"
delete_rule: "@request.auth.role = 'admin'"
```
Only admin users can access.

### Owner Only
```
list_rule: "@request.auth.id = @record.user_id"
update_rule: "@request.auth.id = @record.user_id"
```
Users can only see/edit records they own.

### Owner OR Admin
```
update_rule: "@request.auth.id = @record.user_id || @request.auth.role = 'admin'"
delete_rule: "@request.auth.id = @record.user_id || @request.auth.role = 'admin'"
```
Record owner OR admin can update/delete.

## Real-World Example: Vendor System

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

## Best Practices

1. **Start Restrictive**: Begin with strict rules and loosen as needed
2. **Test Thoroughly**: Verify rules work as expected with different user roles
3. **Document Rules**: Add comments explaining complex access control logic
4. **Use Owner Patterns**: Most apps need "owner can edit" rules
5. **Admin Override**: Allow admins to override most restrictions
