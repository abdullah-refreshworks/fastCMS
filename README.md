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
- [ ] Admin Dashboard - Web UI for management

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

## License

MIT License
