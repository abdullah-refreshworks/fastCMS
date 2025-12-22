# Rate Limiting

FastCMS includes a sophisticated rate limiting system that protects against abuse while providing fair access to all users.

## Overview

The rate limiting middleware provides:
- **Per-user rate limiting**: Authenticated users tracked by user ID
- **Per-IP rate limiting**: Anonymous users tracked by IP address
- **Role-based limits**: Different limits for admin, user, and anonymous
- **Endpoint-specific limits**: Stricter limits for sensitive endpoints
- **Audit logging**: Rate limit violations logged for security monitoring

## Default Limits

### By User Type

| User Type | Requests/Minute | Requests/Hour |
|-----------|-----------------|---------------|
| Anonymous (by IP) | 60 | 500 |
| Authenticated User | 100 | 1,000 |
| Admin User | 300 | 5,000 |

### By Endpoint

| Endpoint | Requests/Minute | Requests/Hour |
|----------|-----------------|---------------|
| `/api/v1/auth/login` | 10 | 50 |
| `/api/v1/auth/register` | 5 | 20 |
| `/api/v1/auth/forgot-password` | 3 | 10 |

## Response Headers

Every API response includes rate limit headers:

```http
X-RateLimit-Limit-Minute: 100
X-RateLimit-Limit-Hour: 1000
X-RateLimit-Remaining-Minute: 95
X-RateLimit-Remaining-Hour: 980
```

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit-Minute` | Maximum requests allowed per minute |
| `X-RateLimit-Limit-Hour` | Maximum requests allowed per hour |
| `X-RateLimit-Remaining-Minute` | Requests remaining in current minute window |
| `X-RateLimit-Remaining-Hour` | Requests remaining in current hour window |

## Rate Limit Exceeded Response

When rate limit is exceeded, the API returns:

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
Retry-After: 60
X-RateLimit-Limit-Minute: 100
X-RateLimit-Remaining-Minute: 0
```

```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please slow down.",
  "details": {
    "limit_per_minute": 100,
    "limit_per_hour": 1000,
    "retry_after_seconds": 60
  }
}
```

## How It Works

### Key Generation

Rate limits are tracked using a key that identifies the client:

1. **Authenticated Users (JWT)**
   - Key: `user:{user_id}`
   - Applies user's role-based limits

2. **API Key Users**
   - Key: `apikey:{hash}`
   - Applies "user" role limits

3. **Anonymous Users**
   - Key: `ip:{client_ip}`
   - Applies "anonymous" limits

### Sliding Window

Rate limits use a sliding window algorithm:
- **Minute window**: Resets 60 seconds after first request
- **Hour window**: Resets 3600 seconds after first request

## Configuration

Rate limiting can be configured via environment variables:

```bash
# Enable/disable rate limiting
RATE_LIMIT_ENABLED=true

# Default limits (used as fallback)
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=1000
```

### Customizing Limits

In `app/core/rate_limit.py`:

```python
# Modify default limits by role
DEFAULT_LIMITS = {
    "anonymous": RateLimitConfig(requests_per_minute=60, requests_per_hour=500),
    "user": RateLimitConfig(requests_per_minute=100, requests_per_hour=1000),
    "admin": RateLimitConfig(requests_per_minute=300, requests_per_hour=5000),
}

# Add endpoint-specific limits
ENDPOINT_LIMITS = {
    "/api/v1/auth/login": RateLimitConfig(requests_per_minute=10, requests_per_hour=50),
    "/api/v1/auth/register": RateLimitConfig(requests_per_minute=5, requests_per_hour=20),
    "/api/v1/auth/forgot-password": RateLimitConfig(requests_per_minute=3, requests_per_hour=10),
    # Add pattern matching with wildcard
    "/api/v1/admin/*": RateLimitConfig(requests_per_minute=50, requests_per_hour=500),
}
```

### Middleware Configuration

```python
from app.core.rate_limit import RateLimitMiddleware, RateLimitConfig

app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=100,
    requests_per_hour=1000,
    limits_by_role={
        "anonymous": RateLimitConfig(60, 500),
        "user": RateLimitConfig(100, 1000),
        "admin": RateLimitConfig(300, 5000),
    },
    endpoint_limits={
        "/api/v1/auth/login": RateLimitConfig(10, 50),
    },
)
```

## Skipped Paths

The following paths are excluded from rate limiting:

- `/health` - Health check endpoint
- `/docs` - API documentation
- `/redoc` - ReDoc documentation
- `/openapi.json` - OpenAPI specification
- `/static/*` - Static files
- `/favicon.ico` - Favicon

## Security Integration

Rate limit violations are logged to the audit system:

```python
{
    "event_type": "security",
    "event_action": "rate_limit",
    "description": "Rate limit exceeded on /api/v1/auth/login",
    "severity": "warning",
    "details": {
        "endpoint": "/api/v1/auth/login",
        "identifier_type": "ip",
        "limit_minute": 10,
        "limit_hour": 50
    }
}
```

### Monitoring

Query rate limit violations:

```http
GET /api/v1/audit?event_type=security&event_action=rate_limit
Authorization: Bearer {admin_token}
```

## Client Handling

### Best Practices

1. **Check remaining headers**: Monitor `X-RateLimit-Remaining-*` headers
2. **Implement backoff**: When approaching limits, slow down requests
3. **Use Retry-After**: When rate limited, wait the specified time
4. **Cache responses**: Reduce unnecessary API calls

### Example: JavaScript Client

```javascript
async function fetchWithRateLimit(url, options = {}) {
  const response = await fetch(url, options);

  // Check rate limit headers
  const remaining = response.headers.get('X-RateLimit-Remaining-Minute');

  if (remaining !== null && parseInt(remaining) < 10) {
    console.warn('Approaching rate limit, slowing down...');
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  if (response.status === 429) {
    const retryAfter = response.headers.get('Retry-After') || 60;
    console.log(`Rate limited. Retrying after ${retryAfter} seconds...`);
    await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
    return fetchWithRateLimit(url, options);
  }

  return response;
}
```

### Example: Python Client

```python
import time
import requests

def fetch_with_rate_limit(url, **kwargs):
    response = requests.get(url, **kwargs)

    # Check remaining requests
    remaining = response.headers.get('X-RateLimit-Remaining-Minute')
    if remaining and int(remaining) < 10:
        print("Approaching rate limit, slowing down...")
        time.sleep(1)

    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 60))
        print(f"Rate limited. Retrying after {retry_after} seconds...")
        time.sleep(retry_after)
        return fetch_with_rate_limit(url, **kwargs)

    return response
```

## Storage

Rate limit counters are stored in-memory by default. For production with multiple instances, consider:

1. **Redis Backend**: Use Redis for distributed rate limiting
2. **Load Balancer Limits**: Configure at the load balancer level
3. **API Gateway**: Use an API gateway with built-in rate limiting

### Memory Usage

The middleware automatically cleans up expired entries when storage exceeds 10,000 keys.

## Troubleshooting

### Rate Limits Not Working

1. Check if rate limiting is enabled:
   ```bash
   echo $RATE_LIMIT_ENABLED  # Should be "true"
   ```

2. Verify middleware is registered in `app/main.py`

3. Check if path is in skip list

### Inconsistent Limits

If using multiple application instances, rate limits won't be synchronized (in-memory storage). Consider:
- Using sticky sessions
- Implementing Redis backend
- Setting limits at load balancer level

### Debugging

Enable debug logging to see rate limit decisions:

```python
import logging
logging.getLogger('app.core.rate_limit').setLevel(logging.DEBUG)
```
