# FastCMS CLI Quick Reference

## Setup

```bash
# Make CLI executable (first time only)
chmod +x fastcms
```

## User Management

```bash
# Create admin user (interactive prompts)
./fastcms create-admin

# Create regular user (interactive prompts)
./fastcms create-user

# List all users
./fastcms list-users
```

## Collection Management

```bash
# Create a collection with fields
./fastcms create-collection --name COLLECTION_NAME --type base \
  --field name:text \
  --field description:text \
  --field price:number \
  --field active:bool

# List all collections
./fastcms list-collections

# Delete a collection
./fastcms delete-collection COLLECTION_NAME
```

## System Information

```bash
# Display system info (database, users, collections count, backups)
./fastcms info
```

## Field Types

Supported field types for `--field name:type`:
- `text` - Text field
- `number` - Numeric field
- `bool` - Boolean field
- `email` - Email validation
- `url` - URL validation
- `date` - Date field
- `select` - Select dropdown
- `relation` - Relation to another collection
- `file` - File upload
- `json` - JSON data
- `editor` - Rich text editor

## Collection Types

- `base` - Standard collection for storing data
- `auth` - Authentication collection (automatically includes email, password, verified fields)
- `view` - View-only collection (no data storage)

## Examples

### Quick Setup Script
```bash
#!/bin/bash
# Initial setup for new FastCMS instance

# Create admin user
./fastcms create-admin

# Create products collection
./fastcms create-collection --name products --type base \
  --field title:text \
  --field description:text \
  --field price:number \
  --field stock:number \
  --field active:bool

# Create categories collection
./fastcms create-collection --name categories --type base \
  --field name:text \
  --field description:text

# Show info
./fastcms info
```

### Check System Status
```bash
./fastcms info
./fastcms list-users
./fastcms list-collections
```

## Help

```bash
# Show all available commands
./fastcms --help

# Show help for specific command
./fastcms create-collection --help
```

## Full Documentation

See [DOCS/cli.md](DOCS/cli.md) for complete CLI documentation including troubleshooting, automation, and advanced usage.
