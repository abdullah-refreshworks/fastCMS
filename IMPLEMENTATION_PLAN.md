# FastCMS - Comprehensive Implementation Plan

> **Mission:** Transform FastCMS into a production-ready, perfectly functioning AI-native BaaS with zero errors
>
> **Timeline:** 5-7 days intensive development
> **Target:** Pull Request with 100% working features

---

## 📋 Executive Summary

This plan covers:
1. ✅ **Current State Assessment** - What works, what's broken
2. 🔧 **Critical Fixes** - Bug fixes and error handling
3. 🚀 **Core Features** - Implementing missing essentials
4. 🧪 **Testing Strategy** - Comprehensive test coverage
5. 📖 **Documentation** - End-user guides and tutorials
6. 🎯 **Quality Assurance** - Pre-PR validation checklist

---

## Phase 1: Current State Assessment (Day 1 - Morning)

### 1.1 Dependency Audit
**Goal:** Ensure all dependencies are installed and compatible

**Tasks:**
- [ ] Install all core dependencies from requirements.txt
- [ ] Install AI dependencies (langchain, openai, etc.)
- [ ] Check for version conflicts
- [ ] Test import statements for all modules
- [ ] Document any missing dependencies

**Commands:**
```bash
# Install core dependencies
pip install -r requirements.txt

# Install AI dependencies
pip install langchain==0.3.7 langchain-openai==0.2.8 langchain-anthropic==0.2.4
pip install langgraph==0.2.45 faiss-cpu==1.9.0 sentence-transformers==3.3.1
pip install tiktoken==0.8.0 qdrant-client==1.12.1 openai==1.54.5
pip install langchain-community==0.3.7

# Verify all imports
python -c "import fastapi, sqlalchemy, langchain, pydantic; print('✓ All imports successful')"
```

**Expected Output:**
- ✅ All dependencies installed without errors
- ✅ No version conflicts
- ✅ All modules importable

### 1.2 Application Startup Test
**Goal:** Ensure the application starts without errors

**Tasks:**
- [ ] Create .env file from .env.example
- [ ] Generate SECRET_KEY
- [ ] Run database migrations
- [ ] Start application
- [ ] Check health endpoint
- [ ] Review startup logs for errors

**Commands:**
```bash
# Setup environment
cp .env.example .env
SECRET_KEY=$(openssl rand -hex 32)
echo "SECRET_KEY=$SECRET_KEY" >> .env

# Run migrations
alembic upgrade head

# Start application
python app/main.py &
APP_PID=$!
sleep 5

# Test health endpoint
curl http://localhost:8000/health

# Check logs
kill $APP_PID
```

**Expected Output:**
- ✅ Application starts without exceptions
- ✅ Health endpoint returns 200 OK
- ✅ Database connection successful
- ✅ No import errors in logs

### 1.3 API Endpoint Audit
**Goal:** Identify broken or missing endpoints

**Tasks:**
- [ ] List all API routes
- [ ] Test each endpoint for basic functionality
- [ ] Document endpoints with errors
- [ ] Check OpenAPI documentation accessibility

**Test Script:**
```python
# test_endpoints.py
import httpx
import asyncio

async def test_all_endpoints():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        endpoints = [
            ("GET", "/health"),
            ("GET", "/docs"),
            ("GET", "/openapi.json"),
            ("POST", "/api/v1/auth/register"),
            ("GET", "/api/v1/collections"),
        ]

        for method, path in endpoints:
            try:
                if method == "GET":
                    response = await client.get(path)
                else:
                    response = await client.post(path, json={})
                print(f"✓ {method} {path} - {response.status_code}")
            except Exception as e:
                print(f"✗ {method} {path} - ERROR: {e}")

asyncio.run(test_all_endpoints())
```

**Expected Output:**
- ✅ All endpoints respond (even if with validation errors)
- ✅ No 500 Internal Server Errors
- ✅ OpenAPI docs accessible

### 1.4 Database Schema Validation
**Goal:** Ensure database schema is correct

**Tasks:**
- [ ] Check all tables created
- [ ] Validate foreign key constraints
- [ ] Test data insertion
- [ ] Verify migrations applied

