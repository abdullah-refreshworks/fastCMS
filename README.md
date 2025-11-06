# FastCMS

Self-hosted Backend-as-a-Service built with FastAPI. Create dynamic collections, REST APIs, and authentication without writing SQL.

## Features Status

### Core Features
- [x] Dynamic Collections - Create database tables via API
- [x] Authentication - JWT-based auth with register/login
- [x] CRUD API - Create, read, update, delete records
- [x] File Storage - Upload and serve files
- [x] Real-time Updates - Server-Sent Events
- [x] Access Control - Permission rules per collection with role-based access
- [x] Admin Dashboard - Complete web UI for management

### AI Features (Planned)
- [ ] Natural Language API Interface
- [ ] Semantic Search - Vector-based search
- [ ] Content Moderation
- [ ] Data Quality Monitoring
- [ ] Auto-Documentation
- [ ] Smart Test Data Generation

## Installation

```bash
# Clone the repository
git clone https://github.com/aalhommada/fastCMS.git
cd fastCMS

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env and set SECRET_KEY (generate: openssl rand -hex 32)

# Run database migrations
alembic upgrade head

# Start the server
python app/main.py
```

### Access
- API Documentation: http://localhost:8000/docs
- Admin Dashboard: http://localhost:8000/admin/ (requires admin role)
- Health Check: http://localhost:8000/health

## Tech Stack

- FastAPI - Async web framework
- SQLAlchemy 2.0 - Async ORM
- SQLite - Database with WAL mode
- Pydantic v2 - Data validation
- Alembic - Database migrations
- JWT - Token-based authentication
- LangChain/LangGraph - AI framework (planned)

## Project Structure

```
fastCMS/
├── app/
│   ├── api/v1/          # API endpoints
│   ├── core/            # Configuration, security
│   ├── db/              # Database models
│   ├── schemas/         # Pydantic models
│   ├── services/        # Business logic
│   └── main.py          # App entry
├── migrations/          # Alembic migrations
├── tests/               # Tests
└── data/                # Database & files
```

## API Examples

### Register
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass123!", "password_confirm": "SecurePass123!", "name": "John Doe"}'
```

### Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass123!"}'
```

### Create Collection
```bash
curl -X POST "http://localhost:8000/api/v1/collections" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "posts",
    "type": "base",
    "schema": [
      {"name": "title", "type": "text", "validation": {"required": true}},
      {"name": "content", "type": "editor"},
      {"name": "published", "type": "bool"}
    ],
    "list_rule": "",
    "view_rule": "",
    "create_rule": "@request.auth.id != '\'''\''",
    "update_rule": "@request.auth.id = @record.user_id || @request.auth.role = '\''admin'\''",
    "delete_rule": "@request.auth.id = @record.user_id || @request.auth.role = '\''admin'\''"
  }'
```

### Access Control Rules
Define fine-grained permissions per collection:
- `list_rule` - Who can list records (empty = public)
- `view_rule` - Who can view a record (empty = public)
- `create_rule` - Who can create records (`@request.auth.id != ''` = authenticated)
- `update_rule` - Who can update records (`@request.auth.id = @record.user_id` = owner only)
- `delete_rule` - Who can delete records (`@request.auth.role = 'admin'` = admin only)

Examples:
- Public: `""` or `null`
- Authenticated only: `"@request.auth.id != ''"`
- Owner only: `"@request.auth.id = @record.user_id"`
- Admin only: `"@request.auth.role = 'admin'"`
- Owner or Admin: `"@request.auth.id = @record.user_id || @request.auth.role = 'admin'"`

## Admin Dashboard

FastCMS includes a complete admin dashboard for managing your backend.

### Access
- URL: http://localhost:8000/admin/
- Requires admin role (set `role` field to `"admin"` in users table)

### Features
- **Dashboard Overview**: System statistics and quick actions
- **User Management**: View, promote/demote, and delete users
- **Collection Management**: Browse collections, view schemas, and manage access rules
- **Access Control**: View and manage permission rules per collection
- **API Documentation**: Direct link to interactive API docs

### Creating an Admin User

First register a user, then update their role:
```bash
# 1. Register a user
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "SecureAdmin123!",
    "password_confirm": "SecureAdmin123!",
    "name": "Admin User"
  }'

# 2. Update role in database (requires database access)
# SQLite:
# sqlite3 data/fastcms.db "UPDATE users SET role = 'admin' WHERE email = 'admin@example.com';"
```

### Admin API Endpoints
- `GET /api/v1/admin/stats` - System statistics
- `GET /api/v1/admin/users` - List all users
- `PATCH /api/v1/admin/users/{id}/role` - Update user role
- `DELETE /api/v1/admin/users/{id}` - Delete user
- `GET /api/v1/admin/collections` - List all collections
- `DELETE /api/v1/admin/collections/{id}` - Delete collection

## Testing

Run tests with pytest:
```bash
# Install dev dependencies
pip install -r requirements.txt ".[dev]"

# Run all tests
pytest

# Run specific test suites
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/e2e/           # End-to-end tests

# Run with coverage
pytest --cov=app --cov-report=html
```

### Test Coverage
- **Unit Tests**: Access control engine, field validation
- **Integration Tests**: Admin API endpoints, authentication flows
- **E2E Tests**: Complete workflows including access control and admin operations

## License

MIT License
