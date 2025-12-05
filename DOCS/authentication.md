# Authentication System

FastCMS provides a comprehensive authentication system with configurable settings, multiple auth methods, and support for custom user collections.

## Authentication Methods

FastCMS supports multiple authentication methods that can be enabled/disabled via settings:

| Method | Setting | Description |
|--------|---------|-------------|
| Password | `password_auth_enabled` | Traditional email/password login |
| OAuth2 | `oauth_enabled` | Social login (Google, GitHub, etc.) |
| OTP | `otp_enabled` | Email code authentication |
| MFA | `mfa_enabled` | Multi-factor authentication |

## Configuring Authentication

### Via Admin UI

Navigate to **Admin > Settings > Authentication** to configure:

- **Authentication Methods**: Enable/disable password, OAuth, OTP, MFA
- **OAuth Behavior**: Auto-create users, link by email
- **Password Requirements**: Minimum length, complexity rules
- **Token Settings**: Access token and refresh token expiry

### Via API

```bash
POST /api/v1/settings
Authorization: Bearer ADMIN_TOKEN
Content-Type: application/json

{
  "key": "password_auth_enabled",
  "value": true,
  "category": "auth"
}
```

## Authentication Settings Reference

### Auth Methods

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `password_auth_enabled` | boolean | `true` | Enable password authentication |
| `oauth_enabled` | boolean | `true` | Enable OAuth2 authentication |
| `otp_enabled` | boolean | `false` | Enable OTP (email code) authentication |
| `mfa_enabled` | boolean | `false` | Enable Multi-Factor Authentication |

### OAuth Behavior

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `oauth_auto_create_user` | boolean | `true` | Auto-create user on first OAuth login |
| `oauth_link_by_email` | boolean | `true` | Link OAuth to existing user by email |
| `verification_required` | boolean | `false` | Require email verification |

### Password Requirements

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `password_min_length` | integer | `8` | Minimum password length |
| `password_require_upper` | boolean | `false` | Require uppercase letter |
| `password_require_number` | boolean | `false` | Require number |
| `password_require_special` | boolean | `false` | Require special character |

### Token Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `token_expiry_hours` | integer | `24` | Access token expiry (hours) |
| `refresh_token_expiry_days` | integer | `7` | Refresh token expiry (days) |

## 1. Built-in Admin Authentication

The `users` table is for admin dashboard access only.

**Roles:**
- `admin` - Full access to admin dashboard and all collections
- `user` - Limited access (typically not used)

**Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/login` | POST | Admin login |
| `/api/v1/auth/register` | POST | Create admin users (requires admin token) |
| `/api/v1/auth/refresh` | POST | Refresh access token |
| `/api/v1/auth/me` | GET | Get current user info |
| `/api/v1/auth/logout` | POST | Logout (invalidate tokens) |

**Login Example:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "your-password"
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
    "email": "admin@example.com",
    "role": "admin",
    "verified": true
  }
}
```

## 2. Auth Collections (Custom User Systems)

Create auth collections for your own user systems (customers, vendors, etc.).

### Creating an Auth Collection

Via Admin UI:
1. Go to **Admin > Collections**
2. Click **"Create Collection"**
3. Set **Type** to **"Auth"**
4. Name it (e.g., "customers")

Via API:
```bash
curl -X POST http://localhost:8000/api/v1/collections \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "name": "customers",
    "type": "auth",
    "schema": {
      "fields": [
        {"name": "company", "type": "text"},
        {"name": "phone", "type": "text"}
      ]
    }
  }'
```

### Auth Collection Endpoints

For a collection named `customers`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/collections/customers/auth/register` | POST | Customer registration |
| `/api/v1/collections/customers/auth/login` | POST | Customer login |
| `/api/v1/collections/customers/auth/refresh` | POST | Refresh token |
| `/api/v1/collections/customers/auth/me` | GET | Get current customer |

**Registration Example:**
```bash
curl -X POST http://localhost:8000/api/v1/collections/customers/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "customer@example.com",
    "password": "securepassword123",
    "company": "Acme Inc",
    "phone": "+1234567890"
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
    "company": "Acme Inc",
    "phone": "+1234567890"
  }
}
```

## Using Authentication Headers

Include the access token in the Authorization header for protected endpoints:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**JavaScript Example:**
```javascript
const response = await fetch('/api/v1/records/products', {
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  }
});
```

## Token Refresh

When the access token expires, use the refresh token to get a new one:

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGc..."
  }'
```

**Response:**
```json
{
  "access_token": "new-access-token...",
  "refresh_token": "new-refresh-token...",
  "token_type": "bearer"
}
```

## Password Validation

Passwords are validated against the configured requirements:

```python
# Example validation errors
{
  "error": "Validation failed",
  "details": {
    "password": "Password must be at least 8 characters",
    "password": "Password must contain an uppercase letter",
    "password": "Password must contain a number"
  }
}
```

## Security Best Practices

1. **Use HTTPS**: Always use HTTPS in production
2. **Token Storage**: Store tokens securely (httpOnly cookies recommended)
3. **Token Expiry**: Use short access token expiry with refresh tokens
4. **Password Requirements**: Enable complexity requirements for production
5. **Rate Limiting**: Enable rate limiting to prevent brute force attacks

## Next Steps

- [Email Verification & Password Reset](email-verification.md)
- [OAuth Authentication](oauth.md)
- [Access Control Rules](access-control.md)