**Commands:**
```bash
# Check database
sqlite3 data/app.db ".schema" | grep "CREATE TABLE"
sqlite3 data/app.db "SELECT name FROM sqlite_master WHERE type='table';"

# Test basic operations
sqlite3 data/app.db "INSERT INTO users (id, email, password_hash, verified, role, created, updated)
VALUES ('test-id', 'test@example.com', 'hash', 1, 'user', datetime('now'), datetime('now'));"
sqlite3 data/app.db "SELECT * FROM users WHERE email='test@example.com';"
```

**Expected Output:**
- ✅ All tables exist (users, refresh_tokens, collections, files, webhooks, etc.)
- ✅ No constraint violations
- ✅ Data insertion successful

---

## Phase 2: Critical Bug Fixes (Day 1 - Afternoon)

### 2.1 Error Handling Implementation
**Priority:** CRITICAL
**Goal:** Add comprehensive error handling throughout the codebase

#### 2.1.1 Global Exception Handler
**File:** `app/core/exceptions.py`

**Tasks:**
- [x] Custom exception classes exist
- [ ] Add global exception handler in main.py
- [ ] Add request validation error handler
- [ ] Add database error handler
- [ ] Add authentication error handler

**Implementation:**
```python
# app/main.py - Add exception handlers
from app.core.exceptions import (
    NotFoundException,
    UnauthorizedException,
    ForbiddenException,
    BadRequestException
)
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "detail": exc.errors(),
            "body": exc.body
        }
    )

@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Database Error",
            "detail": "An error occurred while processing your request"
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )
```

#### 2.1.2 Service Layer Error Handling
**Files:** `app/services/*.py`

**Tasks:**
- [ ] Add try-catch blocks to all service methods
- [ ] Add detailed error logging
- [ ] Return meaningful error messages
- [ ] Handle edge cases (null values, empty results)

**Example Pattern:**
```python
# app/services/collection_service.py
async def create_collection(self, data: CollectionCreate) -> Collection:
    try:
        # Validate collection name
        if not data.name or not data.name.strip():
            raise BadRequestException("Collection name cannot be empty")

        # Check for duplicates
        existing = await self.collection_repo.get_by_name(data.name)
        if existing:
            raise BadRequestException(f"Collection '{data.name}' already exists")

        # Create collection
        collection = await self.collection_repo.create(data)
        logger.info(f"Collection created: {collection.name}")
        return collection

    except BadRequestException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error creating collection: {e}")
        raise BadRequestException("Failed to create collection")
    except Exception as e:
        logger.error(f"Unexpected error creating collection: {e}")
        raise BadRequestException("An unexpected error occurred")
```

#### 2.1.3 API Route Error Handling
**Files:** `app/api/v1/*.py`

**Tasks:**
- [ ] Add error handling to all route handlers
- [ ] Validate request data
- [ ] Return proper HTTP status codes
- [ ] Add request logging

**Example Pattern:**
```python
@router.post("/collections", response_model=CollectionResponse, status_code=201)
async def create_collection(
    data: CollectionCreate,
    current_user: User = Depends(get_current_admin),
    collection_service: CollectionService = Depends(get_collection_service)
):
    """Create a new collection (admin only)."""
    try:
        collection = await collection_service.create_collection(data)
        return collection
    except BadRequestException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in create_collection endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### 2.2 AI Service Error Handling
**Priority:** HIGH
**Goal:** Ensure AI features don't crash the app

**Tasks:**
- [ ] Add AI provider availability checks
- [ ] Handle missing API keys gracefully
- [ ] Add timeout handling
- [ ] Implement retry logic
- [ ] Provide fallback responses

**Implementation:**
```python
# app/services/ai_service.py
async def generate_content(self, prompt: str, **kwargs) -> str:
    """Generate content with comprehensive error handling."""
    try:
        # Check if AI is enabled
        if not self.settings.AI_ENABLED:
            raise BadRequestException("AI features are not enabled")

        # Check API key
        if not self._get_api_key():
            raise BadRequestException(
                f"API key not configured for {self.settings.AI_PROVIDER}"
            )

        # Set timeout
        timeout = kwargs.get("timeout", 30)

        # Generate with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with asyncio.timeout(timeout):
                    response = await self.llm.ainvoke(prompt)
                    return response.content
            except asyncio.TimeoutError:
                if attempt == max_retries - 1:
                    raise BadRequestException("AI request timed out")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

    except BadRequestException:
        raise
    except Exception as e:
        logger.error(f"AI generation error: {e}")
        raise BadRequestException(f"AI generation failed: {str(e)}")
