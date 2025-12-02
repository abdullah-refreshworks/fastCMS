# System Settings

FastCMS includes a settings system for storing application configuration values in the database.

## What are System Settings?

Settings are key-value pairs stored in the database that control application behavior. Unlike environment variables, settings can be changed at runtime without restarting the application.

**Use Cases:**
- Feature flags
- Application-wide configuration
- User preferences
- API keys for third-party services
- Rate limits
- Default values

## Setting Categories

Settings are organized into categories:
- `app` - General application settings
- `email` - Email/SMTP configuration
- `security` - Security and authentication settings
- `storage` - File storage configuration
- `custom` - Your custom settings

## Get All Settings

**Endpoint:** `GET /api/v1/settings`

**Requires:** Admin authentication

**Example:**
```bash
curl "http://localhost:8000/api/v1/settings" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Response:**
```json
[
  {
    "id": "setting-1",
    "key": "app_name",
    "value": "My FastCMS",
    "category": "app",
    "description": "Application name"
  },
  {
    "id": "setting-2",
    "key": "max_upload_size",
    "value": 10485760,
    "category": "storage",
    "description": "Maximum file upload size in bytes"
  }
]
```

## Get Settings by Category

**Endpoint:** `GET /api/v1/settings/{category}`

**Example:**
```bash
curl "http://localhost:8000/api/v1/settings/email" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Response:**
```json
[
  {
    "id": "setting-3",
    "key": "smtp_host",
    "value": "smtp.gmail.com",
    "category": "email",
    "description": "SMTP server host"
  },
  {
    "id": "setting-4",
    "key": "smtp_port",
    "value": 587,
    "category": "email",
    "description": "SMTP server port"
  }
]
```

## Update a Setting

**Endpoint:** `POST /api/v1/settings`

**Request Body:**
```json
{
  "key": "app_name",
  "value": "My FastCMS",
  "category": "app",
  "description": "Application name displayed in admin"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/settings" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "key": "maintenance_mode",
    "value": false,
    "category": "app",
    "description": "Enable maintenance mode"
  }'
```

**Response:**
```json
{
  "id": "setting-uuid",
  "key": "maintenance_mode",
  "value": false,
  "category": "app"
}
```

## Delete a Setting

**Endpoint:** `DELETE /api/v1/settings/{key}`

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/settings/old_setting" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Response:**
```json
{
  "deleted": true
}
```

## Common Settings Examples

**Application Settings:**
```json
{
  "key": "app_name",
  "value": "My FastCMS",
  "category": "app"
}
```

**Feature Flags:**
```json
{
  "key": "enable_ai_features",
  "value": true,
  "category": "app"
}
```

**Rate Limiting:**
```json
{
  "key": "api_rate_limit",
  "value": 100,
  "category": "security",
  "description": "Max API requests per minute"
}
```

**File Upload Limits:**
```json
{
  "key": "max_file_size",
  "value": 10485760,
  "category": "storage",
  "description": "Maximum file size in bytes (10MB)"
}
```

## Using Settings in Code

Settings are primarily managed via the API, but you can also access them programmatically in your application code.

**Python example:**
```python
from app.services.settings_service import SettingsService

# Get a setting
settings = SettingsService(db)
app_name = await settings.get("app_name", default="FastCMS")

# Set a setting
await settings.set(
    key="maintenance_mode",
    value=True,
    category="app",
    description="Site maintenance mode"
)
```

## Best Practices

1. **Use Categories**: Organize related settings together
2. **Add Descriptions**: Always include helpful descriptions
3. **Set Defaults**: Have sensible defaults in your code
4. **Validate Values**: Check setting values before using them
5. **Document Settings**: Keep a list of all available settings
