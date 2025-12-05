# OAuth Authentication

FastCMS supports OAuth authentication with **29 providers**, allowing users to sign in with their existing accounts. OAuth providers can be configured via the Admin UI or API.

## Supported Providers

FastCMS supports all major OAuth providers (matching PocketBase compatibility):

| Provider | Type | Required Fields |
|----------|------|-----------------|
| Google | `google` | client_id, client_secret |
| GitHub | `github` | client_id, client_secret |
| Microsoft | `microsoft` | client_id, client_secret |
| Apple | `apple` | client_id, client_secret, team_id, key_id |
| Discord | `discord` | client_id, client_secret |
| Facebook | `facebook` | client_id, client_secret |
| GitLab | `gitlab` | client_id, client_secret |
| Twitter/X | `twitter` | client_id, client_secret |
| Spotify | `spotify` | client_id, client_secret |
| Twitch | `twitch` | client_id, client_secret |
| Kakao | `kakao` | client_id, client_secret |
| Yandex | `yandex` | client_id, client_secret |
| VK | `vk` | client_id, client_secret |
| Bitbucket | `bitbucket` | client_id, client_secret |
| Instagram | `instagram` | client_id, client_secret |
| Strava | `strava` | client_id, client_secret |
| Box | `box` | client_id, client_secret |
| Gitea | `gitea` | client_id, client_secret, custom_url |
| Gitee | `gitee` | client_id, client_secret |
| Linear | `linear` | client_id, client_secret |
| LiveChat | `livechat` | client_id, client_secret |
| Monday.com | `monday` | client_id, client_secret |
| Notion | `notion` | client_id, client_secret |
| Patreon | `patreon` | client_id, client_secret |
| Planning Center | `planningcenter` | client_id, client_secret |
| WakaTime | `wakatime` | client_id, client_secret |
| Mailcow | `mailcow` | client_id, client_secret, custom_url |
| OpenID Connect | `oidc` | client_id, client_secret, discovery_url |
| Lark/Feishu | `lark` | client_id, client_secret |

## Configuration Methods

### Method 1: Admin UI (Recommended)

1. Navigate to **Admin > Settings > OAuth Providers**
2. Click **"Add Provider"**
3. Select the provider type from the dropdown
4. Enter the required credentials (Client ID, Client Secret)
5. Toggle **"Enabled"** to activate the provider
6. Click **"Add Provider"** to save

The UI automatically shows:
- Required fields for each provider type
- The redirect URL to configure in your OAuth app

### Method 2: Environment Variables (Legacy)

For backward compatibility, providers can still be configured via `.env`:

```env
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/oauth/google/callback

GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

**Note:** Database-configured providers (via Admin UI) take precedence over environment variables.

### Method 3: API

Create providers programmatically via the OAuth Provider Management API.

## OAuth Provider Management API

All provider management endpoints require admin authentication.

### List Available Provider Types

Get all supported OAuth provider types with their required fields:

```bash
GET /api/v1/oauth/providers/types
```

**Response:**
```json
[
  {
    "type": "google",
    "name": "Google",
    "required_fields": ["client_id", "client_secret"],
    "optional_fields": [],
    "scopes": ["openid", "email", "profile"]
  },
  {
    "type": "github",
    "name": "GitHub",
    "required_fields": ["client_id", "client_secret"],
    "optional_fields": [],
    "scopes": ["user:email"]
  }
]
```

### List Configured Providers

```bash
GET /api/v1/oauth/providers
Authorization: Bearer ADMIN_TOKEN
```

**Response:**
```json
[
  {
    "id": "provider-uuid",
    "provider_type": "google",
    "name": "Google",
    "enabled": true,
    "client_id": "12345678...",
    "has_secret": true,
    "extra_config": {},
    "custom_scopes": null,
    "collection_id": null,
    "display_order": 0
  }
]
```

### List Enabled Providers (Public)

For login UI - returns only enabled providers without sensitive data:

```bash
GET /api/v1/oauth/providers/enabled
```

**Response:**
```json
[
  {
    "type": "google",
    "name": "Google",
    "auth_url": "https://accounts.google.com/o/oauth2/v2/auth"
  }
]
```

### Create Provider

```bash
POST /api/v1/oauth/providers
Authorization: Bearer ADMIN_TOKEN
Content-Type: application/json

{
  "provider_type": "google",
  "name": "Google",
  "client_id": "your-client-id.apps.googleusercontent.com",
  "client_secret": "your-client-secret",
  "enabled": true
}
```

**Response:** `201 Created`
```json
{
  "id": "new-provider-uuid",
  "provider_type": "google",
  "name": "Google",
  "enabled": true,
  "client_id": "12345678...",
  "has_secret": true
}
```

### Update Provider

```bash
PATCH /api/v1/oauth/providers/{provider_id}
Authorization: Bearer ADMIN_TOKEN
Content-Type: application/json

{
  "enabled": false,
  "client_secret": "new-secret"
}
```

### Delete Provider

```bash
DELETE /api/v1/oauth/providers/{provider_id}
Authorization: Bearer ADMIN_TOKEN
```

**Response:** `204 No Content`

### Reorder Providers

Control display order in login UI:

```bash
POST /api/v1/oauth/providers/reorder
Authorization: Bearer ADMIN_TOKEN
Content-Type: application/json

