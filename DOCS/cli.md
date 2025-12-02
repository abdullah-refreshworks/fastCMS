# FastCMS Command Line Interface (CLI)

FastCMS includes a powerful command-line interface that allows you to manage your CMS directly from the terminal. This is perfect for automation, DevOps workflows, and quick administration tasks.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [User Management](#user-management)
- [Collection Management](#collection-management)
- [System Information](#system-information)
- [Examples & Use Cases](#examples--use-cases)
- [Troubleshooting](#troubleshooting)

---

## Installation

The CLI is included with FastCMS. No additional installation is required.

### Prerequisites

- Python 3.8 or higher
- FastCMS installed with all dependencies

### Verify Installation

```bash
# Make the fastcms script executable (first time only)
chmod +x fastcms

# Run the CLI
./fastcms --help

# Or use Python directly
python fastcms_cli.py --help
```

**Output:**
```
Usage: fastcms [OPTIONS] COMMAND [ARGS]...

  FastCMS Command Line Interface

  Manage users, collections, and settings from the terminal.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  create-admin        Create a new admin user.
  create-collection   Create a new collection.
  create-user         Create a new user.
  delete-collection   Delete a collection by name.
  info                Display FastCMS system information.
  list-collections    List all collections.
  list-users          List all users.
```

---

## Quick Start

### 1. Create Your First Admin User

```bash
fastcms create-admin
```

You'll be prompted for:
- Email address
- Password (hidden input with confirmation)
- Name

**Example:**
```bash
$ fastcms create-admin
Email: admin@fastcms.dev
Password:
Repeat for confirmation:
Name: FastCMS Admin

✅ Admin user created successfully!
   Email: admin@fastcms.dev
   Name: FastCMS Admin
   Role: admin
   ID: 9ded1234-bed5-48a4-b0ce-310578dfab8f
```

### 2. Create Your First Collection

```bash
fastcms create-collection \
  --name products \
  --type base \
  --field title:text \
  --field price:number \
  --field active:bool
```

**Output:**
```
✅ Collection 'products' created successfully!
   Type: base
   ID: abc123...
   Fields: 3 custom field(s)
     • title (text)
     • price (number)
     • active (bool)

💡 Tip: Access your collection at /admin/collections/products/records
```

### 3. Check System Information

```bash
fastcms info
```

**Output:**
```
⚡ FastCMS System Information

  ✓ Database: Connected
  • Users: 1
  • Collections: 1

  • Data directory: /path/to/fastCMS/data
  • Database size: 0.15 MB
  • Backups: 0

  💡 Run 'fastcms --help' to see all available commands
```

---

## User Management

### Create Admin User

Create an administrative user with full access to the FastCMS dashboard.

**Command:**
```bash
fastcms create-admin
```

**Interactive Prompts:**
```
Email: admin@example.com
Password: [hidden]
Repeat for confirmation: [hidden]
Name: John Administrator
```

**Options:**
- `--email TEXT`: Admin email address (prompted if not provided)
- `--password TEXT`: Admin password (prompted if not provided)
- `--name TEXT`: Admin name (prompted if not provided)

**Non-Interactive Mode:**
```bash
fastcms create-admin \
  --email admin@example.com \
  --name "John Administrator"
# Password will still be prompted for security
```

**Example Output:**
```
✅ Admin user created successfully!
   Email: admin@example.com
   Name: John Administrator
   Role: admin
   ID: uuid-here
```

---

### Create Regular User

Create a regular user account (non-admin).

**Command:**
```bash
fastcms create-user
```

**Options:**
- `--email TEXT`: User email address
- `--password TEXT`: User password
- `--name TEXT`: User name
- `--role [admin|user]`: User role (default: user)

**Example - Create Regular User:**
```bash
fastcms create-user \
  --email user@example.com \
  --name "Regular User" \
  --role user
```

**Example - Create Admin via create-user:**
```bash
fastcms create-user \
  --email admin2@example.com \
  --name "Second Admin" \
  --role admin
```

**Output:**
```
✅ User created successfully!
   Email: user@example.com
   Name: Regular User
   Role: user
   Verified: false
   ID: uuid-here
```

---

### List All Users

Display all users in the system.

**Command:**
```bash
fastcms list-users
```

**Example Output:**
```
📋 Found 3 user(s):

  • admin@fastcms.dev
    Name: FastCMS Admin
    Role: ADMIN
    Verified: ✓
    ID: uuid-1
    Created: 2025-01-15 10:30:00

  • user@example.com
    Name: Regular User
    Role: USER
    Verified: ✗
    ID: uuid-2
    Created: 2025-01-15 11:00:00

  • developer@example.com
    Name: Dev User
    Role: ADMIN
    Verified: ✓
    ID: uuid-3
    Created: 2025-01-15 11:30:00
```

**Features:**
- Color-coded roles (admins in green, users in blue)
- Verification status indicators (✓/✗)
- Sorted by creation date (newest first)

---

## Collection Management

### Create Collection

Create a new collection with custom fields.

**Command:**
```bash
fastcms create-collection [OPTIONS]
```

**Options:**
- `--name TEXT`: Collection name (lowercase, letters, numbers, underscores)
- `--type [base|auth|view]`: Collection type (default: base)
- `--field TEXT`: Field definition (can be used multiple times)

**Field Format:**
```
--field field_name:field_type
```

**Available Field Types:**
- `text` - Text field
- `number` - Numeric field
- `bool` - Boolean field
- `email` - Email validation
- `url` - URL validation
- `date` - Date/time field
- `select` - Select dropdown
- `relation` - Relation to another collection
- `file` - File upload
- `json` - JSON data
- `editor` - Rich text editor

---

### Example: Create Blog Posts Collection

```bash
fastcms create-collection \
  --name blog_posts \
  --type base \
  --field title:text \
  --field content:editor \
  --field published:bool \
  --field publish_date:date \
  --field author_email:email
```

**Output:**
```
✅ Collection 'blog_posts' created successfully!
   Type: base
   ID: collection-uuid
   Fields: 5 custom field(s)
     • title (text)
     • content (editor)
     • published (bool)
     • publish_date (date)
     • author_email (email)

💡 Tip: Access your collection at /admin/collections/blog_posts/records
```

---

### Example: Create Auth Collection

Auth collections automatically include authentication fields.

```bash
fastcms create-collection \
  --name customers \
  --type auth \
  --field company:text \
  --field phone:text
```

**Output:**
```
ℹ️  Auth collection will automatically include: email, password, verified, role, token_key
✅ Collection 'customers' created successfully!
   Type: auth
   ID: collection-uuid
   Fields: 2 custom field(s)
     • company (text)
     • phone (text)

💡 Tip: Access your collection at /admin/collections/customers/records
```

**Note:** Auth collections automatically get:
- `email` (unique, indexed)
- `password` (hashed)
- `verified` (boolean)
- `role` (string)
- `token_key` (string)

---

### Example: Simple Collection

Create a minimal collection without custom fields:

```bash
fastcms create-collection --name notes --type base
```

The collection will be created with only the default system fields (`id`, `created`, `updated`). You can add custom fields later via the admin UI.

---

### List All Collections

Display all collections in the system.

**Command:**
```bash
fastcms list-collections
```

**Example Output:**
```
📚 Found 3 collection(s):

  • products
    Type: BASE
    ID: uuid-1
    Fields: 3
      title, price, active
    Created: 2025-01-15 10:00:00

  • customers
    Type: AUTH
    ID: uuid-2
    Fields: 2
      company, phone
    Created: 2025-01-15 11:00:00

  • sales_report
    Type: VIEW
    ID: uuid-3
    Fields: 0
    Created: 2025-01-15 12:00:00
```

**Features:**
- Color-coded types (base=blue, auth=green, view=magenta)
- Field count and preview (first 3 fields)
- Sorted by creation date

---

### Delete Collection

Delete a collection by name.

**Command:**
```bash
fastcms delete-collection COLLECTION_NAME
```

**Example:**
```bash
fastcms delete-collection old_products
```

**Output:**
```
⚠️  Are you sure you want to delete collection 'old_products'? This cannot be undone! [y/N]: y
✅ Collection 'old_products' deleted successfully!
```

**Warning:** This action is irreversible and will delete:
- The collection metadata
- All records in the collection
- The database table

---

## System Information

### Display System Info

Get an overview of your FastCMS instance.

**Command:**
```bash
fastcms info
```

**Example Output:**
```
⚡ FastCMS System Information

  ✓ Database: Connected
  • Users: 5
  • Collections: 12

  • Data directory: /home/user/fastcms/data
  • Database size: 2.45 MB
  • Backups: 3

  💡 Run 'fastcms --help' to see all available commands
```

**Information Displayed:**
- Database connection status
- Total user count
- Total collection count
- Data directory location
- Database file size
- Number of backups

---

## Examples & Use Cases

### 1. Initial Setup Script

Set up a new FastCMS instance with admin user and collections:

```bash
#!/bin/bash
# setup.sh - Initial FastCMS setup

echo "Setting up FastCMS..."

# Create admin user
fastcms create-admin \
  --name "System Administrator"

# Create collections
fastcms create-collection \
  --name products \
  --type base \
  --field name:text \
  --field price:number \
  --field stock:number \
  --field active:bool

fastcms create-collection \
  --name customers \
  --type auth \
  --field company:text \
  --field phone:text \
  --field address:text

fastcms create-collection \
  --name orders \
  --type base \
  --field customer_id:text \
  --field total:number \
  --field status:text

echo "✅ Setup complete!"
fastcms info
```

---

### 2. Multi-Environment Setup

Create different setups for dev, staging, and production:

**dev-setup.sh:**
```bash
#!/bin/bash
fastcms create-admin --name "Dev Admin"

fastcms create-collection --name test_data --type base
fastcms create-collection --name test_users --type auth
```

**production-setup.sh:**
```bash
#!/bin/bash
fastcms create-admin --name "Production Admin"

fastcms create-collection \
  --name products \
  --type base \
  --field name:text \
  --field price:number

fastcms create-collection \
  --name customers \
  --type auth \
  --field company:text
```

---

### 3. User Management Automation

Create multiple users from a script:

```bash
#!/bin/bash
# create-team.sh

USERS=(
  "manager@company.com:John Manager:admin"
  "dev@company.com:Jane Developer:user"
  "support@company.com:Bob Support:user"
)

for user_data in "${USERS[@]}"; do
  IFS=':' read -r email name role <<< "$user_data"

  echo "Creating user: $email ($role)"
  fastcms create-user \
    --email "$email" \
    --name "$name" \
    --role "$role"
done

echo "✅ Team created!"
fastcms list-users
```

---

### 4. Collection Batch Creation

Create multiple collections at once:

```bash
#!/bin/bash
# create-blog-collections.sh

# Blog posts
fastcms create-collection \
  --name posts \
  --type base \
  --field title:text \
  --field content:editor \
  --field published:bool \
  --field publish_date:date

# Authors (auth collection)
fastcms create-collection \
  --name authors \
  --type auth \
  --field bio:editor \
  --field website:url

# Comments
fastcms create-collection \
  --name comments \
  --type base \
  --field post_id:text \
  --field content:text \
  --field author_name:text \
  --field author_email:email

# Categories
fastcms create-collection \
  --name categories \
  --type base \
  --field name:text \
  --field description:text

echo "✅ Blog collections created!"
fastcms list-collections
```

---

### 5. Database Health Check

Regularly check your database status:

```bash
#!/bin/bash
# health-check.sh

echo "🔍 FastCMS Health Check"
echo "======================="

fastcms info

echo ""
echo "Recent users:"
fastcms list-users | head -n 20

echo ""
echo "Collections:"
fastcms list-collections | head -n 20
```

---

### 6. CI/CD Integration

Integrate with GitHub Actions:

**.github/workflows/setup.yml:**
```yaml
name: Setup FastCMS

on:
  push:
    branches: [main]

jobs:
  setup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run migrations
        run: alembic upgrade head

      - name: Create admin user
        run: |
          fastcms create-admin \
            --email ${{ secrets.ADMIN_EMAIL }} \
            --name "CI Admin"

      - name: Setup collections
        run: |
          fastcms create-collection --name products --type base
          fastcms create-collection --name users --type auth

      - name: Verify setup
        run: fastcms info
```

---

### 7. Docker Entrypoint

Use CLI in Docker container initialization:

**docker-entrypoint.sh:**
```bash
#!/bin/bash
set -e

# Run migrations
alembic upgrade head

# Create admin if doesn't exist
if [ -n "$ADMIN_EMAIL" ] && [ -n "$ADMIN_PASSWORD" ]; then
  echo "Creating admin user..."
  fastcms create-admin \
    --email "$ADMIN_EMAIL" \
    --name "${ADMIN_NAME:-Admin}"
fi

# Start application
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## Troubleshooting

### Command Not Found

**Problem:**
```bash
$ fastcms --help
bash: fastcms: command not found
```

**Solution:**
```bash
# Use the full path
python /path/to/fastcms/cli.py --help

# Or add to PATH
export PATH="$PATH:/path/to/fastcms"
./fastcms --help

# Or use python directly
fastcms --help
```

---

### Database Connection Error

**Problem:**
```
❌ Error: could not connect to database
```

**Solutions:**

1. **Check database exists:**
```bash
ls -la data/app.db
```

2. **Run migrations:**
```bash
alembic upgrade head
```

3. **Check DATABASE_URL in .env:**
```bash
cat .env | grep DATABASE_URL
```

4. **Verify database permissions:**
```bash
chmod 644 data/app.db
```

---

### User Already Exists

**Problem:**
```
❌ User with email 'admin@example.com' already exists!
```

**Solutions:**

1. **Use a different email:**
```bash
fastcms create-admin --email admin2@example.com
```

2. **List existing users:**
```bash
fastcms list-users
```

3. **Delete the user via admin UI first**, then recreate

---

### Collection Already Exists

**Problem:**
```
❌ Collection 'products' already exists!
```

**Solutions:**

1. **Use a different name:**
```bash
fastcms create-collection --name products_v2 --type base
```

2. **List existing collections:**
```bash
fastcms list-collections
```

3. **Delete the collection first:**
```bash
fastcms delete-collection products
```

---

### Invalid Field Type

**Problem:**
```
❌ Invalid field type: string. Must be one of: text, number, bool, ...
```

**Solution:**

Use the correct field type name:
- ❌ `string` → ✅ `text`
- ❌ `int` → ✅ `number`
- ❌ `boolean` → ✅ `bool`
- ❌ `datetime` → ✅ `date`

**Correct command:**
```bash
fastcms create-collection \
  --name products \
  --field name:text \
  --field price:number \
  --field active:bool
```

---

### Permission Denied

**Problem:**
```bash
$ ./fastcms --help
-bash: ./fastcms: Permission denied
```

**Solution:**
```bash
# Make script executable
chmod +x fastcms cli.py

# Or use python directly
fastcms --help
```

---

## Advanced Tips

### 1. Use Aliases

Add to your `.bashrc` or `.zshrc`:

```bash
alias fcms='python /path/to/fastcms/cli.py'
```

Then use:
```bash
fcms create-admin
fcms list-users
fcms info
```

---

### 2. Non-Interactive Scripts

For automation, you can pass values via environment variables or files:

```bash
# Using environment variables
export ADMIN_EMAIL="admin@example.com"
export ADMIN_PASSWORD="secure_password"
export ADMIN_NAME="Admin"

# Then use echo to pipe input
echo -e "$ADMIN_EMAIL\n$ADMIN_PASSWORD\n$ADMIN_PASSWORD\n$ADMIN_NAME" | fastcms create-admin
```

---

### 3. JSON Output (Future)

For scripting, you might want to parse output. Currently outputs are human-readable. For JSON output, use the REST API directly:

```bash
# Get collections as JSON
curl http://localhost:8000/api/v1/collections

# Get users as JSON (requires auth token)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/auth/users
```

---

### 4. Logging

Enable detailed logging:

```bash
# Add to .env
LOG_LEVEL=DEBUG

# Run CLI with verbose output
fastcms create-admin 2>&1 | tee setup.log
```

---

## Next Steps

- **Learn More**: Check out [DOCS/README.md](./README.md) for complete documentation
- **API Reference**: See [DOCS/api-reference.md](./api-reference.md) for REST API
- **Web UI**: Access the admin dashboard at `http://localhost:8000/admin`
- **Automation**: Use the CLI in your deployment scripts and CI/CD pipelines

---

## Feedback & Contributions

Found a bug or have a feature request for the CLI?
- GitHub Issues: https://github.com/yourusername/fastCMS/issues
- Pull Requests Welcome!

---

**Happy Automating! ⚡**
