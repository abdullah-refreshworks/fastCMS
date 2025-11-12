# FastCMS 🚀

<div align="center">

**The AI-Native Backend for Modern Apps**

*Build production-ready backends in hours, not weeks*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Roadmap](ROADMAP.md) • [Contributing](#-contributing)

</div>

---

## 🎯 Why FastCMS?

FastCMS is an **open-source Backend-as-a-Service** that combines:

- 🤖 **AI Superpowers** - LangChain/LangGraph integration, semantic search, natural language queries
- ⚡ **Lightning Fast** - Built on FastAPI, fully async, optimized for performance
- 🔓 **No Vendor Lock-in** - Self-hosted, open-source, own your data
- 🎨 **Dynamic Schema** - Create database tables via API, no migrations needed
- 🔐 **Enterprise Auth** - JWT, OAuth2, MFA, SSO-ready
- 📡 **Real-time Ready** - WebSockets, SSE, webhooks out of the box
- 💰 **Cost Effective** - Run on a $5/month VPS, no per-request pricing

**Stop building the same backend features over and over. Start shipping products.**

---

## ✨ What Makes FastCMS Different?

Unlike traditional BaaS platforms, FastCMS is **AI-native from the ground up**:

| Traditional BaaS | FastCMS (AI-Native) |
|-----------------|---------------------|
| Write SQL queries | **Ask in plain English** |
| Manual data validation | **AI-powered data enrichment** |
| Static schemas | **AI-suggested schema evolution** |
| Basic search | **Semantic vector search** |
| Manual content creation | **AI content generation** |
| Fixed permissions | **AI-driven access control** |

**FastCMS is the only BaaS where AI is not a plugin—it's the foundation.**

## 🌟 Features

### 🤖 AI-Powered Features (Industry First!)

FastCMS is the **only open-source BaaS with built-in AI**:

- **Natural Language Queries** - "Find all active users over 18" → Automatic filter generation
- **Semantic Search** - Vector embeddings (FAISS/Qdrant) for intelligent content discovery
- **AI Content Generation** - GPT-4, Claude, or local LLMs for content creation
- **AI Schema Builder** - Describe your data model in English, get complete schemas
- **AI Data Enrichment** - Automatic data validation, formatting, and enhancement
- **AI Chat Assistant** - Built-in help system that understands your backend
- **Streaming AI** - Real-time AI responses via Server-Sent Events
- **Multi-LLM Support** - OpenAI, Anthropic, Ollama (local models)
- **AI Agents** - *Coming Soon* - Autonomous workflows with LangGraph

### 🔐 Authentication & Authorization

- **Email/Password** - Secure bcrypt hashing, email verification
- **OAuth2 Social Login** - Google, GitHub, Microsoft (15+ providers coming)
- **JWT Tokens** - Access tokens (15min) + refresh tokens (30 days)
- **Password Reset** - Secure token-based recovery flow
- **Role-Based Access Control (RBAC)** - User and admin roles
- **Fine-Grained Permissions** - Expression-based rules per collection
- **Session Management** - Multi-device session tracking
- **MFA/2FA** - *Coming Soon* - TOTP-based two-factor authentication
- **SSO/SAML** - *Coming Soon* - Enterprise single sign-on

### 📊 Database & APIs

- **Dynamic Schema** - Create tables via API, no migrations needed
- **REST API** - Auto-generated CRUD endpoints with OpenAPI docs
- **GraphQL** - *Coming Soon* - Auto-generated GraphQL schema
- **Advanced Filtering** - Expressive query syntax (`age>=18&&status=active`)
- **Relation Expansion** - Auto-fetch related records (`?expand=author,category`)
- **Pagination & Sorting** - Built-in pagination with customizable limits
- **Rate Limiting** - IP-based throttling (100/min, 1000/hour)
- **SQLite** - Default database with WAL mode (PostgreSQL/MySQL coming)
- **Async/Await** - Fully asynchronous for high performance
- **Database Migrations** - Alembic-powered version control

### 📁 File Storage

- **File Upload/Download** - Multi-file support with validation
- **Image Thumbnails** - Automatic thumbnail generation
- **S3-Compatible** - *Coming Soon* - AWS S3, MinIO, DigitalOcean Spaces
- **CDN Integration** - *Coming Soon* - CloudFront, Cloudflare
- **Image Transformation** - *Coming Soon* - On-demand resize, format conversion
- **Video Processing** - *Coming Soon* - FFmpeg-powered transcoding
- **File Versioning** - Track file history and rollbacks

### 📡 Real-time & Events

- **Server-Sent Events (SSE)** - Real-time database subscriptions
- **WebSockets** - *Coming Soon* - Bidirectional real-time communication
- **Webhooks** - HTTP callbacks with HMAC signature verification
- **Event Broadcasting** - Collection-specific and global subscriptions
- **Presence System** - *Coming Soon* - Track online/offline users
- **Collaborative Editing** - *Coming Soon* - CRDT-based real-time collaboration

### 🎨 Admin Dashboard

- **User Management** - View, edit, promote, delete users
- **Collection Browser** - Visual schema editor and data explorer
- **File Manager** - Upload, preview, and manage files
- **Access Control UI** - Configure permission rules visually
- **System Statistics** - Monitor users, collections, and activity
- **API Documentation** - Integrated Swagger/OpenAPI docs
- **Database Studio** - *Coming Soon* - Visual query builder

### 🛠️ Developer Experience

- **CLI Tool** - *Coming Soon* - Command-line management and deployment
- **TypeScript SDK** - *Coming Soon* - Type-safe client with auto-completion
- **Python SDK** - *Coming Soon* - Async client with type hints
- **React Components** - *Coming Soon* - Pre-built UI components
- **Docker Support** - Production-ready Docker images
- **One-Click Deploy** - *Coming Soon* - Railway, Render, Vercel templates
- **OpenAPI Spec** - Automatic API documentation
- **Type Safety** - Full type hints throughout codebase

### 🔍 Monitoring & Observability

- **Structured Logging** - *Coming Soon* - JSON logs with correlation IDs
- **Metrics** - *Coming Soon* - Prometheus/Grafana integration
- **Error Tracking** - *Coming Soon* - Sentry integration
- **Audit Logs** - *Coming Soon* - Complete user action history
- **Performance Monitoring** - *Coming Soon* - APM integration
- **Health Checks** - Built-in health and readiness endpoints

### 🏢 Enterprise Features *(Coming Soon)*

- **Multi-Tenancy** - Organization/workspace isolation
- **SSO/SAML** - Okta, Auth0, Azure AD integration
- **Advanced Security** - IP whitelisting, VPN support
- **Compliance** - GDPR, SOC2, HIPAA toolkits
- **High Availability** - Read replicas, auto-scaling
- **White-Labeling** - Custom branding and domains
- **SLA Guarantees** - 99.9% uptime commitment

## 🚀 Quick Start

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

## 📚 Documentation

- **[Roadmap](ROADMAP.md)** - Feature roadmap and development phases
- **[BaaS Comparison](BAAS_COMPARISON.md)** - How FastCMS compares to alternatives
- **[User Guide](USER_GUIDE.md)** - Complete end-user documentation
- **[API Reference](http://localhost:8000/docs)** - Interactive API documentation

---

## 🎬 Demo Video

*Coming Soon* - Watch a 5-minute demo of building a blog with AI-powered content generation

---

## 💡 Use Cases

### SaaS Applications
Build multi-tenant SaaS apps with dynamic schemas, user authentication, and AI features without backend code.

### Mobile Apps
Use FastCMS as your mobile backend with real-time sync, file storage, and push notifications.

### AI Applications
Build RAG systems, chatbots, content generators, or recommendation engines with built-in LangChain.

### Internal Tools
Create admin panels, dashboards, and CRUD apps with auto-generated APIs and beautiful UI.

### E-commerce
Product catalogs, user reviews, recommendations, and order management with AI-powered search.

### Content Management
Blogs, documentation, knowledge bases with AI content generation and semantic search.

---

## 🏆 Tech Stack

**Core Framework**
- **FastAPI 0.115** - High-performance async web framework
- **Python 3.11+** - Modern Python with type hints
- **Uvicorn** - Lightning-fast ASGI server
- **Pydantic v2** - Data validation and serialization

**Database & ORM**
- **SQLAlchemy 2.0** - Async ORM with type safety
- **SQLite** - Default database with WAL mode
- **Alembic** - Database migrations and version control
- **PostgreSQL** - *Coming Soon* - Production database
- **MySQL** - *Coming Soon* - Alternative database

**Authentication & Security**
- **python-jose** - JWT token handling
- **Passlib + bcrypt** - Password hashing
- **Authlib** - OAuth2 client
- **itsdangerous** - Secure token generation

**AI & Machine Learning**
- **LangChain 0.3.7** - AI orchestration framework
- **LangGraph 0.2.45** - AI workflow engine
- **OpenAI** - GPT-4 integration
- **Anthropic** - Claude integration
- **Ollama** - Local LLM support
- **FAISS** - Vector similarity search
- **Qdrant** - Vector database
- **Sentence Transformers** - Text embeddings

**Performance & Caching**
- **orjson** - Fast JSON serialization (2-3x faster)
- **Redis** - *Coming Soon* - Caching and pub/sub
- **Celery** - *Coming Soon* - Background jobs

**Observability**
- **Structlog** - *Coming Soon* - Structured logging
- **Prometheus** - *Coming Soon* - Metrics
- **Sentry** - *Coming Soon* - Error tracking

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

Query records using powerful filter syntax:

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

### OAuth2 Social Authentication

FastCMS supports OAuth2 authentication with Google, GitHub, and Microsoft. Users can sign in with their existing accounts, and FastCMS automatically links OAuth accounts to users by email.

#### Configuration

Add OAuth provider credentials to your `.env` file:

```bash
# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# GitHub OAuth
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# Microsoft OAuth
MICROSOFT_CLIENT_ID=your_microsoft_client_id
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret
```

#### Setup OAuth Apps

**Google:**

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://localhost:8000/api/v1/oauth/callback/google`

**GitHub:**

1. Go to Settings > Developer settings > OAuth Apps
2. Create new OAuth App
3. Set callback URL: `http://localhost:8000/api/v1/oauth/callback/github`

**Microsoft:**

1. Go to [Azure Portal](https://portal.azure.com)
2. Register a new application
3. Add redirect URI: `http://localhost:8000/api/v1/oauth/callback/microsoft`

#### Usage

Users can authenticate by visiting the OAuth login endpoints in their browser:

```
http://localhost:8000/api/v1/oauth/login/google
http://localhost:8000/api/v1/oauth/login/github
http://localhost:8000/api/v1/oauth/login/microsoft
```

The OAuth flow will redirect to the provider, then back to your callback URL with tokens.

#### Manage OAuth Accounts

```bash
# List linked OAuth accounts
curl -X GET "http://localhost:8000/api/v1/oauth/accounts" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Unlink OAuth provider
curl -X DELETE "http://localhost:8000/api/v1/oauth/accounts/google" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Features

- Automatic user creation on first OAuth login
- Link multiple OAuth providers to one account
- Auto-link OAuth accounts by verified email
- Secure token storage and refresh
- Prevents unlinking the only authentication method
- Users created via OAuth are marked as verified

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
- OAuth2 social authentication (Google, GitHub, Microsoft)
- Password hashing with bcrypt
- Email verification for new accounts
- Secure password reset with time-limited tokens
- Role-based access control (user, admin)
- Fine-grained permission rules per collection
- Webhook signature verification with HMAC
- Session middleware for OAuth state management
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

## 🗺️ Roadmap

FastCMS is actively developed with **175+ features planned**. See [ROADMAP.md](ROADMAP.md) for the complete roadmap.

### ✅ Completed (v0.1.0 - January 2025)

**Core Backend**
- ✅ Dynamic schema/collections
- ✅ Auto-generated REST APIs
- ✅ Advanced filtering & querying
- ✅ Relation expansion
- ✅ File upload/download
- ✅ Real-time updates (SSE)
- ✅ Webhooks with HMAC
- ✅ Admin dashboard

**Authentication**
- ✅ Email/password auth
- ✅ JWT tokens
- ✅ OAuth2 (3 providers)
- ✅ Email verification
- ✅ Password reset
- ✅ RBAC

**AI Features (Industry First!)**
- ✅ LangChain integration
- ✅ Semantic search
- ✅ Natural language queries
- ✅ AI content generation
- ✅ AI chat assistant
- ✅ Vector embeddings

### 🚧 In Progress (Q1 2025)

**Phase 1: Production Foundation**
- 🔨 PostgreSQL support
- 🔨 S3-compatible storage
- 🔨 Database backups
- 🔨 Multi-factor auth (MFA)
- 🔨 Audit logging
- 🔨 CLI tool
- 🔨 GraphQL API
- 🔨 Background jobs
- 🔨 Error tracking

### 🔮 Coming Soon (Q2 2025)

**Phase 2: AI Domination**
- 🤖 LangGraph workflows
- 🤖 AI agents system
- 🤖 RAG pipelines
- 🤖 Multimodal AI
- 🤖 AI model marketplace
- 🤖 Human-in-the-loop
- 🤖 Fine-tuning interface

**See [ROADMAP.md](ROADMAP.md) for the complete feature list and timeline.**

---

## 📊 Comparison

| Feature | FastCMS | Supabase | Appwrite | Firebase | Strapi |
|---------|---------|----------|----------|----------|--------|
| **Open Source** | ✅ MIT | ✅ Apache 2.0 | ✅ BSD | ❌ Proprietary | ✅ MIT |
| **Self-Hosted** | ✅ | ✅ | ✅ | ❌ | ✅ |
| **Built-in AI** | ✅ LangChain | ❌ | ❌ | 🟡 Vertex AI | ❌ |
| **Natural Language Queries** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Semantic Search** | ✅ | 🟡 pgvector | ❌ | 🟡 Firestore | ❌ |
| **Dynamic Schema** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **GraphQL** | 🔨 Q1 2025 | ✅ | ❌ | ❌ | ✅ |
| **Real-time** | ✅ SSE | ✅ WebSocket | ✅ WebSocket | ✅ | ❌ |
| **Language** | 🐍 Python | TypeScript | Dart/Node | Multi | JavaScript |
| **Database** | SQLite/PostgreSQL | PostgreSQL | NoSQL | NoSQL/Firestore | Multi-DB |
| **Pricing** | Free | Free + Paid | Free + Paid | Pay-as-you-go | Free + Paid |

**See [BAAS_COMPARISON.md](BAAS_COMPARISON.md) for detailed feature comparison.**

## 🤝 Contributing

We welcome contributions of all kinds! FastCMS is built by the community, for the community.

### How to Contribute

1. **⭐ Star the repo** - Show your support!
2. **🐛 Report bugs** - Open an issue with reproduction steps
3. **💡 Suggest features** - Share your ideas in Discussions
4. **🔧 Submit PRs** - Fix bugs or add features
5. **📖 Improve docs** - Help others get started
6. **✍️ Write tutorials** - Blog posts, videos, guides
7. **💬 Help others** - Answer questions in Discord

### Development Setup

```bash
# Fork and clone the repo
git clone https://github.com/YOUR_USERNAME/fastCMS.git
cd fastCMS

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -e ".[dev]"

# Setup environment
cp .env.example .env

# Run tests
pytest

# Start development server
python app/main.py
```

### Contribution Guidelines

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guide
- Use [Black](https://github.com/psf/black) for code formatting
- Add type hints to all functions
- Write tests for new features
- Update documentation
- Keep PRs focused and atomic

### First-Time Contributors

Look for issues labeled `good first issue` or `help wanted`. We're here to help you get started!

---

## 🌟 Stargazers

[![Stargazers over time](https://starchart.cc/aalhommada/fastCMS.svg)](https://starchart.cc/aalhommada/fastCMS)

---

## 📣 Community

- **GitHub Discussions** - Ask questions, share ideas
- **Discord** - *Coming Soon* - Real-time chat
- **Twitter/X** - *Coming Soon* - Follow for updates
- **Blog** - *Coming Soon* - Tutorials and announcements

---

## 🎉 Sponsors

FastCMS is free and open-source. Consider sponsoring to support development!

- **[GitHub Sponsors](https://github.com/sponsors/)** - *Coming Soon*
- **[Open Collective](https://opencollective.com/)** - *Coming Soon*

---

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for release notes and version history.

---

## 🙏 Acknowledgments

FastCMS is inspired by amazing projects:
- **FastAPI** - For the incredible web framework
- **LangChain** - For democratizing AI development
- **Supabase** - For showing what open-source BaaS can be
- **Strapi** - For the headless CMS vision

Built with ❤️ by developers, for developers.

---

## 📄 License

FastCMS is [MIT licensed](LICENSE). Build anything, anywhere, forever.
