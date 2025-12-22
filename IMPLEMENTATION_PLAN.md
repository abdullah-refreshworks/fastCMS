# FastCMS Security Implementation Plan

## Completed (Phase 1 - Security Foundation)

### 1. Two-Factor Authentication (2FA/TOTP) ✅
- **Files Created/Modified:**
  - `app/services/two_factor_service.py` - TOTP logic
  - `app/schemas/auth.py` - 2FA schemas
  - `app/api/v1/auth.py` - 2FA endpoints
  - `app/db/models/user.py` - 2FA fields
  - `migrations/versions/20251222_add_2fa_fields.py`
  - `DOCS/two-factor-auth.md`
- **Features:** Setup, enable, disable, verify, backup codes
- **Commit:** Done

### 2. API Keys for Service Authentication ✅
- **Files Created/Modified:**
  - `app/db/models/api_key.py` - APIKey model
  - `app/services/api_key_service.py` - Key management
  - `app/api/v1/api_keys.py` - API endpoints
  - `app/core/dependencies.py` - X-API-Key header support
  - `migrations/versions/20251222_1104_*_add_api_keys_table.py`
  - `DOCS/api-keys.md`
- **Features:** Create, list, update, delete, revoke, usage tracking
- **Commit:** Done

### 3. Security Headers Middleware ✅
- **Files Created/Modified:**
  - `app/core/middleware.py` - SecurityHeadersMiddleware
  - `app/main.py` - Middleware registration
  - `DOCS/security-headers.md`
- **Headers:** X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, CSP, HSTS, Referrer-Policy, Permissions-Policy
- **Commit:** Done

### 4. Enhanced Audit Logging ✅
- **Files Created/Modified:**
  - `app/db/models/audit_log.py` - AuditLog model
  - `app/services/audit_service.py` - Audit logging service
  - `app/api/v1/audit.py` - Admin endpoints
  - `migrations/versions/20251222_1257_*_add_audit_logs_table.py`
  - `DOCS/audit-logging.md`
- **Features:** Event types, severity levels, user tracking, statistics, cleanup
- **Commit:** Done

### 5. Per-User Rate Limiting ✅
- **Files Created/Modified:**
  - `app/core/rate_limit.py` - Enhanced middleware
  - `DOCS/rate-limiting.md`
- **Features:** Per-user/IP limits, role-based limits, endpoint-specific limits, audit integration
- **Commit:** Done

---

## Remaining Work (Phase 2-4)

### Phase 2: User Experience & Admin Features

#### 1. Account Lockout After Failed Attempts
- Lock accounts after X failed login attempts
- Configurable lockout duration
- Admin unlock capability
- **Files to modify:**
  - `app/db/models/user.py` - Add `failed_attempts`, `locked_until` fields
  - `app/services/auth_service.py` - Implement lockout logic
  - `app/api/v1/admin.py` - Admin unlock endpoint
  - Create migration

#### 2. Session Management
- List active sessions per user
- Revoke specific sessions
- "Log out all devices" feature
- **Files to create:**
  - `app/db/models/session.py` - Session tracking model
  - `app/services/session_service.py` - Session management
  - `app/api/v1/sessions.py` - Session endpoints
  - Create migration

#### 3. Password Policies
- Configurable password requirements
- Password history (prevent reuse)
- Password expiration (optional)
- **Files to modify:**
  - `app/core/config.py` - Password policy settings
  - `app/services/auth_service.py` - Policy enforcement
  - `app/db/models/user.py` - Password history field

#### 4. Admin Dashboard Enhancements
- Security overview dashboard
- User management improvements
- System health monitoring
- **Files to modify:**
  - `app/admin/templates/` - Dashboard templates
  - `app/api/v1/admin.py` - Dashboard data endpoints

### Phase 3: Integration & Monitoring

#### 1. Email Notifications for Security Events
- Login from new device/location
- Password changed
- 2FA enabled/disabled
- Account locked
- **Files to create:**
  - `app/services/security_notifications.py`
  - Email templates for security events

#### 2. IP Allowlist/Blocklist
- Admin-configurable IP restrictions
- Temporary and permanent blocks
- **Files to create:**
  - `app/db/models/ip_rules.py`
  - `app/services/ip_filter_service.py`
  - `app/core/middleware.py` - IP filter middleware
  - Create migration