```

### 2.3 Database Connection Handling
**Priority:** CRITICAL
**Goal:** Ensure database connections are managed properly

**Tasks:**
- [ ] Add connection pooling configuration
- [ ] Implement connection retry logic
- [ ] Add connection health checks
- [ ] Handle connection timeouts
- [ ] Clean up connections on shutdown

**Implementation:**
```python
# app/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
import logging

logger = logging.getLogger(__name__)

def create_engine(database_url: str, echo: bool = False):
    """Create database engine with proper connection handling."""
    try:
        engine = create_async_engine(
            database_url,
            echo=echo,
            poolclass=QueuePool if "sqlite" not in database_url else NullPool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,   # Recycle connections after 1 hour
        )
        logger.info("Database engine created successfully")
        return engine
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        raise

async def get_db() -> AsyncSession:
    """Get database session with error handling."""
    session = None
    try:
        session = AsyncSessionLocal()
        yield session
    except Exception as e:
        logger.error(f"Database session error: {e}")
        if session:
            await session.rollback()
        raise
    finally:
        if session:
            await session.close()
```

### 2.4 File Upload Error Handling
**Priority:** HIGH
**Goal:** Handle file upload errors gracefully

**Tasks:**
- [ ] Validate file size
- [ ] Validate file type
- [ ] Handle disk space errors
- [ ] Clean up failed uploads
- [ ] Return detailed error messages

**Implementation:**
```python
# app/services/file_service.py
async def upload_file(
    self,
    file: UploadFile,
    user_id: str,
    collection_name: Optional[str] = None
) -> File:
    """Upload file with comprehensive error handling."""
    temp_path = None
    try:
        # Validate file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset

        max_size = self.settings.MAX_FILE_SIZE
        if file_size > max_size:
            raise BadRequestException(
                f"File too large. Maximum size: {max_size / 1024 / 1024}MB"
            )

        # Validate file type
        if not self._is_allowed_file_type(file.content_type):
            raise BadRequestException(
                f"File type not allowed: {file.content_type}"
            )

        # Generate unique filename
        file_id = str(uuid.uuid4())
        extension = Path(file.filename).suffix
        filename = f"{file_id}{extension}"

        # Ensure storage directory exists
        storage_path = Path(self.settings.LOCAL_STORAGE_PATH)
        storage_path.mkdir(parents=True, exist_ok=True)

        # Save file
        temp_path = storage_path / filename
        async with aiofiles.open(temp_path, 'wb') as f:
            while chunk := await file.read(8192):
                await f.write(chunk)

        # Create database record
        file_record = await self.file_repo.create(
            filename=filename,
            original_filename=file.filename,
            mime_type=file.content_type,
            size=file_size,
            storage_path=str(temp_path),
            user_id=user_id,
            collection_name=collection_name
        )

        logger.info(f"File uploaded: {filename}")
        return file_record

    except BadRequestException:
        # Clean up temp file
        if temp_path and temp_path.exists():
            temp_path.unlink()
        raise
    except Exception as e:
        # Clean up temp file
        if temp_path and temp_path.exists():
            temp_path.unlink()
        logger.error(f"File upload error: {e}")
        raise BadRequestException("File upload failed")
```

---

## Phase 3: Core Feature Implementation (Days 2-3)

### 3.1 Configuration Validation
**Priority:** CRITICAL
**File:** `app/core/config.py`

**Tasks:**
- [ ] Add environment variable validation
- [ ] Provide sensible defaults
- [ ] Add configuration validation on startup
- [ ] Document all configuration options

**Implementation:**
```python
# app/core/config.py
from pydantic import field_validator, ValidationError
from typing import Optional
import secrets

