# Audit Logging

FastCMS includes a comprehensive audit logging system for tracking security-relevant events. This system provides visibility into authentication attempts, configuration changes, and security events.

## Overview

The audit log system tracks:
- **Authentication events**: Login, logout, failed attempts
- **2FA events**: Setup, enable, disable, verification
- **API Key events**: Create, update, delete, revoke
- **Security events**: Rate limiting, suspicious activity
- **Administrative actions**: Settings changes, backups

## Event Types

| Event Type | Description |
|------------|-------------|
| `auth` | Authentication-related events |
| `user` | User management events |
| `api_key` | API key operations |
| `two_factor` | 2FA/TOTP events |
| `collection` | Collection operations |
| `record` | Record operations |
| `file` | File operations |
| `admin` | Administrative actions |
| `system` | System events |
| `security` | Security-related events |

## Event Actions

### Authentication Actions
| Action | Description |
|--------|-------------|
| `login` | Successful login |
| `logout` | User logout |
| `login_failed` | Failed login attempt |
| `token_refresh` | Token refresh |
| `password_change` | Password changed |
| `password_reset` | Password reset |

### 2FA Actions
| Action | Description |
|--------|-------------|
| `setup` | 2FA setup initiated |
| `enable` | 2FA enabled |
| `disable` | 2FA disabled |
| `verify` | 2FA verification |
| `backup_codes_regen` | Backup codes regenerated |
| `backup_code_used` | Backup code used |

### API Key Actions
| Action | Description |
|--------|-------------|
| `create` | API key created |
| `update` | API key updated |
| `delete` | API key deleted |
| `revoke` | API key revoked |
| `revoke_all` | All API keys revoked |

## Severity Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| `info` | Normal operations | Successful logins, standard actions |
| `warning` | Notable events | Failed logins, configuration changes |
| `critical` | Security concerns | Suspicious activity, access denied |

## API Endpoints

All audit endpoints require admin authentication.

### List Audit Logs

```http
GET /api/v1/audit
Authorization: Bearer {admin_token}
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | int | Max results (1-1000, default: 100) |
| `offset` | int | Skip results (default: 0) |
| `event_type` | string | Filter by event type |
| `event_action` | string | Filter by action |
| `user_id` | string | Filter by user ID |
| `severity` | string | Filter by severity |
| `outcome` | string | Filter by outcome |
| `from_date` | datetime | Filter from date |
| `to_date` | datetime | Filter to date |
| `ip_address` | string | Filter by IP |

**Response:**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "event_type": "auth",
      "event_action": "login",
      "severity": "info",
      "user_id": "user-123",
      "user_email": "user@example.com",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "resource_type": null,
      "resource_id": null,
      "description": "User logged in via password",
      "details": "{\"method\": \"password\"}",
      "outcome": "success",
      "error_message": null,
      "created": "2025-01-15T10:30:00"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

### Get Security Events

```http
GET /api/v1/audit/security
Authorization: Bearer {admin_token}
```

**Query Parameters:**
- `severity`: Filter by severity (optional)
- `limit`: Max results (1-1000, default: 100)

### Get Failed Logins

```http
GET /api/v1/audit/failed-logins
Authorization: Bearer {admin_token}
```

**Query Parameters:**
- `ip_address`: Filter by IP address
- `from_date`: Filter from date
- `limit`: Max results (1-1000, default: 100)

### Get User Activity

```http
GET /api/v1/audit/user/{user_id}
Authorization: Bearer {admin_token}
```

**Query Parameters:**
- `limit`: Max results (1-500, default: 50)

### Get Audit Statistics

```http
GET /api/v1/audit/statistics
Authorization: Bearer {admin_token}
```

**Query Parameters:**
- `from_date`: Filter from date
- `to_date`: Filter to date

**Response:**
```json
{
  "by_event_type": {
    "auth": 150,
    "api_key": 25,
    "two_factor": 10
  },
  "by_severity": {
    "info": 160,
    "warning": 20,
    "critical": 5
  },
  "by_outcome": {
    "success": 175,
    "failure": 10
  },
  "total": 185
}
```

### Cleanup Old Logs

```http
DELETE /api/v1/audit/cleanup
Authorization: Bearer {admin_token}
```

**Query Parameters:**
- `retention_days`: Days to keep (7-365, default: 90)

**Response:**
```json
{
  "deleted": 150,
  "message": "Deleted 150 audit logs older than 90 days"
}
```

## Using the Audit Service

### Basic Usage

```python
from app.services.audit_service import (
    AuditService,
    EventType,
    EventAction,
    Severity,
    Outcome,
)

