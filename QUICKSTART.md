# FastCMS - Quick Start Guide

Get your backend running in 5 minutes.

---

## Prerequisites

- Python 3.11+
- SQLite (included with Python)

---

## Installation

```bash
# 1. Clone & enter directory
git clone https://github.com/aalhommada/fastCMS.git
cd fastCMS

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# On Mac/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Setup environment
cp .env.example .env

# 6. Generate secret key
openssl rand -hex 32

# 7. Edit .env and paste your secret key into SECRET_KEY=
```

---

## First Run

```bash
# Start the server (choose one method)

# Method 1: Run as a module (recommended)
python -m app.main

# Method 2: Use uvicorn directly (best for development)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Method 3: If you get "ModuleNotFoundError: No module named 'app'"
export PYTHONPATH=$PWD:$PYTHONPATH
python app/main.py
```

The server starts at **http://localhost:8000**

---

## Initial Setup

### Via Browser (Recommended)

1. Open http://localhost:8000/setup
2. Fill in admin details:
   - Name: Your Name
   - Email: admin@example.com
   - Password: SecurePass123!
3. Click "Create Admin Account"
4. You're logged in! 🎉

### Via API

```bash
curl -X POST http://localhost:8000/api/v1/setup/setup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "name": "Admin User"
  }'
```

---

## Your First Collection

### Via Admin UI

1. Go to http://localhost:8000/admin/
2. Click "Collections"
3. Click "Create Collection"
4. Fill in:
   - Name: posts
   - Type: base
   - Add fields:
     - title (text, required)
     - content (editor)
     - published (bool)
5. Click "Create"

### Via API

```bash
# 1. Login to get token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"SecurePass123!"}' \
  | jq -r '.access_token')

# 2. Create collection
curl -X POST http://localhost:8000/api/v1/collections \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "posts",
    "type": "base",
    "schema": [
      {"name": "title", "type": "text", "validation": {"required": true}},
      {"name": "content", "type": "editor"},
      {"name": "published", "type": "bool"}
    ]
  }'
```

---

## Add Your First Record

```bash
curl -X POST http://localhost:8000/api/v1/posts/records \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "title": "My First Post",
      "content": "<p>Hello FastCMS!</p>",
      "published": true
    }
  }'
```

---

## Query Records

```bash
# Get all posts
curl http://localhost:8000/api/v1/posts/records

# Get published posts only
curl "http://localhost:8000/api/v1/posts/records?filter=published=true"

# Search by title
curl "http://localhost:8000/api/v1/posts/records?filter=title~First"

# Sort by newest
curl "http://localhost:8000/api/v1/posts/records?sort=-created"
```

---

## Upload a File

```bash
curl -X POST http://localhost:8000/api/v1/files/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@image.jpg"
```

**Bonus:** Thumbnails are automatically generated! 🎨

---

## Create a Backup

```bash
curl -X POST http://localhost:8000/api/v1/backups \
  -H "Authorization: Bearer $TOKEN"
```

---

## Useful URLs

- **Admin Dashboard:** http://localhost:8000/admin/
- **API Docs (Swagger):** http://localhost:8000/docs
- **API Docs (ReDoc):** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

---

## Next Steps

### Enable Social Login

Add to `.env`:
```bash
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

Users can now login at: http://localhost:8000/api/v1/oauth/login/google

### Enable AI Features

```bash
# Install AI dependencies
pip install langchain langchain-openai langchain-anthropic faiss-cpu sentence-transformers

# Add to .env
AI_ENABLED=true
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
```

Now use natural language queries:
```bash
curl -X POST http://localhost:8000/api/v1/ai/query/natural-language \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "Find all published posts", "collection_name": "posts"}'
```

### Production Deployment

```bash
# Install production server
pip install gunicorn

# Run with gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## Common Tasks

### Create Admin User Manually

```bash
# Login to database
sqlite3 data/app.db

# Update user role
UPDATE users SET role = 'admin' WHERE email = 'user@example.com';
```

### Reset Database

```bash
# Delete database and files
rm -rf data/app.db data/files/

# Restart server - will create fresh database
python app/main.py
```

### Export Collection

```bash
curl http://localhost:8000/api/v1/collections/{id}/export?include_data=true \
  -H "Authorization: Bearer $TOKEN" \
  > collection_backup.json
```

### Import Collection

```bash
curl -X POST http://localhost:8000/api/v1/collections/import \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @collection_backup.json
```

---

## Troubleshooting

### Can't access /setup
Check if users already exist:
```bash
sqlite3 data/app.db "SELECT COUNT(*) FROM users;"
```
If > 0, use /admin/login instead.

### Database locked error
- Stop all servers accessing the database
- Ensure WAL mode is enabled (it is by default)

### Import fails
- Check JSON format matches export format
- Ensure no collection with same name exists
- Check error messages in response

---

## Getting Help

- **Documentation:** Check README.md and FEATURES.md
- **API Reference:** http://localhost:8000/docs
- **Comparison:** Read POCKETBASE_COMPARISON.md
- **Code:** All code is documented with docstrings

---

## Summary

You now have:
- ✅ Running backend server
- ✅ Admin dashboard access
- ✅ First collection created
- ✅ First record added
- ✅ API basics learned

**You're ready to build!** 🚀

---

**FastCMS - Your backend, simplified.**
