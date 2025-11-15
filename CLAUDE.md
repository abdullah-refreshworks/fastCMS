# CLAUDE.md - AI Assistant Guide for FastCMS

This document provides comprehensive guidance for AI assistants working on the FastCMS codebase. It covers the project structure, development workflows, key conventions, and best practices.

## Project Overview

**FastCMS** is an AI-Native Backend-as-a-Service (BaaS) built with FastAPI. It provides dynamic collections, REST APIs, authentication, and AI-powered features without requiring users to write SQL.

### Key Features
- Dynamic Collections: Create database tables via API
- Authentication: JWT + OAuth2 (Google, GitHub, Microsoft)
- Access Control: Fine-grained permission rules per collection
- CRUD API: Create, read, update, delete with advanced filtering
- AI Features: Natural language queries, semantic search, content generation
- Real-time: Server-Sent Events (SSE) for live updates
- File Storage: Local, S3, Azure blob storage
- Admin Dashboard: Complete web UI for management
- Webhooks: HTTP callbacks for record events

### Technology Stack
- **Framework**: FastAPI 0.115.0 (async ASGI)
- **Database**: SQLAlchemy 2.0.35 (async ORM), SQLite/PostgreSQL
- **Validation**: Pydantic v2
- **Auth**: JWT (python-jose), OAuth2 (authlib)
- **AI**: LangChain 0.3.7, OpenAI, Anthropic Claude, Ollama
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Code Quality**: black, ruff, mypy (strict mode)

## Codebase Structure

```
fastCMS/
├── app/                    # Main application code
│   ├── admin/             # Web UI dashboard (Jinja2 templates, static files)
│   ├── ai/                # AI features module (agents, embeddings, workflows)
│   ├── api/v1/            # REST API endpoints
│   ├── core/              # Core systems (config, security, access control)
│   ├── db/                # Database layer (models, repositories, session)
│   ├── schemas/           # Pydantic models for API validation
│   ├── services/          # Business logic layer
│   ├── utils/             # Utility functions
│   └── main.py            # FastAPI application entry point
├── cli/                   # CLI commands (fastcms command)
├── migrations/            # Alembic database migrations
├── tests/                 # Test suites (unit, integration, e2e)
├── data/                  # Runtime data (database, uploaded files)
├── sdk/                   # Client SDKs (TypeScript)
├── pyproject.toml         # Project configuration & dependencies
├── alembic.ini           # Database migration configuration
└── .env.example          # Environment variables template
```

## Architecture & Design Patterns

### Layered Architecture

FastCMS follows clean architecture principles with clear separation of concerns:

1. **API Layer** (`app/api/v1/`): FastAPI routes, request/response handling
2. **Service Layer** (`app/services/`): Business logic, orchestration
3. **Repository Layer** (`app/db/repositories/`): Data access abstraction
4. **Model Layer** (`app/db/models/`): SQLAlchemy ORM models

### Design Patterns

- **Repository Pattern**: Abstracts data access from business logic
- **Service Layer Pattern**: Encapsulates business logic
- **Factory Pattern**: Dynamic SQLAlchemy model generation
- **Observer Pattern**: Event system with 30+ event types
- **Strategy Pattern**: Pluggable storage backends (local, S3, Azure)
- **Dependency Injection**: FastAPI's dependency system
- **Decorator Pattern**: Hooks system for extending functionality

### Key Architectural Decisions

1. **Async-First**: All I/O operations use async/await for performance
2. **Type Safety**: Full type hints throughout, mypy strict mode
3. **Pydantic v2**: All API inputs/outputs validated with Pydantic
4. **Event-Driven**: Hooks allow extending behavior without modifying core
5. **Dynamic Schema**: Runtime table generation from JSON schemas
6. **Access Control**: Rule-based permissions evaluated per request

## File Organization Rules

### When to Create New Files

