# Webhooks

FastCMS includes a powerful webhook system that allows you to subscribe to events and receive HTTP callbacks when records are created, updated, or deleted in your collections.

## What are Webhooks?

Webhooks are HTTP POST requests sent to a URL you specify whenever certain events occur. This allows external systems to react to changes in your FastCMS data in real-time.

**Use Cases:**
- Send notifications when new users register
- Sync data to external systems
- Trigger workflows in other applications
- Update search indexes when content changes
- Send emails or SMS notifications
- Log events to analytics platforms

## Creating a Webhook

**Endpoint:** `POST /api/v1/webhooks`

**Request Body:**
```json
{
  "url": "https://your-server.com/webhook",
  "collection_name": "posts",
  "events": ["create", "update", "delete"],
  "secret": "your-webhook-secret",
  "retry_count": 3
}
```

**Parameters:**
- `url` (required) - The endpoint that will receive webhook POSTs
- `collection_name` (required) - Collection to watch for events
- `events` (required) - Array of events to subscribe to: `["create", "update", "delete"]`
- `secret` (optional) - Secret key for HMAC signature verification
- `retry_count` (optional) - Number of retry attempts on failure (default: 3, max: 5)

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/webhooks" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "url": "https://myapp.com/api/webhook",
    "collection_name": "posts",
    "events": ["create", "update"],
    "secret": "myWebhookSecret123",
    "retry_count": 3
  }'
```

## Webhook Payload

When an event occurs, FastCMS sends a POST request to your webhook URL with this payload:

```json
{
  "event": "create",
  "collection": "posts",
  "record_id": "record-uuid",
  "data": {
    "id": "record-uuid",
    "title": "New Post",
    "content": "Post content...",
    "created": "2025-01-15T10:00:00",
    "updated": "2025-01-15T10:00:00"
  },
  "timestamp": "2025-01-15T10:00:00"
}
```

**Payload Fields:**
- `event` - Event type: `create`, `update`, or `delete`
- `collection` - Collection name where the event occurred
- `record_id` - ID of the affected record
- `data` - Full record data (empty for delete events)
- `timestamp` - When the event occurred (ISO 8601)

## Webhook Security

**HMAC Signature Verification:**

If you provided a `secret` when creating the webhook, FastCMS will sign each request with HMAC-SHA256 and include it in the `X-Webhook-Signature` header.

**Verifying the signature (Python example):**
```python
import hmac
import hashlib

def verify_webhook(request_body, signature, secret):
    expected = hmac.new(
        secret.encode(),
        request_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

# In your webhook handler:
signature = request.headers.get('X-Webhook-Signature')
if not verify_webhook(request.body, signature, 'myWebhookSecret123'):
    return 401  # Unauthorized
```

**Verifying the signature (Node.js example):**
```javascript
const crypto = require('crypto');

function verifyWebhook(body, signature, secret) {
  const expected = crypto
    .createHmac('sha256', secret)
    .update(body)
    .digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(expected),
    Buffer.from(signature)
  );
}

// In your webhook handler:
const signature = req.headers['x-webhook-signature'];
if (!verifyWebhook(req.body, signature, 'myWebhookSecret123')) {
  return res.status(401).send('Unauthorized');
}
```

## Managing Webhooks

### List All Webhooks
```bash
GET /api/v1/webhooks
```

**Filter by collection:**
```bash
GET /api/v1/webhooks?collection_name=posts
```

### Get Single Webhook
```bash
GET /api/v1/webhooks/{webhook_id}
```

### Update Webhook
```bash
PATCH /api/v1/webhooks/{webhook_id}
```

**Request Body (all fields optional):**
```json
{
  "url": "https://new-url.com/webhook",
  "events": ["create"],
  "active": false,
  "secret": "newSecret",
  "retry_count": 5
}
```

### Delete Webhook
```bash
DELETE /api/v1/webhooks/{webhook_id}
```

## Webhook Retry Logic

When your webhook endpoint fails or returns a non-2xx status code, FastCMS will automatically retry:

**Retry Schedule:**
- 1st retry: After 1 minute
- 2nd retry: After 5 minutes
- 3rd retry: After 15 minutes
- 4th retry: After 30 minutes
- 5th retry: After 1 hour

**After all retries fail:**
- Webhook is automatically disabled (`active: false`)
- You must re-enable it manually after fixing the issue

## Best Practices

1. **Respond Quickly**: Return 200 OK immediately, process the webhook asynchronously
2. **Verify Signatures**: Always verify HMAC signatures in production
3. **Be Idempotent**: Handle duplicate webhook deliveries gracefully
4. **Use HTTPS**: Only use HTTPS URLs for security
5. **Monitor Failures**: Check webhook status regularly, re-enable if disabled

## Troubleshooting

**Webhook not firing:**
- Check that the webhook is `active: true`
- Verify the collection name is correct
- Ensure events array includes the event type
- Check that your URL is accessible from the internet

**Webhook disabled automatically:**
- All retry attempts failed
- Check your endpoint logs for errors
- Fix the issue and re-enable: `PATCH /webhooks/{id}` with `{"active": true}`

**Signature verification fails:**
- Ensure you're using the same secret
- Verify you're hashing the raw request body
- Check that your HMAC implementation is correct
