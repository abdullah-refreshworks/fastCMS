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

## Best Practices

### Security

1. Always use strong SECRET_KEY in production
2. Use HTTPS in production
3. Set appropriate access control rules on collections
4. Validate user input on the client side
5. Use refresh tokens for long-lived sessions

### Performance

1. Add indexes to frequently queried fields
2. Use pagination for large datasets
3. Set appropriate cache TTL for view collections
4. Use view collections for complex queries instead of client-side joins

### Data Modeling

1. Use auth collections for any user type requiring authentication
2. Use base collections for standard data
3. Use view collections for reports and aggregations
4. Use relation fields to link collections
5. Set cascade_delete appropriately on relations

## Troubleshooting

### Collection Creation Fails

**Issue:** "An invalid form control with name='' is not focusable"

**Solution:** This occurs when hidden required fields (relation/view fields) are present. Ensure you're creating the correct collection type and all visible required fields are filled.

### Authentication Fails

**Issue:** 401 Unauthorized

**Solution:**
- Ensure access token is included in Authorization header
- Check if token has expired (access tokens expire in 15 minutes by default)
- Use refresh token to get a new access token

### Access Denied to Records

**Issue:** Cannot view/edit records despite being authenticated

**Solution:**
- Check the access control rules on the collection
- Ensure your user meets the rule criteria
- Verify the record data matches the rules (e.g., user_id field)

## Next Steps

- [Learn about Collections](collections.md)
- [Set up Authentication](authentication.md)
- [Explore the API](api-reference.md)