- **New API Endpoint Group**: Create new file in `app/api/v1/` (e.g., `analytics.py`)
- **New Business Logic Domain**: Create service in `app/services/` (e.g., `analytics_service.py`)
- **New Database Model**: Add to `app/db/models/` (e.g., `analytics.py`)
- **New Repository**: Add to `app/db/repositories/` (e.g., `analytics.py`)
- **New Pydantic Schemas**: Add to `app/schemas/` (e.g., `analytics.py`)

### When to Edit Existing Files

- **Adding to Existing API Group**: Edit corresponding file in `app/api/v1/`
- **Enhancing Existing Service**: Edit corresponding service file
- **Modifying Existing Model**: Edit corresponding model file
- **Adding Utility Functions**: Add to existing or new file in `app/utils/`

### File Naming Conventions

- **Python Files**: `snake_case.py` (e.g., `auth_service.py`)
- **Classes**: `PascalCase` (e.g., `AuthService`, `UserRepository`)
- **Functions**: `snake_case` (e.g., `create_user`, `validate_email`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_FILE_SIZE`, `DEFAULT_PAGE_SIZE`)
- **Test Files**: `test_*.py` (e.g., `test_auth_service.py`)

## Development Workflow

### Initial Setup

```bash
# Clone repository
git clone https://github.com/aalhommada/fastCMS.git
cd fastCMS

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -e ".[dev]"    # Development install with dev tools
# pip install -e ".[all]"  # All features including AI, S3, Azure

# Setup environment
cp .env.example .env
# Edit .env - MUST set SECRET_KEY (generate with: openssl rand -hex 32)

# Run migrations
alembic upgrade head

# Start development server
python app/main.py
# OR: uvicorn app.main:app --reload
# OR: fastcms dev --reload
```

### Environment Variables

Key environment variables to configure:

```bash
# Required
SECRET_KEY=<generate-with-openssl-rand-hex-32>
DATABASE_URL=sqlite+aiosqlite:///./data/app.db

# Optional but recommended
AI_ENABLED=true
AI_PROVIDER=openai  # or anthropic, ollama
OPENAI_API_KEY=<your-key>
SMTP_HOST=smtp.gmail.com
SMTP_USER=<your-email>
SMTP_PASSWORD=<your-password>
```

### Common Development Tasks

#### Running the Application

```bash
# Development mode with hot reload
python app/main.py

# Or with uvicorn directly
uvicorn app.main:app --reload --port 8000

# Using CLI
fastcms dev --port 8000 --reload
```

#### Running Tests

```bash
# All tests
pytest

# Specific test suite
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# With coverage report
pytest --cov=app --cov-report=html

# Single test file
pytest tests/e2e/test_auth_features.py -v
```

#### Code Quality

```bash
# Format code with black
black app/ cli/ tests/

# Lint with ruff
ruff check app/ cli/ tests/

# Type check with mypy
mypy app/

# Run all quality checks
black app/ && ruff check app/ && mypy app/ && pytest
```

#### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "add new feature"

# Apply migrations
alembic upgrade head

# Revert last migration
alembic downgrade -1

# Show migration history
alembic history
```

## Database Layer

### Models (`app/db/models/`)

All models inherit from `BaseModel` which provides:
- `id`: UUID primary key
- `created`: UTC timestamp
- `updated`: UTC timestamp (auto-updated)
- `to_dict()`: Convert to dictionary

**Key Models:**
- `User`: User accounts with email, password, role
- `Collection`: Collection metadata with schema and access rules
- `RefreshToken`: JWT refresh tokens
- `OAuthAccount`: OAuth provider accounts
- `File`: File metadata
- `Webhook`: Webhook configurations
- `VerificationToken`: Email verification and password reset tokens

### Dynamic Models

FastCMS generates SQLAlchemy models at runtime from collection schemas:

```python
# DynamicModelGenerator creates tables on-the-fly
from app.db.models.dynamic import DynamicModelGenerator

generator = DynamicModelGenerator()
model = await generator.create_model(collection_name, schema)
```

### Repositories (`app/db/repositories/`)

Repositories provide data access methods:

```python
from app.db.repositories.user import UserRepository

async def get_user_by_email(email: str):
    async with get_db_context() as db:
        repo = UserRepository(db)
        user = await repo.get_by_email(email)
        return user
```

**Pattern:**
- Constructor takes `AsyncSession`
- Methods are async
- Handle database exceptions
- Return models or None

### Database Session

```python
# In API endpoints (FastAPI dependency)
from app.core.dependencies import get_db

async def my_endpoint(db: AsyncSession = Depends(get_db)):
    # Use db session
    pass

# In CLI or services (context manager)
from app.db.session import get_db_context

async with get_db_context() as db:
    # Use db session
    pass
```

## API Development Patterns

### Creating New Endpoints

1. **Define Pydantic Schemas** (`app/schemas/`)

```python
# app/schemas/analytics.py
from pydantic import BaseModel, Field

class AnalyticsRequest(BaseModel):
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")

class AnalyticsResponse(BaseModel):
    total_users: int
    total_collections: int
    message: str = "✅ Analytics retrieved successfully"
```

2. **Create Service** (`app/services/`)

```python
# app/services/analytics_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.repositories.user import UserRepository

class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_analytics(self, start_date: str, end_date: str) -> dict:
        user_repo = UserRepository(self.db)
        total_users = await user_repo.count()
        # Business logic here
        return {"total_users": total_users}
```

3. **Create API Endpoint** (`app/api/v1/`)

```python
# app/api/v1/analytics.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_user
from app.schemas.analytics import AnalyticsRequest, AnalyticsResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter()

@router.post("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    request: AnalyticsRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = AnalyticsService(db)
    data = await service.get_analytics(request.start_date, request.end_date)
    return AnalyticsResponse(**data)
```

4. **Register Router** (`app/main.py`)

```python
from app.api.v1 import analytics

app.include_router(analytics.router, prefix="/api/v1", tags=["analytics"])
```

### API Response Standards

**Success Response:**
```json
{
  "id": "uuid",
  "field": "value",
  "created": "2024-11-14T00:00:00Z",
  "message": "✅ Success message"
}
```

**List Response:**
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "per_page": 30,
  "message": "✅ Retrieved 30 items"
}
```

**Error Response:**
```json
{
  "error": "ErrorType",
  "message": "❌ User-friendly message",
  "details": "Additional context"
}
```

### Query Parameters

**Standard Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 30, max: 100)
- `filter`: PocketBase-style filter (e.g., `age>=18&&status=active`)
- `sort`: Sort fields (e.g., `name,-created` for name ASC, created DESC)
- `expand`: Relation expansion (e.g., `author,category`)

## Access Control System

FastCMS uses rule-based access control evaluated per request.

### Access Rules

Collections have 5 rule types:
- `list_rule`: Who can list records
- `view_rule`: Who can view a single record
- `create_rule`: Who can create records
- `update_rule`: Who can update records
- `delete_rule`: Who can delete records

### Rule Syntax

Rules use a simple expression language:

```python
# Public (anyone can access)
"" or null