async def log_custom_event(db):
    service = AuditService(db)

    await service.log(
        event_type=EventType.ADMIN,
        event_action=EventAction.SETTINGS_CHANGE,
        description="System settings updated",
        user_id="admin-123",
        user_email="admin@example.com",
        ip_address="192.168.1.1",
        details={"setting": "rate_limit", "old": 100, "new": 200},
        severity=Severity.WARNING,
    )
```

### Convenience Methods

```python
# Log successful login
await service.log_login(
    user_id="user-123",
    user_email="user@example.com",
    ip_address="192.168.1.100",
    method="password",
)

# Log failed login
await service.log_login_failed(
    email="attacker@example.com",
    ip_address="10.0.0.1",
    reason="invalid_password",
)

# Log 2FA event
await service.log_2fa_event(
    action=EventAction.ENABLE,
    user_id="user-123",
    user_email="user@example.com",
    ip_address="192.168.1.100",
)

# Log API key event
await service.log_api_key_event(
    action=EventAction.CREATE,
    user_id="user-123",
    user_email="user@example.com",
    key_name="Production Key",
    ip_address="192.168.1.100",
)

# Log security event
await service.log_security_event(
    action=EventAction.SUSPICIOUS_ACTIVITY,
    description="Multiple failed logins from same IP",
    ip_address="10.0.0.1",
    details={"attempts": 10, "timeframe": "5 minutes"},
)
```

## Querying Audit Logs

### Get Recent Logs

```python
# Get last 100 logs
logs = await service.get_logs(limit=100)

# Get logs for specific user
user_logs = await service.get_user_activity(user_id="user-123")

# Get security events
security_logs = await service.get_security_events(severity="critical")

# Get failed logins
failed = await service.get_failed_logins(ip_address="10.0.0.1")
```

### Count Failed Logins

```python
from datetime import datetime, timedelta, timezone

# Count failed logins from IP in last hour
since = datetime.now(timezone.utc) - timedelta(hours=1)
count = await service.count_failed_logins(
    ip_address="10.0.0.1",
    since=since,
)

if count >= 5:
    # Block IP or trigger alert
    await service.log_security_event(
        action=EventAction.RATE_LIMIT,
        description=f"IP blocked after {count} failed logins",
        ip_address="10.0.0.1",
    )
```

## Database Schema

Audit logs are stored in the `audit_logs` table:

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `event_type` | String(50) | Event category |
| `event_action` | String(50) | Specific action |
| `severity` | String(20) | info/warning/critical |
| `user_id` | UUID | Acting user ID |
| `user_email` | String(255) | User email for display |
| `ip_address` | String(45) | Client IP |
| `user_agent` | String(512) | Client user agent |
| `resource_type` | String(50) | Affected resource type |
| `resource_id` | UUID | Affected resource ID |
| `description` | String(500) | Human-readable description |
| `details` | Text | JSON metadata |
| `outcome` | String(20) | success/failure/error |
| `error_message` | String(500) | Error details |
| `created` | DateTime | Event timestamp |
| `updated` | DateTime | Last update |

## Best Practices

### What to Log

**Always log:**
- Login attempts (success and failure)
- Password changes
- 2FA configuration changes
- API key operations
- Administrative actions
- Access to sensitive data
- Configuration changes

**Consider logging:**
- Bulk data operations
- Export operations
- Unusual access patterns

**Avoid logging:**
- Sensitive data content (passwords, tokens)
- High-frequency read operations
- Internal system calls

### Retention

- Default retention: 90 days
- Minimum recommended: 30 days
- For compliance: Check requirements (GDPR, SOC2, etc.)

### Monitoring

Set up alerts for:
- Multiple failed logins from same IP
- Failed logins to admin accounts
- 2FA disabled on admin accounts
- API key revocations
- Critical severity events

## Integration Example

### In Auth Service

```python
async def login(self, data: UserLogin, ip_address: str):
    audit = AuditService(self.db)

    user = await self.user_repo.get_by_email(data.email)

    if not user or not verify_password(data.password, user.password_hash):
        await audit.log_login_failed(
            email=data.email,
            ip_address=ip_address,
            reason="invalid_credentials",
        )
        raise UnauthorizedException("Invalid credentials")

    # Create tokens...

    await audit.log_login(
        user_id=user.id,
        user_email=user.email,
        ip_address=ip_address,
        method="password",
    )

    return auth_response
```
