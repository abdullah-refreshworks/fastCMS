# Security Headers

FastCMS includes a comprehensive security headers middleware that adds important HTTP security headers to all responses. These headers protect against common web vulnerabilities.

## Headers Overview

| Header | Value | Purpose |
|--------|-------|---------|
| X-Content-Type-Options | nosniff | Prevents MIME type sniffing |
| X-Frame-Options | DENY | Prevents clickjacking attacks |
| X-XSS-Protection | 1; mode=block | XSS filter for legacy browsers |
| Referrer-Policy | strict-origin-when-cross-origin | Controls referrer information |
| Permissions-Policy | (restrictive) | Disables unnecessary browser features |
| Content-Security-Policy | (see below) | Controls resource loading |
| Strict-Transport-Security | max-age=31536000 | HSTS (production only) |
| Cache-Control | no-store, no-cache, must-revalidate, private | API response caching |

## Header Details

### X-Content-Type-Options

```http
X-Content-Type-Options: nosniff
```

Prevents browsers from MIME-sniffing a response away from the declared content-type. This helps prevent:
- XSS attacks via content-type confusion
- Drive-by downloads

### X-Frame-Options

```http
X-Frame-Options: DENY
```

Prevents the page from being displayed in frames, iframes, or objects. Protects against:
- Clickjacking attacks
- UI redressing attacks

### X-XSS-Protection

```http
X-XSS-Protection: 1; mode=block
```

Enables the XSS filter built into most browsers. When a potential XSS attack is detected:
- Browser blocks rendering
- Prevents reflected XSS attacks

**Note:** This is primarily for legacy browsers. Modern browsers use CSP instead.

### Referrer-Policy

```http
Referrer-Policy: strict-origin-when-cross-origin
```

Controls how much referrer information is sent:
- **Same-origin requests**: Full URL
- **Cross-origin requests**: Origin only (no path)
- **HTTPS to HTTP**: No referrer

### Permissions-Policy

```http
Permissions-Policy: accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()
```

Disables browser features that FastCMS doesn't need:
- Accelerometer access
- Camera access
- Geolocation
- Gyroscope
- Magnetometer
- Microphone
- Payment API
- USB access

### Content-Security-Policy (CSP)

Default policy:

```http
Content-Security-Policy:
  default-src 'self';
  script-src 'self' 'unsafe-inline' 'unsafe-eval';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  font-src 'self' data:;
  connect-src 'self' ws: wss:;
  frame-ancestors 'none';
  base-uri 'self';
  form-action 'self'
```

| Directive | Value | Purpose |
|-----------|-------|---------|
| default-src | 'self' | Only load resources from same origin |
| script-src | 'self' 'unsafe-inline' 'unsafe-eval' | Scripts (admin UI requires inline) |
| style-src | 'self' 'unsafe-inline' | Styles with inline support |
| img-src | 'self' data: https: | Images from same origin, data URIs, HTTPS |
| font-src | 'self' data: | Fonts from same origin and data URIs |
| connect-src | 'self' ws: wss: | AJAX/WebSocket connections |
| frame-ancestors | 'none' | Cannot be embedded in frames |
| base-uri | 'self' | Restrict `<base>` element |
| form-action | 'self' | Form submissions to same origin |

### Strict-Transport-Security (HSTS)

**Only in production:**

```http
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

Forces browsers to only use HTTPS:
- **max-age**: 1 year (31536000 seconds)
- **includeSubDomains**: Applies to all subdomains

### Cache-Control (API Responses)

For all `/api/` endpoints:

```http
Cache-Control: no-store, no-cache, must-revalidate, private
Pragma: no-cache
```

Prevents caching of API responses to:
- Protect sensitive data
- Ensure fresh data on each request

## Configuration

The security headers middleware can be customized in `app/main.py`:

```python
from app.core.middleware import SecurityHeadersMiddleware

app.add_middleware(
    SecurityHeadersMiddleware,
    content_security_policy="custom CSP here",
    permissions_policy="custom permissions here",
    hsts_max_age=63072000,  # 2 years
    frame_options="SAMEORIGIN",  # Allow same-origin frames
    include_subdomains=False,
)
```

### Custom CSP for Third-Party Services

If you use external services, extend the CSP:

```python
# Allow Google Analytics and external APIs
custom_csp = "; ".join([
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' https://www.google-analytics.com",
    "img-src 'self' data: https:",
    "connect-src 'self' ws: wss: https://api.external-service.com",
    "frame-ancestors 'none'",
])

app.add_middleware(
    SecurityHeadersMiddleware,
    content_security_policy=custom_csp,
)
```

## Testing Security Headers

### Using cURL

```bash
curl -I https://your-fastcms.com/api/v1/health
```

### Using Security Scanners

- [Security Headers](https://securityheaders.com/) - Online scanner
- [Mozilla Observatory](https://observatory.mozilla.org/) - Comprehensive analysis
- [Qualys SSL Labs](https://www.ssllabs.com/ssltest/) - SSL/TLS testing

### Expected Grade

With default configuration, FastCMS should achieve:
- **Security Headers**: A grade
- **Mozilla Observatory**: A- to A+ grade

## Troubleshooting

### Admin UI Not Loading

If the admin UI doesn't load, the CSP might be too restrictive. Check browser console for CSP violations:

```javascript
// In browser console
document.addEventListener('securitypolicyviolation', (e) => {
    console.log('CSP Violation:', e.violatedDirective, e.blockedURI);
});
```

### WebSocket Connection Failed

Ensure `connect-src` includes WebSocket protocols:

```http
connect-src 'self' ws: wss:
```

### External Images Not Loading

Add external domains to `img-src`:

```http
img-src 'self' data: https: https://cdn.example.com
```

## Security Recommendations

1. **Use HTTPS in Production**
   - HSTS only activates over HTTPS
   - Set up SSL/TLS with valid certificates

2. **Review CSP Regularly**
   - Monitor CSP violation reports
   - Remove unnecessary permissions

3. **Test After Changes**
   - Run security scanners after configuration changes
   - Test all functionality with new headers

4. **Consider Report-Only Mode**
   ```python
   # Use Content-Security-Policy-Report-Only first
   response.headers["Content-Security-Policy-Report-Only"] = csp
   ```
