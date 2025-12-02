# Authentication System

FastCMS has two authentication systems:

## 1. Built-in Admin Authentication

The `users` table is for admin dashboard access only.

**Roles:**
- `admin` - Full access to admin dashboard and all collections
- `user` - Limited access (typically not used)

**Endpoints:**
- `POST /api/v1/auth/login` - Admin login
- `POST /api/v1/auth/register` - Create admin users (requires admin token)
- `POST /api/v1/auth/refresh` - Refresh admin access token

## 2. Auth Collections (Custom User Systems)

Create auth collections for your own user systems (customers, vendors, etc.).

**Example: Customer Authentication**

1. Create "customers" auth collection
2. Customers can register at: `POST /api/v1/collections/customers/auth/register`
3. Customers can login at: `POST /api/v1/collections/customers/auth/login`

**Registration Example:**

```bash
curl -X POST http://localhost:8000/api/v1/collections/customers/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "customer@example.com",
    "password": "securepassword123"
  }'
```

**Login Example:**

```bash
curl -X POST http://localhost:8000/api/v1/collections/customers/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "customer@example.com",
    "password": "securepassword123"
  }'
```

**Response:**

```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "customer@example.com",
    "verified": false,
    "role": "user"
  }
}
```

## Authentication Headers

Include the access token in the Authorization header for protected endpoints:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Next Steps

- [Email Verification & Password Reset](email-verification.md)
- [OAuth Authentication](oauth.md)
- [Access Control Rules](access-control.md)
