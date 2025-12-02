# Field Types

## Text Field
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

## Number Field
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

## Boolean Field
```json
{
  "name": "published",
  "type": "bool",
  "validation": {
    "required": false
  }
}
```

## Email Field
```json
{
  "name": "contact_email",
  "type": "email",
  "validation": {
    "required": true
  }
}
```

## URL Field
```json
{
  "name": "website",
  "type": "url",
  "validation": {
    "required": false
  }
}
```

## Date Field
```json
{
  "name": "publish_date",
  "type": "date",
  "validation": {
    "required": false
  }
}
```

## Select Field
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

## Relation Field
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

## File Field
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

## JSON Field
```json
{
  "name": "metadata",
  "type": "json",
  "validation": {
    "required": false
  }
}
```

## Editor Field (Rich Text)
```json
{
  "name": "content",
  "type": "editor",
  "validation": {
    "required": false
  }
}
```
