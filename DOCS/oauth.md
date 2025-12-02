# OAuth Authentication

FastCMS supports OAuth authentication for popular providers, allowing users to sign in with their existing accounts from Google, GitHub, or Microsoft.

## Supported Providers

- **Google** - Google account authentication
- **GitHub** - GitHub account authentication
- **Microsoft** - Microsoft account authentication

## Configuration

OAuth providers are configured via environment variables in your `.env` file:

**Google OAuth:**
```env
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/oauth/google/callback
```

**GitHub OAuth:**
```env
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GITHUB_REDIRECT_URI=http://localhost:8000/api/v1/oauth/github/callback
```

**Microsoft OAuth:**
```env
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
MICROSOFT_REDIRECT_URI=http://localhost:8000/api/v1/oauth/microsoft/callback
```

## Setting Up OAuth Providers

### Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth 2.0 Client ID"
5. Select "Web application"
6. Add authorized redirect URI: `http://localhost:8000/api/v1/oauth/google/callback`
7. Copy the Client ID and Client Secret to your `.env` file

### GitHub OAuth

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click "New OAuth App"
3. Fill in:
   - Application name: Your app name
   - Homepage URL: `http://localhost:8000`
   - Authorization callback URL: `http://localhost:8000/api/v1/oauth/github/callback`
4. Copy the Client ID and Client Secret to your `.env` file

### Microsoft OAuth

1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to "Azure Active Directory" > "App registrations"
3. Click "New registration"
4. Fill in:
   - Name: Your app name
   - Redirect URI: `http://localhost:8000/api/v1/oauth/microsoft/callback`
5. Copy the Application (client) ID
6. Create a new client secret under "Certificates & secrets"
7. Copy both values to your `.env` file

## OAuth Flow

**1. Initiate OAuth Login**

Redirect users to the OAuth authorization URL:

```bash
GET /api/v1/oauth/{provider}/login
```

**Example:**
```
http://localhost:8000/api/v1/oauth/google/login
http://localhost:8000/api/v1/oauth/github/login
http://localhost:8000/api/v1/oauth/microsoft/login
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
- Returns JWT tokens for your application

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

**JavaScript Example:**
```javascript
// Redirect to OAuth login
function loginWithGoogle() {
  window.location.href = 'http://localhost:8000/api/v1/oauth/google/login';
}

// Handle callback (if handling manually)
const urlParams = new URLSearchParams(window.location.search);
const code = urlParams.get('code');
if (code) {
  // Exchange code for tokens
  fetch(`http://localhost:8000/api/v1/oauth/google/callback?code=${code}`)
    .then(res => res.json())
    .then(data => {
      // Store tokens
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      // Redirect to dashboard
      window.location.href = '/dashboard';
    });
}
```

## OAuth with Auth Collections

OAuth works with both the main user system and auth collections (e.g., customers, vendors).

**Collection-specific OAuth:**
```bash
GET /api/v1/oauth/{provider}/login?collection=customers
```

This allows customers to sign in with OAuth while keeping them separate from admin users.

## Account Linking

If a user signs in with OAuth and an account with that email already exists:
- **Email verified**: Accounts are automatically linked
- **Email not verified**: User must verify email first or use password login

## Security Considerations

1. **HTTPS in Production**: Always use HTTPS URLs for OAuth redirects in production
2. **State Parameter**: FastCMS automatically includes CSRF protection via state parameter
3. **Redirect URI Validation**: Ensure redirect URIs match exactly in provider settings
4. **Scope Limitations**: OAuth only requests minimal required scopes (email, profile)

## Troubleshooting

**Redirect URI Mismatch:**
- Ensure the redirect URI in your `.env` file exactly matches what's configured in the OAuth provider
- Include the full URL: `http://localhost:8000/api/v1/oauth/google/callback`

**Access Denied Error:**
- User denied permission at the OAuth provider
- User needs to retry the OAuth flow

**Invalid Client Error:**
- Client ID or Client Secret is incorrect
- Verify credentials in `.env` file match provider settings

**Email Already Exists:**
- An account with this email already exists
- User can sign in with password or request password reset
- Or verify the existing account's email to enable linking

## Best Practices

1. **Production URLs**: Update redirect URIs to your production domain before deploying
2. **Error Handling**: Implement proper error handling for OAuth failures
3. **Email Verification**: Encourage users to verify email even with OAuth
4. **Multiple Providers**: Allow users to link multiple OAuth providers to one account
5. **Fallback**: Always provide traditional email/password login as backup