{
  "provider_ids": ["provider-uuid-1", "provider-uuid-2", "provider-uuid-3"]
}
```

## Setting Up OAuth Providers

### Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth 2.0 Client ID"
5. Select "Web application"
6. Add authorized redirect URI: `http://localhost:8000/api/v1/oauth/google/callback`
7. Copy the Client ID and Client Secret
8. Add via Admin UI or API

### GitHub OAuth

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click "New OAuth App"
3. Fill in:
   - Application name: Your app name
   - Homepage URL: `http://localhost:8000`
   - Authorization callback URL: `http://localhost:8000/api/v1/oauth/github/callback`
4. Copy the Client ID and Client Secret
5. Add via Admin UI or API

### Microsoft OAuth

1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to "Azure Active Directory" > "App registrations"
3. Click "New registration"
4. Add redirect URI: `http://localhost:8000/api/v1/oauth/microsoft/callback`
5. Copy the Application (client) ID
6. Create a client secret under "Certificates & secrets"
7. Add via Admin UI or API

### OpenID Connect (Generic)

For any OIDC-compatible provider:

```json
{
  "provider_type": "oidc",
  "name": "My OIDC Provider",
  "client_id": "your-client-id",
  "client_secret": "your-client-secret",
  "extra_config": {
    "discovery_url": "https://your-provider.com/.well-known/openid-configuration"
  }
}
```

## OAuth Flow

**1. Initiate OAuth Login**

Redirect users to the OAuth authorization URL:

```
GET /api/v1/oauth/{provider}/login
```

**Examples:**
```
http://localhost:8000/api/v1/oauth/google/login
http://localhost:8000/api/v1/oauth/github/login
```

**2. User Authorization**

The user is redirected to the provider's login page where they authorize your application.

**3. Callback**

After authorization, the provider redirects back to:
```
/api/v1/oauth/{provider}/callback?code=AUTHORIZATION_CODE
```

FastCMS automatically:
- Exchanges the code for an access token
- Fetches the user's profile information
- Creates or updates the user account
- Returns JWT tokens

**4. Response**

```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "user-uuid",
    "email": "user@gmail.com",
    "name": "John Doe",
    "verified": true,
    "oauth_provider": "google"
  }
}
```

## Using OAuth in Your Frontend

**HTML Example:**
```html
<a href="http://localhost:8000/api/v1/oauth/google/login">
  <button>Sign in with Google</button>
</a>

<a href="http://localhost:8000/api/v1/oauth/github/login">
  <button>Sign in with GitHub</button>
</a>
```

**Dynamic Provider Buttons:**
```javascript
// Fetch enabled providers
const providers = await fetch('/api/v1/oauth/providers/enabled').then(r => r.json());

// Render login buttons
providers.forEach(provider => {
  const button = document.createElement('a');
  button.href = `/api/v1/oauth/${provider.type}/login`;
  button.innerHTML = `Sign in with ${provider.name}`;
  loginContainer.appendChild(button);
});
```

## OAuth with Auth Collections

OAuth works with both the main user system and auth collections.

**Collection-specific OAuth:**
```
GET /api/v1/oauth/{provider}/login?collection=customers
```

This allows customers to sign in with OAuth while keeping them separate from admin users.

## OAuth Behavior Settings

Configure OAuth behavior in **Admin > Settings > Authentication**:

| Setting | Description | Default |
|---------|-------------|---------|
| `oauth_enabled` | Enable OAuth authentication | `true` |
| `oauth_auto_create_user` | Auto-create user on first OAuth login | `true` |
| `oauth_link_by_email` | Link OAuth to existing user by email | `true` |

## Account Linking

If a user signs in with OAuth and an account with that email already exists:
- **Email verified + `oauth_link_by_email` enabled**: Accounts are automatically linked
- **Email not verified**: User must verify email first or use password login

## Security Considerations

1. **HTTPS in Production**: Always use HTTPS URLs for OAuth redirects
2. **State Parameter**: FastCMS includes CSRF protection via state parameter
3. **Redirect URI Validation**: Ensure redirect URIs match exactly in provider settings
4. **Secrets Storage**: Client secrets are encrypted in the database

## Troubleshooting

**Redirect URI Mismatch:**
- Ensure the redirect URI exactly matches: `http://localhost:8000/api/v1/oauth/{provider}/callback`
- Check for trailing slashes

**Access Denied Error:**
- User denied permission at the OAuth provider
- Check if the correct scopes are requested

**Invalid Client Error:**
- Client ID or Client Secret is incorrect
- Verify credentials match provider settings

**Provider Not Found:**
- Provider not configured or not enabled
- Check `/api/v1/oauth/providers/enabled` for active providers

## Best Practices

1. **Use Admin UI**: Easier to manage and update providers
2. **Production URLs**: Update redirect URIs before deploying
3. **Multiple Providers**: Offer several options for user convenience
4. **Error Handling**: Implement proper error handling for OAuth failures
5. **Fallback**: Always provide email/password login as backup