# Authenticated users only
"@request.auth.id != ''"

# Owner only
"@request.auth.id = @record.user_id"

# Admin only
"@request.auth.role = 'admin'"

# Owner or Admin
"@request.auth.id = @record.user_id || @request.auth.role = 'admin'"

# Complex conditions
"@request.auth.verified = true && @record.published = true"
```

**Operators:**
- `=`, `!=`: Equality
- `>`, `<`, `>=`, `<=`: Comparison
- `&&`: AND
- `||`: OR

**Variables:**
- `@request.auth.*`: Current user properties (id, email, role, verified)
- `@record.*`: Record being accessed

### Implementing Access Control

```python
from app.core.access_control import AccessControlEngine

engine = AccessControlEngine()
allowed = await engine.check_access(
    rule="@request.auth.id = @record.user_id",
    user=current_user,
    record=record_dict
)
```

## Events and Hooks System

FastCMS has an event-driven architecture with 30+ event types.

### Event Types

**Record Events:**
- `RECORD_BEFORE_CREATE`, `RECORD_AFTER_CREATE`
- `RECORD_BEFORE_UPDATE`, `RECORD_AFTER_UPDATE`
- `RECORD_BEFORE_DELETE`, `RECORD_AFTER_DELETE`

**Collection Events:**
- `COLLECTION_BEFORE_CREATE`, `COLLECTION_AFTER_CREATE`
- `COLLECTION_BEFORE_UPDATE`, `COLLECTION_AFTER_UPDATE`
- `COLLECTION_BEFORE_DELETE`, `COLLECTION_AFTER_DELETE`

**Auth Events:**
- `AUTH_BEFORE_REGISTER`, `AUTH_AFTER_REGISTER`
- `AUTH_BEFORE_LOGIN`, `AUTH_AFTER_LOGIN`

**File Events:**
- `FILE_BEFORE_UPLOAD`, `FILE_AFTER_UPLOAD`
- `FILE_BEFORE_DELETE`, `FILE_AFTER_DELETE`

### Creating Hooks

```python
from app.core.hooks import hook
from app.core.events import EventType

