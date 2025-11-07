# FastCMS

**AI-Native** Backend-as-a-Service built with FastAPI. Create dynamic collections, REST APIs, and authentication without writing SQL - powered by LangChain and AI.

## Features Status

### Core Features
- [x] Dynamic Collections - Create database tables via API
- [x] Authentication - JWT-based auth with register/login
- [x] Email Verification - Secure email verification flow
- [x] Password Reset - Token-based password recovery
- [x] CRUD API - Create, read, update, delete records
- [x] Advanced Filtering - PocketBase-like query syntax
- [x] Relation Expansion - Fetch related records automatically
- [x] File Storage - Upload and serve files
- [x] Real-time Updates - Server-Sent Events
- [x] Webhooks - HTTP callbacks for record events
- [x] Rate Limiting - Per-IP request limiting
- [x] Access Control - Permission rules per collection with role-based access
- [x] Admin Dashboard - Complete web UI for management

### AI Features
- [x] Natural Language to API Query - Convert plain English to filter syntax
- [x] Semantic Search - Vector embeddings with FAISS/Qdrant
- [x] AI Content Generation - GPT-4/Claude powered content creation
- [x] Schema Generation - Auto-generate collection schemas from descriptions
- [x] Data Enrichment - AI-powered data validation and enhancement
- [x] AI Chat Assistant - Help with API usage and data modeling
- [x] Streaming Responses - Real-time AI generation via SSE

## Quick Start

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
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"  # Installs all dependencies including dev tools
# Or use: pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env and set SECRET_KEY (generate: openssl rand -hex 32)

# Run database migrations (if using existing database)
alembic upgrade head

# Start the server
python app/main.py
# Or with uvicorn: uvicorn app.main:app --reload
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
│   ├── admin/           # Admin dashboard (UI routes & templates)
│   ├── api/v1/          # API endpoints (auth, collections, records, files, admin)
│   ├── core/            # Configuration, security, access control
│   ├── db/              # Database models & repositories
│   ├── schemas/         # Pydantic models
│   ├── services/        # Business logic
│   ├── utils/           # Utility functions
│   └── main.py          # App entry point
├── migrations/          # Alembic database migrations
├── tests/               # Test suites (unit, integration, e2e)
├── data/                # Database & uploaded files
└── pyproject.toml       # Project dependencies & configuration
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

### Advanced Filtering
Query records using PocketBase-like filter syntax:

```bash
# Greater than or equal
curl "http://localhost:8000/api/v1/users/records?filter=age>=18"

# Multiple conditions with AND
curl "http://localhost:8000/api/v1/users/records?filter=age>=18&&status=active"

# Text search (like)
curl "http://localhost:8000/api/v1/users/records?filter=email~gmail.com"

# Sorting (prefix with - for descending)
curl "http://localhost:8000/api/v1/posts/records?sort=-created"
```

Supported operators:
- `=` - Equal
- `!=` - Not equal
- `>` - Greater than
- `<` - Less than
- `>=` - Greater than or equal
- `<=` - Less than or equal
- `~` - Contains (like)
- `&&` - AND condition

### Relation Expansion
Automatically fetch related records:

```bash
# Expand single relation
curl "http://localhost:8000/api/v1/posts/records/{id}?expand=author"

# Expand multiple relations
curl "http://localhost:8000/api/v1/posts/records/{id}?expand=author,category"
```

### Webhooks
Subscribe to record events:

```bash
# Create webhook
curl -X POST "http://localhost:8000/api/v1/webhooks" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-server.com/webhook",
    "collection_name": "posts",
    "events": ["record.created", "record.updated", "record.deleted"],
    "secret": "your_webhook_secret"
  }'
```

Webhook payload includes HMAC signature (X-Webhook-Signature header) for verification.

### Email Verification & Password Reset

```bash
# Request password reset
curl -X POST "http://localhost:8000/api/v1/auth/request-password-reset" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'

# Verify email with token
curl -X POST "http://localhost:8000/api/v1/auth/verify-email" \
  -H "Content-Type: application/json" \
  -d '{"token": "TOKEN_FROM_EMAIL"}'

# Reset password with token
curl -X POST "http://localhost:8000/api/v1/auth/reset-password" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "TOKEN_FROM_EMAIL",
    "password": "NewPass123!",
    "password_confirm": "NewPass123!"
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

## AI Features

FastCMS includes powerful AI features powered by LangChain, supporting OpenAI, Anthropic Claude, and local LLMs via Ollama.

### Configuration

```bash
# .env configuration
AI_ENABLED=true
AI_PROVIDER=openai  # or anthropic, ollama

# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Ollama (local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Vector Database
VECTOR_DB_TYPE=faiss  # or qdrant
```

### Install AI Dependencies

```bash
pip install ".[ai]"  # Installs langchain, openai, anthropic, faiss, etc.
```

### AI Content Generation

Generate content with streaming support:

```bash
# Generate content
curl -X POST "http://localhost:8000/api/v1/ai/generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a blog post about FastCMS",
    "context": {"tone": "professional", "length": "medium"},
    "max_tokens": 500
  }'

# Stream generated content (SSE)
curl -X POST "http://localhost:8000/api/v1/ai/generate/stream" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write an article about AI in CMS"}'
```

### Natural Language Queries

Convert plain English to API filter syntax:

```bash
curl -X POST "http://localhost:8000/api/v1/ai/query/natural-language" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find all active users over 18 years old",
    "collection_name": "users"
  }'

# Returns: {"filter_expression": "age>=18&&status=active"}
```

### Semantic Search

Search using natural language and vector embeddings:

```bash
# Index a collection first (admin only)
curl -X POST "http://localhost:8000/api/v1/ai/index/collection" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "articles",
    "rebuild": true
  }'

# Perform semantic search
curl -X POST "http://localhost:8000/api/v1/ai/search/semantic" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "content about FastAPI performance",
    "collection_name": "articles",
    "k": 5,
    "score_threshold": 0.7
  }'
```

### AI Schema Generation

Generate collection schemas from natural language descriptions:

```bash
curl -X POST "http://localhost:8000/api/v1/ai/schema/generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "A blog post with title, content, author, tags, and publication date"
  }'

# Returns suggested schema with field types and validations
```

### Data Enrichment

Use AI to validate, enhance, or transform data:

```bash
curl -X POST "http://localhost:8000/api/v1/ai/enrich" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "title": "my blog post",
      "content": "some content here"
    },
    "instructions": "Fix capitalization, add a meta description, and suggest 3 relevant tags"
  }'
```

### AI Chat Assistant

Chat with AI about FastCMS usage:

```bash
curl -X POST "http://localhost:8000/api/v1/ai/chat" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How do I create a collection with relation fields?",
    "history": []
  }'
```

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

## Architecture & Design

### Security Features
- JWT-based authentication with access and refresh tokens
- Password hashing with bcrypt
- Email verification for new accounts
- Secure password reset with time-limited tokens
- Role-based access control (user, admin)
- Fine-grained permission rules per collection
- Webhook signature verification with HMAC
- CORS protection
- Rate limiting (100 req/min, 1000 req/hour per IP)

### Performance Optimizations
- Async/await throughout for non-blocking I/O
- orjson for fast JSON serialization
- SQLAlchemy 2.0 with async support
- Connection pooling
- Efficient database queries with pagination

### Best Practices
- Type hints throughout the codebase
- Pydantic v2 for data validation
- Clean architecture with separation of concerns
- Repository pattern for data access
- Service layer for business logic
- Comprehensive error handling
- Structured logging

## Roadmap

### Completed ✅
- [x] Core CMS functionality
- [x] Authentication & authorization
- [x] Email verification
- [x] Password reset functionality
- [x] Access control system
- [x] Advanced querying & filtering
- [x] Relation expansion
- [x] Webhooks system
- [x] API rate limiting
- [x] Admin dashboard
- [x] File storage
- [x] Real-time updates
- [x] **AI Integration** - LangChain/LangGraph with OpenAI, Anthropic, Ollama
- [x] **Semantic Search** - Vector embeddings with FAISS/Qdrant
- [x] **Natural Language Queries** - Plain English to API filters
- [x] **AI Content Generation** - GPT-4/Claude powered generation
- [x] **AI Chat Assistant** - Help with API usage
- [x] Comprehensive test coverage

### Next Steps 🚀
- [ ] OAuth2 providers (Google, GitHub, etc.)
- [ ] Multi-tenancy support
- [ ] S3-compatible storage
- [ ] Database backups
- [ ] Audit logging

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details
