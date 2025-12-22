# Two-Factor Authentication (2FA)

FastCMS supports TOTP-based two-factor authentication for enhanced account security. Users can enable 2FA using any authenticator app (Google Authenticator, Authy, 1Password, etc.).

## Features

- **TOTP-based**: Uses Time-based One-Time Passwords (RFC 6238)
- **QR Code Setup**: Easy scanning with authenticator apps
- **Backup Codes**: 10 one-time recovery codes
- **Secure Storage**: Secrets stored securely in the database

## Setup 2FA

### Step 1: Generate Setup

```bash
curl -X POST http://localhost:8000/api/v1/auth/2fa/setup \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEU...",
  "otpauth_url": "otpauth://totp/FastCMS:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=FastCMS"
}
```

### Step 2: Scan QR Code

1. Open your authenticator app (Google Authenticator, Authy, etc.)
2. Scan the QR code from the response
3. The app will show a 6-digit code

### Step 3: Enable 2FA

Verify the code to complete setup:

```bash
curl -X POST http://localhost:8000/api/v1/auth/2fa/enable \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code": "123456"}'
```

**Response:**
```json
{
  "enabled": true,
  "backup_codes": [
    "a1b2-c3d4",
    "e5f6-g7h8",
    "i9j0-k1l2",
    "m3n4-o5p6",
    "q7r8-s9t0",
    "u1v2-w3x4",
    "y5z6-a7b8",
    "c9d0-e1f2",
    "g3h4-i5j6",
    "k7l8-m9n0"
  ],
  "message": "2FA enabled successfully. Save your backup codes securely."
}
```

**Important:** Save your backup codes in a secure location. Each code can only be used once.

## Login with 2FA

When 2FA is enabled, login requires both password and TOTP code:

### First Request (Password Only)

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "yourpassword"
  }'
```

**Response (2FA Required):**
```json
{
  "user": {"id": "...", "email": "user@example.com", "two_factor_enabled": true},
  "token": {"access_token": "", "refresh_token": "", "expires_in": 0},
  "requires_2fa": true,
  "message": "Two-factor authentication required"
}
```

### Second Request (With 2FA Code)

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "yourpassword",
    "two_factor_code": "123456"
  }'
```

**Response (Success):**
```json
{
  "user": {"id": "...", "email": "user@example.com", "two_factor_enabled": true},
  "token": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 86400
  },
  "requires_2fa": false
}
```

## Using Backup Codes

If you lose access to your authenticator app, use a backup code instead of the TOTP code:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "yourpassword",
    "two_factor_code": "a1b2-c3d4"
  }'
```

**Note:** Each backup code can only be used once. After use, it's automatically invalidated.

## Check 2FA Status

```bash
curl http://localhost:8000/api/v1/auth/2fa/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "enabled": true,
  "backup_codes_remaining": 8
}
```

## Regenerate Backup Codes

If you've used some backup codes or want new ones:

```bash
curl -X POST http://localhost:8000/api/v1/auth/2fa/backup-codes \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code": "123456"}'
```

**Note:** This requires a valid TOTP code (not a backup code) and invalidates all previous backup codes.

## Disable 2FA

```bash
curl -X POST http://localhost:8000/api/v1/auth/2fa/disable \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code": "123456"}'
```

You can use either a TOTP code or a backup code to disable 2FA.

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/2fa/status` | GET | Check 2FA status |
| `/api/v1/auth/2fa/setup` | POST | Generate setup (secret + QR code) |
| `/api/v1/auth/2fa/enable` | POST | Enable 2FA with verification code |
| `/api/v1/auth/2fa/disable` | POST | Disable 2FA |
| `/api/v1/auth/2fa/backup-codes` | POST | Regenerate backup codes |

## JavaScript Example

```javascript
class TwoFactorAuth {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  async setup() {
    const res = await fetch(`${this.baseUrl}/api/v1/auth/2fa/setup`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    return res.json();
  }

  async enable(code) {
    const res = await fetch(`${this.baseUrl}/api/v1/auth/2fa/enable`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ code })
    });
    return res.json();
  }

  async disable(code) {
    const res = await fetch(`${this.baseUrl}/api/v1/auth/2fa/disable`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ code })
    });
    return res.json();
  }

  async status() {
    const res = await fetch(`${this.baseUrl}/api/v1/auth/2fa/status`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    return res.json();
  }
}

// Usage
const twoFA = new TwoFactorAuth('http://localhost:8000', userToken);

// Setup 2FA
const setup = await twoFA.setup();
console.log('Scan this QR code:', setup.qr_code);

// Enable after user scans and enters code
const result = await twoFA.enable('123456');
console.log('Backup codes:', result.backup_codes);
```

## Security Best Practices

1. **Save Backup Codes**: Store them in a secure location (password manager, safe)
2. **Use Authenticator Apps**: Prefer apps over SMS-based 2FA
3. **Don't Share Codes**: Never share your TOTP codes or backup codes
4. **Regular Regeneration**: Regenerate backup codes periodically
5. **Secure Your Device**: Keep your authenticator app device secure

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Code invalid | Ensure device time is synced (TOTP is time-based) |
| QR code won't scan | Use the manual entry secret instead |
| Lost authenticator | Use a backup code to log in and disable 2FA |
| No backup codes left | Contact administrator to reset 2FA |