@hook(EventType.RECORD_AFTER_CREATE)
async def send_welcome_email(context):
    """Send welcome email when user is created"""
    if context.get("collection_name") == "users":
        email = context["record"]["email"]
        # Send email logic

@hook(EventType.RECORD_BEFORE_DELETE)
async def prevent_admin_delete(context):
    """Prevent deleting admin users"""
    if context["record"].get("role") == "admin":
        raise ValueError("Cannot delete admin users")
```

### Dispatching Events

```python
from app.core.events import event_dispatcher, EventType

# Dispatch event
await event_dispatcher.dispatch(
    EventType.RECORD_AFTER_CREATE,
    collection_name="users",
    record=user_dict
)
```

## Testing Guidelines

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests (fast, isolated)
│   └── test_access_control.py
├── integration/             # Integration tests (database, services)
│   └── test_admin_api.py
└── e2e/                     # End-to-end tests (full workflows)
    ├── test_auth_features.py
    └── test_complete_platform.py
```

### Writing Tests

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_collection(client: AsyncClient, admin_token: str):
    """Test creating a new collection"""
    response = await client.post(
        "/api/v1/collections",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "test_collection",
            "type": "base",
            "schema": [
                {"name": "title", "type": "text", "validation": {"required": True}}
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test_collection"
```

### Key Test Fixtures

Available in `tests/conftest.py`:

- `client`: AsyncClient for API testing
- `db`: Database session
- `test_user`: Regular user account
- `admin_user`: Admin user account
- `admin_token`: Admin JWT token
- `user_token`: Regular user JWT token

### Running Specific Tests

```bash
# Run all tests in a file
pytest tests/e2e/test_auth_features.py

# Run specific test
pytest tests/e2e/test_auth_features.py::test_user_registration

# Run with verbose output
pytest -v

# Run with print statements
pytest -s

# Run and stop at first failure
pytest -x
```

## AI Features Development

AI features are optional and require `AI_ENABLED=true` in `.env`.

### AI Service Architecture

```python
# app/services/ai_service.py
class AIService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.provider = self._get_provider()

    async def generate_content(self, prompt: str) -> str:
        # Content generation logic

    async def semantic_search(self, query: str, collection: str) -> list:
        # Vector similarity search
```

### Using Different AI Providers

```python
# Set in .env
AI_PROVIDER=openai      # OpenAI GPT-4
AI_PROVIDER=anthropic   # Anthropic Claude
AI_PROVIDER=ollama      # Local LLMs
```

### Vector Embeddings

```python
from app.services.vector_store_service import VectorStoreService

service = VectorStoreService(db)

# Index collection for semantic search
await service.index_collection("articles", rebuild=True)

# Perform semantic search
results = await service.search(
    query="FastAPI performance",
    collection_name="articles",
    k=5,
    score_threshold=0.7
)
```

## Security Best Practices

### Authentication

```python
# Require authentication
from app.core.dependencies import get_current_user

@router.get("/protected")
async def protected_route(current_user = Depends(get_current_user)):
    # Only authenticated users can access
    pass
```

### Admin-Only Endpoints

```python
from app.core.dependencies import require_admin

@router.delete("/admin/users/{id}")
async def delete_user(
    id: str,
    current_user = Depends(require_admin)
):
    # Only admins can access
    pass
```

### Input Validation

- **Always** use Pydantic models for request validation
- **Never** directly access request.query_params without validation
- **Always** sanitize file uploads

### SQL Injection Prevention

- **Always** use SQLAlchemy ORM methods
- **Never** construct raw SQL with string concatenation
- Use parameterized queries when raw SQL is necessary

### XSS Prevention

- **Always** validate and sanitize user input
- **Never** trust client data
- Use Pydantic validators for complex validation

## Error Handling

### Custom Exceptions

```python
# app/core/exceptions.py
class FastCMSException(Exception):
    """Base exception"""
    pass

class UnauthorizedException(FastCMSException):
    """Unauthorized access"""
    pass

class NotFoundException(FastCMSException):
    """Resource not found"""
    pass
```

### Using Exceptions

```python
from app.core.exceptions import NotFoundException

async def get_collection(id: str):
    collection = await repo.get(id)
    if not collection:
        raise NotFoundException(f"Collection {id} not found")
    return collection
```

### Exception Handlers

Exception handlers are registered in `app/main.py`:

```python
@app.exception_handler(NotFoundException)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "NotFound", "message": str(exc)}
    )