class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "FastCMS"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if not v or len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters. "
                "Generate one with: openssl rand -hex 32"
            )
        return v

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/app.db"

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v:
            raise ValueError("DATABASE_URL is required")
        return v

    # AI Settings
    AI_ENABLED: bool = True
    AI_PROVIDER: str = "openai"  # openai, anthropic, ollama

    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: Optional[str] = "http://localhost:11434"

    @field_validator("AI_ENABLED")
    @classmethod
    def validate_ai_config(cls, v: bool, values) -> bool:
        if v:
            provider = values.data.get("AI_PROVIDER", "openai")
            if provider == "openai" and not values.data.get("OPENAI_API_KEY"):
                raise ValueError(
                    "OPENAI_API_KEY required when AI_ENABLED=true and AI_PROVIDER=openai"
                )
            if provider == "anthropic" and not values.data.get("ANTHROPIC_API_KEY"):
                raise ValueError(
                    "ANTHROPIC_API_KEY required when AI_ENABLED=true and AI_PROVIDER=anthropic"
                )
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

def get_settings() -> Settings:
    """Get validated settings with error handling."""
    try:
        return Settings()
    except ValidationError as e:
        print("❌ Configuration Error:")
        for error in e.errors():
            print(f"  - {error['loc'][0]}: {error['msg']}")
        print("\n💡 Check your .env file and ensure all required variables are set")
        raise SystemExit(1)

settings = get_settings()
```

### 3.2 Startup Event Handlers
**Priority:** HIGH
**File:** `app/main.py`

**Tasks:**
- [ ] Add database initialization
- [ ] Add health checks
- [ ] Validate configuration
- [ ] Initialize AI services
- [ ] Create default admin user

**Implementation:**
```python
# app/main.py
@app.on_event("startup")
async def startup_event():
    """Run startup tasks."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Validate configuration
    logger.info("✓ Configuration validated")

    # Initialize database
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✓ Database initialized")
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        raise

    # Test database connection
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
        logger.info("✓ Database connection successful")
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        raise

    # Initialize AI services (if enabled)
    if settings.AI_ENABLED:
        try:
            # Test AI provider connection
            from app.services.ai_service import AIService
            ai_service = AIService()
            # Add a simple test
            logger.info(f"✓ AI service initialized ({settings.AI_PROVIDER})")
        except Exception as e:
            logger.warning(f"⚠ AI service initialization failed: {e}")
            logger.warning("  AI features will be disabled")

    # Log startup complete
    logger.info(f"🚀 {settings.APP_NAME} started successfully")
    logger.info(f"   Environment: {settings.ENVIRONMENT}")
    logger.info(f"   Debug mode: {settings.DEBUG}")
    logger.info(f"   API Docs: http://localhost:8000/docs")

@app.on_event("shutdown")
async def shutdown_event():
    """Run shutdown tasks."""
    logger.info("Shutting down...")

    # Close database connections
    await engine.dispose()
    logger.info("✓ Database connections closed")

    logger.info("👋 Shutdown complete")
```

### 3.3 Health Check Endpoint Enhancement
**Priority:** MEDIUM
**File:** `app/main.py`

**Tasks:**
- [ ] Add detailed health information
- [ ] Check database connectivity
- [ ] Check AI service availability
- [ ] Return proper status codes

**Implementation:**
```python
@app.get("/health", tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """Comprehensive health check endpoint."""
    health_status = {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Check AI service
    if settings.AI_ENABLED:
        try:
            # Simple availability check
            health_status["services"]["ai"] = {
                "status": "healthy",
                "provider": settings.AI_PROVIDER
            }
        except Exception as e:
            health_status["services"]["ai"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
    else:
        health_status["services"]["ai"] = "disabled"

    # Return appropriate status code
    status_code = 200 if health_status["status"] == "healthy" else 503

    return JSONResponse(
        status_code=status_code,
        content=health_status
    )
```

### 3.4 Request/Response Logging Middleware
**Priority:** MEDIUM
**File:** `app/core/logging.py`

**Tasks:**
- [ ] Add request logging middleware
- [ ] Log request method, path, duration
- [ ] Log errors with stack traces
- [ ] Add correlation IDs

**Implementation:**
```python
# app/core/logging.py
import logging
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses."""

    async def dispatch(self, request: Request, call_next):
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        # Log request
        start_time = time.time()
        logger.info(
            f"Request started",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None
            }
        )

        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"Request completed",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration": f"{duration:.3f}s"
                }
            )

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration": f"{duration:.3f}s",
                    "error": str(e)
                },
                exc_info=True
            )
            raise

