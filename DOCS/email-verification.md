# Email Verification & Password Reset

FastCMS includes a complete email verification and password reset system for both admin users and auth collection users.

## SMTP Configuration

First, configure your SMTP settings in the `.env` file:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@fastcms.dev
SMTP_FROM_NAME=FastCMS
```

**Gmail Setup:**
1. Enable 2-factor authentication on your Google account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the app password in `SMTP_PASSWORD`

**Other SMTP Providers:**
- **SendGrid**: Use `smtp.sendgrid.net` on port 587
- **Mailgun**: Use `smtp.mailgun.org` on port 587
- **AWS SES**: Use your SES SMTP endpoint

## Email Verification Flow

When a user registers, they receive a verification email with a token.

**1. User Registration (Email Sent Automatically)**

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "name": "John Doe"
  }'
```

The user will receive an email with a verification link like:
```
http://localhost:8000/verify?token=abc123...
```

**2. Verify Email**

```bash
curl -X POST http://localhost:8000/api/v1/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{
    "token": "abc123..."
  }'
```

**Response:**
```json
{
  "message": "Email verified successfully",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "verified": true
  }
}
```

**3. Resend Verification Email**

If the token expires (valid for 24 hours), users can request a new one:

```bash
curl -X POST http://localhost:8000/api/v1/auth/resend-verification \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

## Password Reset Flow

**1. Request Password Reset**

```bash
curl -X POST http://localhost:8000/api/v1/auth/request-password-reset \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

**Response:**
```json
{
  "message": "If the email exists, a password reset link has been sent"
}
```

The user will receive an email with a reset link like:
```
http://localhost:8000/reset-password?token=xyz789...
```

**2. Reset Password**

```bash
curl -X POST http://localhost:8000/api/v1/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "xyz789...",
    "new_password": "NewSecurePass456!",
    "password_confirm": "NewSecurePass456!"
  }'
```

**Response:**
```json
{
  "message": "Password reset successfully"
}
```

## Auth Collections Email Support

Email verification and password reset also work for auth collections (customers, vendors, etc.):

**Registration (Sends Verification Email):**
```bash
curl -X POST http://localhost:8000/api/v1/collections/customers/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "customer@example.com",
    "password": "SecurePass123!"
  }'
```

**Request Password Reset:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/request-password-reset \
  -H "Content-Type: application/json" \
  -d '{
    "email": "customer@example.com",
    "collection": "customers"
  }'
```

## Email Templates

Email templates are HTML-based and include:
- **Verification Email**: Welcome message with verification button
- **Password Reset Email**: Security notice with reset button

Templates are located in `app/services/email_service.py` and can be customized.

## Token Security

- **Verification Tokens**: Valid for 24 hours, single-use
- **Password Reset Tokens**: Valid for 1 hour, single-use
- Tokens are cryptographically secure random strings
- Used tokens are marked and cannot be reused

## Troubleshooting

**Email Not Sending:**
1. Check SMTP credentials in `.env`
2. Verify SMTP host/port are correct
3. Check firewall allows outbound SMTP connections
4. Review server logs for SMTP errors

**Gmail "Less Secure Apps" Error:**
- Don't use "less secure apps" - use App Passwords instead
- Enable 2FA and generate an app-specific password

**Email Goes to Spam:**
- Configure SPF/DKIM records for your domain
- Use a professional email service (SendGrid, Mailgun)
- Avoid localhost/development domains in production
