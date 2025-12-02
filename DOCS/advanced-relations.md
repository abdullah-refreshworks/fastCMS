# Advanced Relations

FastCMS supports advanced relationship types beyond basic one-to-many references. The relation schema includes support for many-to-many, polymorphic, one-to-one, and nested relations with configurable cascade actions.

## Overview

**Current Status:**
- ✅ Schema supports all advanced relation types
- ✅ API accepts and validates advanced relation configurations
- ⏳ Runtime behavior (junction tables, recursive loading, cascades) is not yet implemented
- ⏳ Frontend UI for configuring advanced relations is pending

**Available Relation Types:**
- `one-to-many` - One record can have many related records (default)
- `many-to-one` - Many records reference one parent record
- `many-to-many` - Records can have multiple related records in both directions
- `one-to-one` - One record relates to exactly one other record
- `polymorphic` - Relate to records from multiple different collections

**Cascade Actions:**
- `restrict` - Prevent deletion if related records exist (default)
- `cascade` - Delete related records automatically
- `set_null` - Set foreign key to NULL when parent is deleted
- `no_action` - Do nothing (standard SQL behavior)

## Relation Schema

When defining a relation field, use the `RelationOptions` configuration:

```json
{
  "name": "author",
  "type": "relation",
  "relation": {
    "collection_id": "users",
    "type": "many-to-one",
    "cascade_delete": "restrict",
    "display_fields": ["name", "email"],
    "max_depth": 2
  }
}
```

**RelationOptions Fields:**

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `collection_id` | string | Target collection ID (for single collection) | Required |
| `collection_ids` | array | Target collection IDs (for polymorphic) | null |
| `type` | string | Relationship type | `one-to-many` |
| `cascade_delete` | string | Action on parent deletion | `restrict` |
| `display_fields` | array | Fields to show in relation | `["id"]` |
| `max_depth` | integer | Nested loading depth (0-5) | 1 |
| `junction_table` | string | Junction table for many-to-many | null |
| `junction_field` | string | Field in junction referencing this collection | null |
| `target_field` | string | Field in junction referencing target | null |
| `polymorphic_type_field` | string | Field storing collection type | null |

## One-to-Many Relations

Default relation type. One parent record can have multiple child records.

**Example:** Posts collection with multiple comments

```bash
curl -X POST "http://localhost:8000/api/v1/collections" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "comments",
    "type": "base",
    "schema": {
      "fields": [
        {
          "name": "content",
          "type": "text"
        },
        {
          "name": "post",
          "type": "relation",
          "relation": {
            "collection_id": "posts",
            "type": "one-to-many",
            "cascade_delete": "cascade",
            "display_fields": ["title"]
          }
        }
      ]
    }
  }'
```

## Many-to-One Relations

Multiple records reference a single parent record. Opposite perspective of one-to-many.

**Example:** Multiple posts by one author

```json
{
  "name": "author",
  "type": "relation",
  "relation": {
    "collection_id": "users",
    "type": "many-to-one",
    "cascade_delete": "set_null",
    "display_fields": ["name", "email"]
  }
}
```

## Many-to-Many Relations

Records can relate to multiple records in both directions. Requires a junction table.

**Example:** Posts with multiple tags, tags with multiple posts

```json
{
  "name": "tags",
  "type": "relation",
  "relation": {
    "collection_id": "tags",
    "type": "many-to-many",
    "junction_table": "posts_tags",
    "junction_field": "post_id",
    "target_field": "tag_id",
    "display_fields": ["name"]
  }
}
```

**Note:** Runtime support for automatic junction table creation is pending.

## One-to-One Relations

Each record relates to exactly one record in the target collection.

**Example:** User profile

```json
{
  "name": "profile",
  "type": "relation",
  "relation": {
    "collection_id": "user_profiles",
    "type": "one-to-one",
    "cascade_delete": "cascade",
    "display_fields": ["bio", "avatar"]
  }
}
```

## Polymorphic Relations

Relate to records from multiple different collections. Useful for comments, attachments, etc.

**Example:** Comments that can belong to posts OR events

```json
{
  "name": "commentable",
  "type": "relation",
  "relation": {
    "collection_ids": ["posts", "events"],
    "type": "polymorphic",
    "polymorphic_type_field": "commentable_type",
    "display_fields": ["title"]
  }
}
```

**Storage Pattern:**
- `commentable` field stores the record ID
- `commentable_type` field stores the collection name ("posts" or "events")

**Note:** Runtime support for polymorphic queries is pending.

## Cascade Actions

Control what happens to related records when a parent is deleted.

### CASCADE - Delete Related Records

```json
{
  "cascade_delete": "cascade"
}
```

**Behavior:** When a user is deleted, all their posts are automatically deleted.

### SET_NULL - Clear Foreign Key

```json
{
  "cascade_delete": "set_null"
}
```

**Behavior:** When a user is deleted, posts' `author` field is set to NULL.

### RESTRICT - Prevent Deletion

```json
{
  "cascade_delete": "restrict"
}
```

**Behavior:** Cannot delete user if they have posts. Returns error.

### NO_ACTION - Do Nothing

```json
{
  "cascade_delete": "no_action"
}
```

**Behavior:** Standard SQL behavior, may leave orphaned records.

**Note:** Runtime cascade enforcement is pending.

## Current Limitations

**What Works:**
- ✅ Schema validation for all relation types
- ✅ API accepts advanced relation configurations
- ✅ Basic one-to-many expansion (existing functionality)

**What's Pending:**
- ⏳ Automatic junction table creation for many-to-many
- ⏳ Polymorphic relation querying
- ⏳ Recursive loading beyond depth 1
- ⏳ Cascade action enforcement
- ⏳ Frontend UI for relation configuration

## Best Practices

**1. Choose the Right Relation Type**

Use `many-to-one` for most cases:
```json
// Posts -> Author (many posts, one author each)
{"type": "many-to-one", "collection_id": "users"}
```

Use `many-to-many` for bidirectional multi-relations:
```json
// Posts <-> Tags
{"type": "many-to-many", "junction_table": "posts_tags"}
```

**2. Set Appropriate Cascade Actions**

For dependent data:
```json
// Comments should be deleted with their post
{"cascade_delete": "cascade"}
```

For independent data:
```json
// Posts shouldn't be deleted when author is deleted
{"cascade_delete": "set_null"}
```

For strict referential integrity:
```json
// Can't delete if dependencies exist
{"cascade_delete": "restrict"}
```

**3. Limit Expansion Depth**

```json
// Good: Limited depth for performance
{"max_depth": 2}

// Risky: Deep nesting can cause slow queries
{"max_depth": 5}
```

**4. Choose Display Fields Wisely**

```json
// Good: Useful identifying fields
{"display_fields": ["name", "email"]}

// Bad: Too many fields
{"display_fields": ["id", "name", "email", "bio", "created", "updated"]}
```