# Add to main.py
app.add_middleware(LoggingMiddleware)
```

---

## Phase 4: Testing Strategy (Days 4-5)

### 4.1 Test Directory Structure

```
tests/
├── __init__.py
├── conftest.py                 # Pytest fixtures
├── unit/                       # Unit tests
│   ├── __init__.py
│   ├── test_access_control.py
│   ├── test_auth_service.py
│   ├── test_collection_service.py
│   ├── test_query_parser.py
│   └── test_validators.py
├── integration/                # Integration tests
│   ├── __init__.py
│   ├── test_auth_api.py
│   ├── test_collections_api.py
│   ├── test_records_api.py
│   ├── test_files_api.py
│   └── test_ai_api.py
└── e2e/                        # End-to-end tests
    ├── __init__.py
    ├── test_user_registration_flow.py
    ├── test_collection_crud_flow.py
    ├── test_file_upload_flow.py
    └── test_ai_workflows.py
```

### 4.2 Test Fixtures (conftest.py)

**File:** `tests/conftest.py`

```python
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient
from typing import AsyncGenerator

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.config import settings

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        yield session

    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()

@pytest.fixture
async def test_user(client: AsyncClient):
    """Create test user."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "TestPass123!",
            "password_confirm": "TestPass123!",
            "name": "Test User"
        }
    )
    assert response.status_code == 201
    return response.json()

@pytest.fixture
async def auth_headers(test_user, client: AsyncClient):
    """Get authentication headers."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "TestPass123!"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

### 4.3 Unit Tests

**File:** `tests/unit/test_auth_service.py`

```python
import pytest
from app.services.auth_service import AuthService
from app.core.exceptions import BadRequestException, UnauthorizedException

@pytest.mark.asyncio
async def test_register_user_success(db_session):
    """Test successful user registration."""
    auth_service = AuthService(db_session)

    user = await auth_service.register(
        email="newuser@example.com",
        password="SecurePass123!",
        name="New User"
    )

    assert user.email == "newuser@example.com"
    assert user.name == "New User"
    assert user.verified is False
    assert user.role == "user"

@pytest.mark.asyncio
async def test_register_duplicate_email(db_session):
    """Test registration with duplicate email."""
    auth_service = AuthService(db_session)

    # Create first user
    await auth_service.register(
        email="duplicate@example.com",
        password="Pass123!",
        name="First"
    )

    # Try to create duplicate
    with pytest.raises(BadRequestException, match="already registered"):
        await auth_service.register(
            email="duplicate@example.com",
            password="Pass123!",
            name="Second"
        )

@pytest.mark.asyncio
async def test_login_success(db_session):
    """Test successful login."""
    auth_service = AuthService(db_session)

    # Register user
    await auth_service.register(
        email="login@example.com",
        password="Pass123!",
        name="Login Test"
    )

    # Login
    tokens = await auth_service.login(
        email="login@example.com",
        password="Pass123!"
    )

    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_credentials(db_session):
    """Test login with invalid credentials."""
    auth_service = AuthService(db_session)

    with pytest.raises(UnauthorizedException):
        await auth_service.login(
            email="nonexistent@example.com",
            password="wrongpass"
        )
```

### 4.4 Integration Tests

**File:** `tests/integration/test_collections_api.py`

```python
import pytest

@pytest.mark.asyncio
async def test_create_collection(client, auth_headers):
    """Test collection creation endpoint."""
    response = await client.post(
        "/api/v1/collections",
        headers=auth_headers,
        json={
            "name": "posts",
            "type": "base",
            "schema": [
                {
                    "name": "title",
                    "type": "text",
                    "validation": {"required": True}
                },
                {
                    "name": "content",
                    "type": "editor",
                    "validation": {}
                }
            ]
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "posts"
    assert data["type"] == "base"
    assert len(data["schema"]) == 2

@pytest.mark.asyncio
async def test_list_collections(client, auth_headers):
    """Test listing collections."""
    # Create collection first
    await client.post(
        "/api/v1/collections",
        headers=auth_headers,
        json={
            "name": "test_collection",
            "type": "base",
            "schema": []
        }
    )

    # List collections
    response = await client.get(
        "/api/v1/collections",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(c["name"] == "test_collection" for c in data["items"])
```