```

## Key Conventions

### Code Style

- **Line Length**: 100 characters (enforced by black)
- **Imports**: Organized by isort (stdlib, third-party, local)
- **Type Hints**: Required for all functions (mypy strict mode)
- **Docstrings**: Google style for complex functions

### Naming Conventions

```python
# Classes: PascalCase
class UserService:
    pass

# Functions and methods: snake_case
async def create_user(email: str):
    pass

# Constants: UPPER_SNAKE_CASE
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Private methods: _leading_underscore
def _internal_helper():
    pass

# Async functions: Always prefix with 'async'
async def fetch_data():
    pass
```

### Async/Await

- **All I/O operations** must use async/await
- **Database queries** must use async session
- **HTTP requests** must use httpx.AsyncClient
- **File operations** must use aiofiles

### Import Organization

```python
# Standard library
import os
from typing import Optional

# Third-party
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

# Local imports
from app.core.dependencies import get_db
from app.schemas.user import UserCreate
from app.services.user_service import UserService
```

## Common Tasks for AI Assistants

### Adding a New Collection Field Type

1. Add type to `app/utils/field_types.py`
2. Update `DynamicModelGenerator` in `app/db/models/dynamic.py`
3. Add validation logic
4. Update tests
5. Update documentation

### Adding a New API Endpoint

1. Create Pydantic schemas in `app/schemas/`
2. Create service in `app/services/`
3. Create endpoint in `app/api/v1/`
4. Register router in `app/main.py`
5. Add tests in `tests/`
6. Update API documentation

### Adding a New OAuth Provider

1. Add credentials to `app/core/config.py`
2. Add provider to `app/services/oauth_service.py`
3. Register routes in `app/api/v1/oauth.py`
4. Update `.env.example`
5. Add tests
6. Update README

### Creating a Database Migration

```bash
# 1. Modify models in app/db/models/
# 2. Generate migration
alembic revision --autogenerate -m "add new field to users"

# 3. Review generated migration in migrations/versions/
# 4. Test migration
alembic upgrade head

# 5. Test rollback
alembic downgrade -1
alembic upgrade head

# 6. Commit migration file
```

### Adding a New Event Type

1. Add event to `EventType` enum in `app/core/events.py`
2. Document event in event dispatcher
3. Dispatch event at appropriate location
4. Create example hook
5. Update tests

## Troubleshooting

### Database Locked Errors

SQLite may show "database is locked" errors. Solutions:
- Ensure WAL mode is enabled (handled by `app/db/session.py`)
- Close all connections properly
- Use PostgreSQL for high-concurrency scenarios

### Migration Conflicts

```bash
# If migrations conflict, reset to head
alembic stamp head

