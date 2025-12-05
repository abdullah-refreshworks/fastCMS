# System Settings

FastCMS includes a comprehensive settings system for storing application configuration values in the database. Settings can be managed via the Admin UI or API.

## Admin UI

Navigate to **Admin > Settings** to access the settings interface with four tabs:

### Authentication Tab
Configure how users authenticate:
- **Authentication Methods**: Enable/disable password, OAuth, OTP, MFA
- **OAuth Behavior**: Auto-create users, link by email, require verification
- **Password Requirements**: Minimum length, complexity rules
- **Token Settings**: Access and refresh token expiry

### OAuth Providers Tab
Manage OAuth providers for social login:
- View configured providers with status
- Add new providers (29 supported)
- Edit provider credentials
- Enable/disable providers
- Reorder provider display

See [OAuth Documentation](oauth.md) for details.

### Mail Tab
Configure SMTP for sending emails:
- SMTP Host and Port
- SMTP Username and Password
- From Email and Name

### Storage Tab
Configure file storage:
- Storage Type (Local, S3, or Azure Blob Storage)
- Maximum File Size
- S3 Configuration (bucket, region, credentials, custom endpoint)
- Azure Configuration (container, connection string or account credentials)

## Setting Categories

Settings are organized into categories:

| Category | Description |
|----------|-------------|
| `app` | General application settings |
| `auth` | Authentication and security settings |
| `mail` | Email/SMTP configuration |
| `storage` | File storage configuration |
| `backup` | Backup settings |
| `logs` | Request logging settings |

## Default Settings

FastCMS initializes with these default settings:

### App Settings
| Key | Default | Description |
|-----|---------|-------------|
| `app_name` | "FastCMS" | Application name |
| `app_url` | "http://localhost:8000" | Application URL |
| `rate_limit_per_minute` | 100 | Rate limit per minute |
| `rate_limit_per_hour` | 1000 | Rate limit per hour |

### Auth Settings
| Key | Default | Description |
|-----|---------|-------------|
| `password_auth_enabled` | true | Enable password authentication |
| `otp_enabled` | false | Enable OTP authentication |
| `mfa_enabled` | false | Enable MFA |
| `oauth_enabled` | true | Enable OAuth2 |
| `oauth_auto_create_user` | true | Auto-create on OAuth login |
| `oauth_link_by_email` | true | Link OAuth by email |
| `password_min_length` | 8 | Minimum password length |
| `password_require_upper` | false | Require uppercase |
| `password_require_number` | false | Require number |
| `password_require_special` | false | Require special char |
| `token_expiry_hours` | 24 | Access token expiry |
| `refresh_token_expiry_days` | 7 | Refresh token expiry |
| `verification_required` | false | Require email verification |

### Mail Settings
| Key | Default | Description |
|-----|---------|-------------|
| `smtp_host` | "" | SMTP server host |
| `smtp_port` | 587 | SMTP server port |
| `smtp_user` | "" | SMTP username |
| `smtp_password` | "" | SMTP password |
| `from_email` | "noreply@fastcms.dev" | From email |
| `from_name` | "FastCMS" | From name |

### Backup Settings
| Key | Default | Description |
|-----|---------|-------------|
| `enabled` | true | Enable automated backups |
| `cron_schedule` | "0 2 * * *" | Cron schedule (2 AM daily) |
| `retention_days` | 30 | Keep backups for N days |
| `s3_enabled` | false | Upload to S3 |
| `s3_bucket` | "" | S3 bucket name |

### Storage Settings
| Key | Default | Description |
|-----|---------|-------------|
| `type` | "local" | Storage type (local/s3/azure) |
| `max_file_size` | 10485760 | Max file size (10MB) |
| `s3_bucket` | "" | S3 bucket name |
| `s3_region` | "" | S3 region (e.g., us-east-1) |
| `s3_access_key` | "" | S3 access key ID |
| `s3_secret_key` | "" | S3 secret access key |
| `s3_endpoint` | "" | Custom S3 endpoint (for MinIO, etc.) |
| `azure_container` | "" | Azure container name |
| `azure_connection_string` | "" | Azure connection string (recommended) |
| `azure_account_name` | "" | Azure storage account name |
| `azure_account_key` | "" | Azure storage account key |

