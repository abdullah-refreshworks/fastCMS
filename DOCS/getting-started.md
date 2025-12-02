# Getting Started

## Installation

```bash
# Install dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Access the Admin Dashboard

Navigate to `http://localhost:8000/admin` in your browser. On first run, you will be prompted to create an admin account.

## Environment Variables

Create a `.env` file in the project root:

```env
# Application
ENV=development
DEBUG=true

# Database
DATABASE_URL=sqlite:///./data/app.db

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

## Database

FastCMS uses SQLite with WAL (Write-Ahead Logging) mode for better concurrency.

**Database Location:** `data/app.db`

**Important Notes:**
- All collections are stored as dynamic tables
- The `collections` table stores metadata and schemas
- The `users` table is for admin authentication only
- Auth collections create their own tables with authentication fields

## Interactive API Documentation

FastCMS provides interactive API documentation powered by Swagger UI.

Access it at: `http://localhost:8000/docs`

This interface allows you to:
- Browse all available endpoints
- Test API calls directly from the browser
- View request/response schemas
- Authenticate and test protected endpoints

## Next Steps

- [Learn about Collections](collections.md)
- [Set up Authentication](authentication.md)
- [Explore the API](api-reference.md)
