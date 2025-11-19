# Relation Fields Guide

## How to Create Relations in the Admin UI

Now you can create relation fields directly from the admin panel without hardcoding anything!

### Steps:

1. **Go to Collections**
   - Visit: `http://localhost:8000/admin/collections`
   - Click "Create Collection"

2. **Add a Relation Field**
   - Click "Add Field"
   - Enter field name (e.g., `author`, `category`, `post`)
   - Select Type: **"Relation"**

3. **Configure the Relation** (new panel appears automatically!)
   - **Target Collection**: Select from dropdown (e.g., `authors`, `categories`)
   - **Relationship Type**: Choose one:
     - **One to Many**: One parent can have many children (e.g., one author has many posts)
     - **Many to One**: Many children belong to one parent (e.g., many posts have one author)
     - **Many to Many**: Both sides can have multiple (e.g., posts and tags)
     - **One to One**: Unique relationship (e.g., user and profile)
   - **Display Fields**: Comma-separated fields to show (e.g., `id, name, email`)
   - **Cascade Delete**: Check if you want related records deleted when parent is deleted

4. **Save the Collection**

### Example: Creating a Blog with Relations

#### Step 1: Create "authors" collection
```
Fields:
- name (text, required)
- email (email, required, unique)
- bio (editor)
```

#### Step 2: Create "posts" collection with author relation
```
Fields:
- title (text, required)
- content (editor)
- author (relation):
  └─ Target Collection: authors
  └─ Relationship Type: Many to One
  └─ Display Fields: name, email
  └─ Cascade Delete: ☐ (unchecked)
- published (bool)
```

#### Step 3: Create "comments" collection with multiple relations
```
Fields:
- post (relation):
  └─ Target Collection: posts
  └─ Relationship Type: Many to One
  └─ Display Fields: title
  └─ Cascade Delete: ☑ (checked - delete comments when post deleted)

- author (relation):
  └─ Target Collection: authors
  └─ Relationship Type: Many to One
  └─ Display Fields: name
  └─ Cascade Delete: ☐ (unchecked)

- content (text, required)
- approved (bool)
```

## Relationship Types Explained

### One to Many
**Use when**: One parent has many children
**Example**: One author → many posts
```
authors (parent)
  ├── post 1
  ├── post 2
  └── post 3
```

### Many to One
**Use when**: Many children belong to one parent
**Example**: Many posts → one author
```
posts (children)
  ├── post 1 → author A
  ├── post 2 → author A
  └── post 3 → author B
```

### Many to Many
**Use when**: Both sides can have multiple
**Example**: Posts ↔ Tags
```
post 1 ← → tag A, tag B
post 2 ← → tag B, tag C
post 3 ← → tag A, tag C
```
*Note: Many-to-many requires a junction table*

### One to One
**Use when**: Unique 1:1 relationship
**Example**: One user → one profile
```
user 1 → profile 1
user 2 → profile 2
user 3 → profile 3
```

## Cascade Delete

**Checked (enabled)**: When you delete the parent, all related records are also deleted
- Example: Delete a post → all its comments are deleted

**Unchecked (disabled)**: Related records remain when parent is deleted
- Example: Delete a post → author remains

## Display Fields

These fields are shown when displaying the relation in the UI.

**Examples:**
- `id` - Just show the ID (default)
- `name` - Show the name
- `name, email` - Show both name and email
- `title, author` - Show title and author

## Creating Records with Relations

When you create a record with a relation field, you just provide the ID of the related record:

```json
{
  "title": "My Post",
  "content": "...",
  "author": "author-id-here",
  "category": "category-id-here"
}
```

The system automatically validates that the related records exist!

## Benefits of the New UI

✅ **Visual Configuration**: No need to remember collection IDs
✅ **Relationship Types**: Clear selection of how data relates
✅ **Display Control**: Choose which fields to show
✅ **Cascade Delete**: Easy control of deletion behavior
✅ **Type Safety**: Automatic validation of relations
✅ **No Code**: Everything is configurable from the admin panel

## Try It Now!

Visit: `http://localhost:8000/admin/collections/new`

Create a collection, add a relation field, and see the configuration panel appear automatically!