### 4.5 End-to-End Tests

**File:** `tests/e2e/test_user_registration_flow.py`

```python
import pytest

@pytest.mark.asyncio
async def test_complete_user_registration_flow(client):
    """Test complete user registration and authentication flow."""

    # Step 1: Register new user
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "e2e@example.com",
            "password": "E2ETest123!",
            "password_confirm": "E2ETest123!",
            "name": "E2E Test User"
        }
    )
    assert register_response.status_code == 201
    user_data = register_response.json()
    assert user_data["email"] == "e2e@example.com"
    assert user_data["verified"] is False

    # Step 2: Login
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "e2e@example.com",
            "password": "E2ETest123!"
        }
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    access_token = tokens["access_token"]

    # Step 3: Access protected endpoint
    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["email"] == "e2e@example.com"

    # Step 4: Update profile
    update_response = await client.patch(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"name": "Updated Name"}
    )
    assert update_response.status_code == 200
    updated_data = update_response.json()
    assert updated_data["name"] == "Updated Name"

    # Step 5: Logout
    logout_response = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"refresh_token": tokens["refresh_token"]}
    )
    assert logout_response.status_code == 200
```

### 4.6 AI Tests

**File:** `tests/integration/test_ai_api.py`

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
@pytest.mark.skipif(
    not settings.AI_ENABLED,
    reason="AI features disabled"
)
async def test_natural_language_query(client, auth_headers):
    """Test natural language to query conversion."""
    with patch("app.services.ai_service.AIService.natural_language_to_query") as mock:
        mock.return_value = "age>=18&&status=active"

        response = await client.post(
            "/api/v1/ai/query/natural-language",
            headers=auth_headers,
            json={
                "query": "Find all active users over 18",
                "collection_name": "users"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "filter_expression" in data

@pytest.mark.asyncio
async def test_ai_generate_content(client, auth_headers):
    """Test AI content generation."""
    with patch("app.services.ai_service.AIService.generate") as mock:
        mock.return_value = "Generated content about FastCMS"

        response = await client.post(
            "/api/v1/ai/generate",
            headers=auth_headers,
            json={
                "prompt": "Write about FastCMS",
                "max_tokens": 100
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "content" in data
```

### 4.7 Running Tests

**Commands:**
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test category
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run specific test file
pytest tests/unit/test_auth_service.py

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x

# Run tests matching pattern
pytest -k "test_login"
```

---

## Phase 5: Documentation (Day 6)

### 5.1 API Documentation Enhancement

**File:** `docs/API_GUIDE.md`

Create comprehensive API documentation with examples for every endpoint.

### 5.2 Quick Start Guide

**File:** `docs/QUICKSTART.md`

Step-by-step guide for new users to get started in 5 minutes.

### 5.3 Deployment Guide

**File:** `docs/DEPLOYMENT.md`

Instructions for deploying to production (VPS, Docker, Kubernetes).

### 5.4 Troubleshooting Guide

**File:** `docs/TROUBLESHOOTING.md`

Common issues and solutions.

### 5.5 Contributing Guide

**File:** `CONTRIBUTING.md`

Guidelines for contributors.

---

## Phase 6: Pre-PR Quality Assurance (Day 7)

### 6.1 Final Testing Checklist

- [ ] All tests pass (unit, integration, e2e)
- [ ] Test coverage > 80%
- [ ] Application starts without errors
- [ ] All API endpoints work
- [ ] Admin dashboard accessible
- [ ] File uploads work
- [ ] Authentication flows work
- [ ] AI features work (with API keys)
- [ ] Database migrations apply cleanly
- [ ] No console errors or warnings

### 6.2 Code Quality Checklist

- [ ] Code formatted with Black
- [ ] No linting errors (Ruff)
- [ ] Type hints on all functions
- [ ] Docstrings on public functions
- [ ] No commented-out code
- [ ] No TODO comments without issue links
- [ ] Error handling in all services
- [ ] Logging in all critical paths

### 6.3 Documentation Checklist

- [ ] README.md up to date
- [ ] ROADMAP.md accurate
- [ ] USER_GUIDE.md complete
- [ ] API documentation complete
- [ ] All .env.example variables documented
- [ ] Migration guide if needed
- [ ] Changelog updated

### 6.4 Security Checklist

- [ ] No hardcoded secrets
- [ ] No sensitive data in logs
- [ ] CORS configured properly
- [ ] Rate limiting enabled
- [ ] SQL injection prevention verified
- [ ] XSS prevention verified
- [ ] CSRF protection where needed
- [ ] Dependencies up to date

### 6.5 Performance Checklist

- [ ] Database queries optimized
- [ ] Indexes on frequently queried fields
- [ ] No N+1 queries
- [ ] File uploads handle large files
- [ ] API response times < 500ms
- [ ] Memory leaks checked
- [ ] Connection pools configured

---

## Phase 7: Pull Request Creation

### 7.1 PR Title
```
feat: Production-ready FastCMS with comprehensive error handling and tests
```

### 7.2 PR Description Template
```markdown
## Summary
This PR transforms FastCMS into a production-ready AI-native BaaS with:
- Comprehensive error handling throughout the codebase
- Full test suite (unit, integration, e2e)
- Enhanced documentation
- Bug fixes and stability improvements

## Changes Made

### Error Handling
- ✅ Global exception handlers
- ✅ Service layer error handling
- ✅ API route error handling
- ✅ Database connection error handling
- ✅ AI service error handling
- ✅ File upload error handling

### Testing
- ✅ Unit tests for all services (XX tests)
- ✅ Integration tests for all APIs (XX tests)
- ✅ End-to-end workflow tests (XX tests)
- ✅ Test coverage: XX%

### Documentation
- ✅ Enhanced README
- ✅ Complete API guide
- ✅ Quick start guide
- ✅ Deployment guide
- ✅ Troubleshooting guide

### Features
- ✅ Configuration validation
- ✅ Startup health checks
- ✅ Request/response logging
- ✅ Enhanced health endpoint
- ✅ [List other features]

## Testing Performed
- [X] All unit tests pass
- [X] All integration tests pass
- [X] All e2e tests pass
- [X] Manual testing of critical paths
- [X] Tested with and without AI enabled
- [X] Tested authentication flows
- [X] Tested file uploads
- [X] Tested admin dashboard

## Breaking Changes
- None

## Migration Guide
No migration needed.

## Checklist
- [X] Tests added/updated
- [X] Documentation updated
- [X] Code formatted (Black)
- [X] No linting errors
- [X] Changelog updated
- [X] No hardcoded secrets
- [X] All CI checks pass

## Screenshots
[If applicable, add screenshots of new features]

## Related Issues
Closes #X
Fixes #Y
```

---

## Success Metrics

### Before This Plan
- ❌ Application may crash with errors
- ❌ Limited error messages
- ❌ No comprehensive tests
- ❌ Documentation gaps
- ❌ AI features may fail silently

### After This Plan
- ✅ Application runs reliably
- ✅ Detailed error messages
- ✅ 80%+ test coverage
- ✅ Complete documentation
- ✅ AI features degrade gracefully
- ✅ Production-ready deployment
- ✅ Perfect end-user experience

---

## Timeline Summary

| Day | Phase | Deliverable |
|-----|-------|-------------|
| 1 AM | Assessment | Current state documented |
| 1 PM | Critical Fixes | Error handling implemented |
| 2-3 | Core Features | Missing features added |
| 4-5 | Testing | Full test suite completed |
| 6 | Documentation | All docs complete |
| 7 | QA & PR | Pull request submitted |

---

## Next Steps

1. **Review this plan** - Adjust priorities if needed
2. **Set up development environment** - Install dependencies
3. **Start with Phase 1** - Assess current state
4. **Execute systematically** - One phase at a time
5. **Test continuously** - Don't accumulate bugs
6. **Document as you go** - Don't save docs for last
7. **Submit PR** - When all checks pass

---

**Let's build the perfect AI-native BaaS! 🚀**