# Or manually resolve conflicts in versions/
```

### Import Errors

- Ensure virtual environment is activated
- Run `pip install -e ".[dev]"` to install in editable mode
- Check Python version (requires 3.11+)

### Test Failures

- Ensure test database is clean: Tests use in-memory SQLite
- Run tests in isolation: `pytest tests/e2e/test_auth.py`
- Check fixtures in `tests/conftest.py`

## Performance Considerations

### Database Queries

- **Use eager loading** for relationships: `selectinload()`, `joinedload()`
- **Paginate large result sets**: Default 30 items per page
- **Index frequently queried columns**: Add indexes in migrations
- **Avoid N+1 queries**: Use relation expansion carefully

### Async Operations

- **Batch operations**: Use `asyncio.gather()` for parallel tasks
- **Avoid blocking calls**: Use async libraries (aiofiles, httpx)
- **Connection pooling**: Configured in `app/db/session.py`

### Caching (Optional)

- Redis caching available with `REDIS_ENABLED=true`
- Cache expensive computations
- Invalidate cache on updates

## Documentation Standards

### API Documentation

- FastAPI auto-generates OpenAPI docs
- Add descriptions to endpoint functions
- Use Pydantic field descriptions
- Include examples in schemas

### Code Documentation

```python
async def complex_function(param: str) -> dict:
    """
    Brief description of function.

    Args:
        param: Description of parameter

    Returns:
        Description of return value

    Raises:
        ValueError: When parameter is invalid
    """
    pass
```

### Updating Documentation

When adding features:
- Update README.md with new feature
- Update API_DOCUMENTATION.md with endpoints
- Update USER_GUIDE.md with usage examples
- Update this CLAUDE.md if architecture changes

## Git Workflow

### Branch Naming

- `feature/<feature-name>`: New features
- `fix/<bug-name>`: Bug fixes
- `docs/<update>`: Documentation updates
- `refactor/<component>`: Code refactoring

### Commit Messages

```
type: brief description

Longer description if needed

- List of changes
- Another change
```

**Types**: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`

### Pull Requests

- Ensure all tests pass
- Run code quality tools
- Update documentation
- Add test coverage for new features

## Environment-Specific Configuration

### Development
```bash
DEBUG=true
ENVIRONMENT=development
DATABASE_URL=sqlite+aiosqlite:///./data/app.db
LOG_LEVEL=DEBUG
```

### Production
```bash
DEBUG=false
ENVIRONMENT=production
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
LOG_LEVEL=INFO
RATE_LIMIT_ENABLED=true
```

## CLI Commands Reference

```bash
# Development
fastcms dev --port 8000 --reload

# User management
fastcms users create admin@example.com --password admin123 --admin
fastcms users list --role admin

# Database
fastcms migrate up
fastcms migrate create "add new feature"

# Collections
fastcms collections list
fastcms collections show posts

# System info
fastcms info
```

## Quick Reference

### Essential Files
- `app/main.py`: Application entry point
- `app/core/config.py`: Configuration management
- `app/core/security.py`: JWT and password hashing
- `app/core/access_control.py`: Permission engine
- `app/db/session.py`: Database session management
- `app/utils/field_types.py`: Field type definitions
- `app/utils/query_parser.py`: Filter parsing

### Key Dependencies
- Get database session: `Depends(get_db)`
- Get current user: `Depends(get_current_user)`
- Require admin: `Depends(require_admin)`
- Pagination: `Depends(pagination_params)`

### Common Imports
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_user
from app.core.exceptions import NotFoundException, UnauthorizedException
from app.schemas.base import PaginatedResponse
```

## Additional Resources

- **API Documentation**: http://localhost:8000/docs (when running)
- **Admin Dashboard**: http://localhost:8000/admin/
- **GitHub Repository**: https://github.com/aalhommada/fastCMS
- **README.md**: Project overview and quick start
- **USER_GUIDE.md**: Comprehensive user guide
- **API_DOCUMENTATION.md**: Detailed API reference

---

**Last Updated**: 2024-11-14
**Version**: 0.1.0
**Python Version**: 3.11+
**FastAPI Version**: 0.115.0

For questions or issues, consult the documentation or examine the test suites for usage examples.