#### 3. Webhook Security
- Signed webhook payloads
- Retry with exponential backoff
- Delivery status tracking
- **Files to modify:**
  - `app/services/webhook_service.py`
  - `app/db/models/webhook.py` - Add signature fields

#### 4. Enhanced Logging & Monitoring
- Structured logging improvements
- Log aggregation support
- Metrics export (Prometheus format)
- **Files to create:**
  - `app/core/metrics.py`
  - `app/api/v1/metrics.py`

### Phase 4: Advanced Security

#### 1. OAuth Enhancements
- PKCE support
- More providers (Apple, Discord, etc.)
- Custom OAuth provider configuration
- **Files to modify:**
  - `app/services/oauth_service.py`
  - `app/api/v1/oauth.py`

#### 2. Field-Level Encryption
- Encrypt sensitive fields at rest
- Key rotation support
- **Files to create:**
  - `app/core/encryption.py`
  - Field type modifier for encrypted fields

#### 3. Data Export Controls
- Export audit logging
- Rate limiting on exports
- Admin approval for large exports
- **Files to modify:**
  - `app/api/v1/records.py` - Export endpoints
  - `app/services/export_service.py`

#### 4. Compliance Features
- GDPR data export
- Right to deletion
- Data retention policies
- Consent management
- **Files to create:**
  - `app/services/compliance_service.py`
  - `app/api/v1/compliance.py`

---

## Integration Points Needed

The following integrations should be added to existing code:

### 1. Integrate Audit Logging into Auth Service
Add audit logging calls to `app/services/auth_service.py`:
```python
# In login method
await audit.log_login(user_id, user_email, ip_address)

# In login failure
await audit.log_login_failed(email, ip_address, reason)

# In password change
await audit.log_password_change(user_id, user_email, ip_address)
```

### 2. Integrate Audit Logging into API Key Service
Add audit logging calls to `app/services/api_key_service.py`:
```python
# In create_key
await audit.log_api_key_event(EventAction.CREATE, ...)

# In delete_key
await audit.log_api_key_event(EventAction.DELETE, ...)

# In revoke_all_keys
await audit.log_api_key_event(EventAction.REVOKE_ALL, ...)
```

### 3. Integrate Audit Logging into 2FA Service
Add audit logging calls to `app/services/two_factor_service.py`:
```python
# In enable()
await audit.log_2fa_event(EventAction.ENABLE, ...)

# In disable()
await audit.log_2fa_event(EventAction.DISABLE, ...)
```

---

## Testing Checklist

### Phase 1 Testing (Complete these before moving to Phase 2)

- [ ] 2FA setup flow works
- [ ] 2FA login verification works
- [ ] Backup codes work
- [ ] API key creation returns full key once
- [ ] API key authentication works
- [ ] API key revocation works
- [ ] Security headers present on all responses
- [ ] CSP doesn't break admin UI
- [ ] Audit logs capture events correctly
- [ ] Audit API endpoints work (admin only)
- [ ] Rate limiting applies different limits by role
- [ ] Rate limiting applies stricter limits on login endpoint
- [ ] Rate limit exceeded returns 429 with Retry-After

---

## Configuration Options to Add

Add these to `app/core/config.py` and `.env.example`:

```python
# Security Settings
ACCOUNT_LOCKOUT_ATTEMPTS: int = 5
ACCOUNT_LOCKOUT_DURATION: int = 1800  # 30 minutes
PASSWORD_MIN_LENGTH: int = 8
PASSWORD_REQUIRE_UPPERCASE: bool = True
PASSWORD_REQUIRE_LOWERCASE: bool = True
PASSWORD_REQUIRE_DIGIT: bool = True
PASSWORD_REQUIRE_SPECIAL: bool = True
PASSWORD_HISTORY_COUNT: int = 5
SESSION_MAX_AGE: int = 86400  # 24 hours
API_KEY_DEFAULT_EXPIRY_DAYS: int = 365
```

---

## Notes

- All new features should include documentation in `DOCS/`
- All database changes need migrations
- Run tests after each feature
- Commit after each completed feature with descriptive message
- Update `DOCS/README.md` index when adding new docs