### Logs Settings
| Key | Default | Description |
|-----|---------|-------------|
| `enabled` | true | Enable request logging |
| `retention_days` | 7 | Keep logs for N days |
| `log_body` | false | Log request/response bodies |

## Settings API

### Get All Settings

```bash
GET /api/v1/settings
Authorization: Bearer ADMIN_TOKEN
```

**Response:**
```json
{
  "app": {
    "app_name": {
      "value": "FastCMS",
      "description": "Application name"
    },
    "rate_limit_per_minute": {
      "value": 100,
      "description": "Rate limit per minute"
    }
  },
  "auth": {
    "password_auth_enabled": {
      "value": true,
      "description": "Enable password authentication"
    }
  }
}
```

### Get Settings by Category

```bash
GET /api/v1/settings/{category}
Authorization: Bearer ADMIN_TOKEN
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/settings/auth" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Response:**
```json
{
  "password_auth_enabled": {
    "value": true,
    "description": "Enable password authentication"
  },
  "oauth_enabled": {
    "value": true,
    "description": "Enable OAuth2 authentication"
  },
  "password_min_length": {
    "value": 8,
    "description": "Minimum password length"
  }
}
```

### Update a Setting

```bash
POST /api/v1/settings
Authorization: Bearer ADMIN_TOKEN
Content-Type: application/json

{
  "key": "password_min_length",
  "value": 12,
  "category": "auth",
  "description": "Minimum password length"
}
```

**Response:**
```json
{
  "id": "setting-uuid",
  "key": "password_min_length",
  "value": 12,
  "category": "auth"
}
```

### Delete a Setting

```bash
DELETE /api/v1/settings/{key}
Authorization: Bearer ADMIN_TOKEN
```

**Response:**
```json
{
  "deleted": true
}
```

## Using Settings in Code

Access settings programmatically in your application code:

```python
from app.services.settings_service import SettingsService

async def example(db):
    settings = SettingsService(db)

    # Get a setting with default
    min_length = await settings.get("password_min_length", default=8)

    # Set a setting
    await settings.set(
        key="maintenance_mode",
        value=True,
        category="app",
        description="Enable maintenance mode"
    )

    # Get all settings in a category
    auth_settings = await settings.get_category("auth")

    # Delete a setting
    await settings.delete("old_setting")
```

## Common Use Cases

### Enable Maintenance Mode
```json
{
  "key": "maintenance_mode",
  "value": true,
  "category": "app",
  "description": "Site is under maintenance"
}
```

### Configure Rate Limiting
```json
{
  "key": "rate_limit_per_minute",
  "value": 60,
  "category": "app",
  "description": "Max API requests per minute"
}
```

### Enable Strict Password Policy
```bash
curl -X POST "http://localhost:8000/api/v1/settings" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"key": "password_min_length", "value": 12, "category": "auth"}'

curl -X POST "http://localhost:8000/api/v1/settings" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"key": "password_require_upper", "value": true, "category": "auth"}'

curl -X POST "http://localhost:8000/api/v1/settings" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"key": "password_require_number", "value": true, "category": "auth"}'

curl -X POST "http://localhost:8000/api/v1/settings" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"key": "password_require_special", "value": true, "category": "auth"}'
```

## Best Practices

1. **Use Categories**: Organize related settings together
2. **Add Descriptions**: Always include helpful descriptions
3. **Set Defaults**: Have sensible defaults in your code
4. **Validate Values**: Check setting values before using them
5. **Use Admin UI**: Prefer the Admin UI for configuration
6. **Backup Settings**: Settings are included in database backups
