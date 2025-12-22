# API Keys

API Keys provide secure, long-lived authentication tokens for service-to-service communication, CI/CD pipelines, external integrations, and programmatic API access.

## Overview

API Keys are an alternative to JWT tokens, designed for:
- **Service-to-service authentication**: Backend services communicating with FastCMS
- **CI/CD pipelines**: Automated deployments and content updates
- **External integrations**: Third-party tools and services
- **Mobile apps**: Long-lived tokens without session management

### Key Features

- **Secure key generation**: Cryptographically secure random keys
- **One-time display**: Full key shown only at creation time
- **SHA-256 hashing**: Keys are hashed before storage
- **Usage tracking**: Last used timestamp and IP address
- **Scope control**: Fine-grained permission control
- **Expiration support**: Optional key expiration
- **Instant revocation**: Disable keys immediately

## Key Format

API keys follow this format:
```
fcms_{prefix}_{secret}
```

- `fcms_` - Identifier prefix
- `{prefix}` - 8-character hex identifier (visible in UI)
- `{secret}` - 32-character hex secret

Example: `fcms_a1b2c3d4_e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0`

## API Endpoints

All endpoints require authentication (JWT or existing API key).

### Create API Key

```http
POST /api/v1/api-keys
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "name": "CI/CD Pipeline Key",
  "scopes": "collections:read,records:*",
  "expires_at": "2025-12-31T23:59:59Z"
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "CI/CD Pipeline Key",
  "key": "fcms_a1b2c3d4_e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
  "key_prefix": "fcms_a1b2c3d4_****",
  "scopes": "collections:read,records:*",
  "expires_at": "2025-12-31T23:59:59",
  "created": "2025-01-15T10:30:00",
  "message": "Save this key securely. It will not be shown again."
}
```

**Important:** Save the `key` value immediately. It will never be shown again.

### List API Keys

```http
GET /api/v1/api-keys
Authorization: Bearer {jwt_token}
```

**Response (200 OK):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "CI/CD Pipeline Key",
    "key_prefix": "fcms_a1b2c3d4_****",
    "scopes": "collections:read,records:*",
    "active": true,
    "expires_at": "2025-12-31T23:59:59",
    "last_used_at": "2025-01-15T12:00:00",
    "last_used_ip": "192.168.1.100",
    "created": "2025-01-15T10:30:00"
  }
]
```

### Get API Key

```http
GET /api/v1/api-keys/{key_id}
Authorization: Bearer {jwt_token}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "CI/CD Pipeline Key",
  "key_prefix": "fcms_a1b2c3d4_****",
  "scopes": "collections:read,records:*",
  "active": true,
  "expires_at": "2025-12-31T23:59:59",
  "last_used_at": "2025-01-15T12:00:00",
  "last_used_ip": "192.168.1.100",
  "created": "2025-01-15T10:30:00"
}
```

### Update API Key

```http
PATCH /api/v1/api-keys/{key_id}
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "name": "Updated Key Name",
  "scopes": "*",
  "active": false,
  "expires_at": "2026-01-01T00:00:00Z"
}
```

All fields are optional. Only provided fields are updated.

### Delete API Key

```http
DELETE /api/v1/api-keys/{key_id}
Authorization: Bearer {jwt_token}
```

**Response (204 No Content)**

### Revoke All API Keys

Disable all API keys for the authenticated user:

```http
POST /api/v1/api-keys/revoke-all
Authorization: Bearer {jwt_token}
```

**Response (200 OK):**
```json
{
  "revoked": 3,
  "message": "Revoked 3 API keys"
}
```

## Using API Keys for Authentication

Include your API key in the `X-API-Key` header:

```http
GET /api/v1/collections
X-API-Key: fcms_a1b2c3d4_e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0
```

### Example: cURL

```bash
curl -H "X-API-Key: fcms_a1b2c3d4_..." \
  https://your-fastcms.com/api/v1/collections
```

### Example: JavaScript

```javascript
const response = await fetch('https://your-fastcms.com/api/v1/collections', {
  headers: {
    'X-API-Key': 'fcms_a1b2c3d4_...'
  }
});
```

### Example: Python

```python
import requests

response = requests.get(
    'https://your-fastcms.com/api/v1/collections',
    headers={'X-API-Key': 'fcms_a1b2c3d4_...'}
)
```

## Scopes

Scopes control what an API key can access. Use comma-separated values:

| Scope | Description |
|-------|-------------|
| `*` | Full access (default) |
| `collections:read` | Read collection schemas |
| `collections:write` | Create/update collections |
| `records:read` | Read records |
| `records:write` | Create/update records |
| `records:delete` | Delete records |
| `records:*` | All record operations |
| `files:read` | Read files |
| `files:write` | Upload files |
| `files:*` | All file operations |

**Note:** Scope enforcement is available for custom implementation. By default, scopes are stored but not enforced at the endpoint level.

## Security Best Practices

### Key Management

1. **Never commit keys to source control**
   - Use environment variables
   - Use secret management services

2. **Use descriptive names**
   - Include purpose: "GitHub Actions Deploy"
   - Include environment: "Production Sync Service"

3. **Set expiration dates**
   - Rotate keys regularly
   - Use short-lived keys for CI/CD

4. **Limit scopes**
   - Follow principle of least privilege
   - Only grant necessary permissions

### Key Rotation

Implement regular key rotation:

```python
# 1. Create new key
new_key = create_api_key(name="Production Key v2", scopes="*")

# 2. Update services with new key
# ... deployment process ...

# 3. Verify new key works
# ... testing ...

# 4. Delete old key
delete_api_key(old_key_id)
```

### Monitoring

Monitor API key usage:
- Check `last_used_at` for inactive keys
- Review `last_used_ip` for unexpected access
- Audit key creation and deletion

## Error Responses

### Invalid API Key

```json
{
  "error": "Authentication required",
  "message": "Authentication required",
  "details": {}
}
```

### Expired API Key

```json
{
  "error": "API key has expired",
  "message": "API key has expired",
  "details": {}
}
```

### Disabled API Key

```json
{
  "error": "API key is disabled",
  "message": "API key is disabled",
  "details": {}
}
```

### Key Not Found

```json
{
  "error": "API key not found",
  "message": "API key not found",
  "details": {}
}
```

## Database Schema

API keys are stored in the `api_keys` table:

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `name` | String(255) | Human-readable name |
| `key_prefix` | String(8) | First 8 chars for identification |
| `key_hash` | String(64) | SHA-256 hash of full key |
| `user_id` | UUID | Owner user ID |
| `scopes` | Text | Comma-separated permissions |
| `active` | Boolean | Whether key is enabled |
| `expires_at` | DateTime | Optional expiration |
| `last_used_at` | DateTime | Last usage timestamp |
| `last_used_ip` | String(45) | Last usage IP address |
| `created` | DateTime | Creation timestamp |
| `updated` | DateTime | Last update timestamp |
