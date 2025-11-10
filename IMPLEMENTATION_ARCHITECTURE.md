# FastCMS Implementation Architecture - Feature Additions

## Overview

This document details the technical architecture for implementing missing features to achieve parity with PocketBase and Supabase while maintaining FastCMS's AI-native advantages.

---

## 1. CLI TOOL ARCHITECTURE

### 1.1 Technology Stack
- **Framework**: Click (Python CLI framework)
- **Package**: `fastcms-cli` (installable via pip)
- **Structure**:
```
fastcms_cli/
├── __init__.py
├── main.py           # Entry point
├── commands/
│   ├── init.py       # Project scaffolding
│   ├── dev.py        # Development server
│   ├── migrate.py    # Database migrations
│   ├── deploy.py     # Deployment helpers
│   ├── collections.py # Collection management
│   └── users.py      # User management
├── templates/        # Project templates
└── utils/           # Helper functions
```

### 1.2 Core Commands
```bash
# Project initialization
fastcms init my-project --database sqlite|postgres
fastcms init my-project --template blog|ecommerce|saas

# Development
fastcms dev --port 8000 --reload
fastcms dev --debug

# Database operations
fastcms migrate create "add_users_table"
fastcms migrate up
fastcms migrate down
fastcms migrate status

# Collection management
fastcms collections list
fastcms collections create posts --schema posts.json
fastcms collections export posts > posts.json

# User management
fastcms users create admin@example.com --admin
fastcms users list --role admin
fastcms users delete user@example.com

# Deployment
fastcms deploy --target docker|fly|railway
fastcms backup create
fastcms backup restore backup.db
```

### 1.3 Project Structure Template
```
my-project/
├── .env                    # Environment variables
├── fastcms.config.json     # Project configuration
├── app/
│   ├── collections/        # Collection schemas
│   ├── functions/          # Custom serverless functions
│   ├── hooks/              # Event hooks
│   └── migrations/         # Database migrations
├── data/                   # SQLite database and files
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### 1.4 Configuration File (`fastcms.config.json`)
```json
{
  "version": "1.0.0",
  "name": "my-project",
  "database": {
    "type": "sqlite",
    "url": "sqlite+aiosqlite:///./data/app.db"
  },
  "storage": {
    "type": "local",
    "path": "./data/files"
  },
  "auth": {
    "providers": ["email", "google", "github"],
    "mfa": true,
    "magic_links": true
  },
  "features": {
    "realtime": true,
    "webhooks": true,
    "ai": true,
    "edge_functions": true
  }
}
```

---

## 2. GRAPHQL API ARCHITECTURE

### 2.1 Technology Stack
- **Framework**: Strawberry GraphQL (FastAPI integration)
- **Alternative**: Graphene-Python
- **Endpoint**: `/graphql`

### 2.2 Implementation Structure
```
app/api/graphql/
├── __init__.py
├── schema.py          # Main schema
├── types/
│   ├── user.py        # User type
│   ├── collection.py  # Collection type
│   ├── record.py      # Generic record type
│   └── file.py        # File type
├── queries/
│   ├── users.py       # User queries
│   ├── collections.py # Collection queries
│   └── records.py     # Record queries
├── mutations/
│   ├── auth.py        # Authentication mutations
│   ├── records.py     # CRUD mutations
│   └── files.py       # File mutations
└── subscriptions/
    └── realtime.py    # GraphQL subscriptions
```

### 2.3 Dynamic Schema Generation
- Auto-generate GraphQL types from collection schemas
- Support for relations (expand functionality)
- Field-level permissions enforcement

### 2.4 Example Query
```graphql
query GetPosts {
  posts(
    filter: { status: "published" }
    sort: "-created"
    limit: 10
  ) {
    id
    title
    content
    author {
      id
      name
      email
    }
    created
  }
}

mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    id
    title
    status
  }
}
```

---

## 3. FULL-TEXT SEARCH ARCHITECTURE

### 3.1 SQLite Implementation (FTS5)
```python
# Create FTS5 virtual table for collection
CREATE VIRTUAL TABLE posts_fts USING fts5(
    title,
    content,
    tokenize='porter unicode61'
);

# Auto-sync with main table using triggers
CREATE TRIGGER posts_ai AFTER INSERT ON posts BEGIN
    INSERT INTO posts_fts(rowid, title, content)
    VALUES (new.id, new.title, new.content);
END;
```

### 3.2 PostgreSQL Implementation
```python
# Add tsvector column
ALTER TABLE posts ADD COLUMN search_vector tsvector;

# Create GIN index
CREATE INDEX posts_search_idx ON posts USING GIN(search_vector);

# Auto-update with trigger
CREATE TRIGGER posts_search_update
BEFORE INSERT OR UPDATE ON posts
FOR EACH ROW EXECUTE FUNCTION
tsvector_update_trigger(search_vector, 'pg_catalog.english', title, content);
```

### 3.3 API Endpoint
```python
# app/api/v1/search.py
@router.get("/{collection_name}/search")
async def full_text_search(
    collection_name: str,
    q: str,  # Search query
    fields: list[str] = None,  # Fields to search
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    # SQLite FTS5
    # SELECT * FROM posts_fts WHERE posts_fts MATCH 'query' ORDER BY rank

    # PostgreSQL
    # SELECT * FROM posts WHERE search_vector @@ to_tsquery('english', 'query')
    pass
```

---

## 4. WEBSOCKET & REALTIME ARCHITECTURE

### 4.1 WebSocket Manager
```python
# app/core/websocket_manager.py
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.user_presence: Dict[str, Dict] = {}

    async def connect(self, websocket: WebSocket, channel: str, user_id: str):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)

    async def broadcast(self, channel: str, message: dict):
        if channel in self.active_connections:
            for connection in self.active_connections[channel]:
                await connection.send_json(message)

    async def update_presence(self, channel: str, user_id: str, status: dict):
        self.user_presence[f"{channel}:{user_id}"] = status
        await self.broadcast(channel, {
            "type": "presence",
            "user_id": user_id,
            "status": status
        })
```

### 4.2 WebSocket Endpoints
```python
# app/api/v1/realtime_ws.py
@router.websocket("/ws/{channel}")
async def websocket_endpoint(
    websocket: WebSocket,
    channel: str,
    token: str = None
):
    # Authenticate
    user = await verify_token(token)

    # Connect
    await manager.connect(websocket, channel, user.id if user else None)

    try:
        while True:
            data = await websocket.receive_json()

            # Handle different message types
            if data["type"] == "broadcast":
                await manager.broadcast(channel, data["payload"])
            elif data["type"] == "presence":
                await manager.update_presence(channel, user.id, data["status"])
    except WebSocketDisconnect:
        await manager.disconnect(websocket, channel, user.id)
```

### 4.3 Channel Types
1. **Database Changes**: `db:{collection_name}` or `db:{collection}:{record_id}`
2. **Broadcast**: `channel:{channel_name}`
3. **Presence**: `presence:{channel_name}`
4. **User-specific**: `user:{user_id}`

---

## 5. AUTHENTICATION ENHANCEMENTS

### 5.1 Magic Link Flow
```python
# Database model
class MagicLink(Base):
    __tablename__ = "magic_links"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(String(50), nullable=False)
    used = Column(Boolean, default=False)
    created = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# API endpoints
@router.post("/auth/magic-link/request")
async def request_magic_link(email: str):
    # Generate token
    token = secrets.token_urlsafe(32)

    # Save to database
    magic_link = MagicLink(email=email, token=token, expires_at=...)

    # Send email with link
    link = f"{BASE_URL}/auth/magic-link/verify?token={token}"
    await send_email(email, "Magic Link", f"Click here: {link}")

@router.get("/auth/magic-link/verify")
async def verify_magic_link(token: str):
    # Verify token and return JWT
    pass
```

### 5.2 Phone/SMS Authentication
```python
# Database model
class PhoneVerification(Base):
    __tablename__ = "phone_verifications"

    id = Column(String(36), primary_key=True)
    phone_number = Column(String(20), nullable=False, index=True)
    code = Column(String(6), nullable=False)  # 6-digit code
    expires_at = Column(String(50), nullable=False)
    verified = Column(Boolean, default=False)

# Integration with Twilio
from twilio.rest import Client

@router.post("/auth/phone/send-code")
async def send_verification_code(phone: str):
    code = "".join([str(random.randint(0, 9)) for _ in range(6)])

    # Send via Twilio
    client = Client(TWILIO_SID, TWILIO_TOKEN)
    client.messages.create(
        to=phone,
        from_=TWILIO_PHONE,
        body=f"Your verification code is: {code}"
    )

    # Save to database
    verification = PhoneVerification(phone_number=phone, code=code, ...)

@router.post("/auth/phone/verify")
async def verify_phone_code(phone: str, code: str):
    # Verify and return JWT
    pass
```

### 5.3 Multi-Factor Authentication (TOTP)
```python
import pyotp

# Database model
class MFASecret(Base):
    __tablename__ = "mfa_secrets"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), unique=True)
    secret = Column(String(32), nullable=False)  # Base32 secret
    enabled = Column(Boolean, default=False)
    backup_codes = Column(JSON)  # List of one-time backup codes

# Setup MFA
@router.post("/auth/mfa/setup")
async def setup_mfa(user: User = Depends(get_current_user)):
    # Generate secret
    secret = pyotp.random_base32()

    # Create QR code
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(user.email, issuer_name="FastCMS")

    # Generate QR code image
    import qrcode
    qr = qrcode.make(uri)

    # Save secret (disabled until verified)
    mfa = MFASecret(user_id=user.id, secret=secret, enabled=False)

    return {"secret": secret, "qr_code": qr, "uri": uri}

@router.post("/auth/mfa/verify")
async def verify_mfa_setup(code: str, user: User = Depends(get_current_user)):
    mfa = await get_mfa_secret(user.id)
    totp = pyotp.TOTP(mfa.secret)

    if totp.verify(code):
        mfa.enabled = True
        # Generate backup codes
        mfa.backup_codes = [secrets.token_hex(4) for _ in range(10)]
        return {"success": True, "backup_codes": mfa.backup_codes}

@router.post("/auth/login-with-mfa")
async def login_with_mfa(email: str, password: str, mfa_code: str):
    # Verify password first
    user = await authenticate_user(email, password)

    # Then verify MFA
    mfa = await get_mfa_secret(user.id)
    totp = pyotp.TOTP(mfa.secret)

    if totp.verify(mfa_code) or mfa_code in mfa.backup_codes:
        return create_tokens(user)
```

---

## 6. TYPESCRIPT/JAVASCRIPT SDK

### 6.1 SDK Structure
```typescript
// fastcms-js/src/index.ts
export class FastCMS {
  private baseUrl: string;
  private apiKey?: string;

  auth: AuthService;
  collections: CollectionService;
  storage: StorageService;
  realtime: RealtimeService;

  constructor(config: FastCMSConfig) {
    this.baseUrl = config.baseUrl;
    this.apiKey = config.apiKey;

    this.auth = new AuthService(this);
    this.collections = new CollectionService(this);
    this.storage = new StorageService(this);
    this.realtime = new RealtimeService(this);
  }

  collection<T = any>(name: string): CollectionClient<T> {
    return new CollectionClient<T>(this, name);
  }
}

// Type-safe collection client
class CollectionClient<T> {
  async create(data: Partial<T>): Promise<T> { }
  async getList(options?: QueryOptions): Promise<ListResult<T>> { }
  async getOne(id: string, options?: ExpandOptions): Promise<T> { }
  async update(id: string, data: Partial<T>): Promise<T> { }
  async delete(id: string): Promise<void> { }

  // Realtime
  subscribe(callback: (data: RealtimeEvent<T>) => void): UnsubscribeFn { }
}

// Usage example
const client = new FastCMS({ baseUrl: 'http://localhost:8000' });

// Auth
await client.auth.signUpWithEmail('user@example.com', 'password');
await client.auth.signInWithEmail('user@example.com', 'password');
await client.auth.signInWithOAuth('google');

// CRUD with type safety
interface Post {
  id: string;
  title: string;
  content: string;
  author: string;
}

const posts = client.collection<Post>('posts');
const post = await posts.create({ title: 'Hello', content: '...' });
const list = await posts.getList({ filter: 'status=published', sort: '-created' });

// Realtime
posts.subscribe((event) => {
  console.log(event.action, event.record);
});

// Storage
const file = await client.storage.upload(fileBlob, { collection: 'posts' });
const url = client.storage.getUrl(file.id);
```

### 6.2 Type Generation from Schemas
```typescript
// fastcms-js/cli/generate-types.ts
async function generateTypes(baseUrl: string, output: string) {
  // Fetch all collections
  const collections = await fetch(`${baseUrl}/api/v1/collections`);

  // Generate TypeScript interfaces
  const types = collections.map(col => {
    return `
export interface ${pascalCase(col.name)} {
  id: string;
  ${col.schema.map(field => {
    return `${field.name}: ${mapFieldType(field.type)};`;
  }).join('\n  ')}
  created: string;
  updated: string;
}
    `;
  });

  // Write to file
  fs.writeFileSync(output, types.join('\n'));
}
```

---

## 7. SERVERLESS FUNCTIONS ARCHITECTURE

### 7.1 Function Structure
```
app/functions/
├── send-welcome-email.py
├── process-payment.py
├── generate-report.py
└── resize-image.py
```

### 7.2 Function Format
```python
# app/functions/send-welcome-email.py
"""
FastCMS Serverless Function
Trigger: auth.create
"""

def handler(event, context):
    """
    event: {
        "type": "auth.create",
        "data": { "id": "...", "email": "...", ... },
        "timestamp": "..."
    }
    context: {
        "user": { ... },  # Authenticated user (if any)
        "env": { ... },   # Environment variables
        "db": DatabaseClient,
        "storage": StorageClient
    }
    """
    user = event["data"]

    # Send email
    context.send_email(
        to=user["email"],
        subject="Welcome!",
        body=f"Welcome {user['name']}!"
    )

    return {"success": True}
```

### 7.3 Execution Engine (Sandboxed)
```python
# app/services/functions_service.py
import RestrictedPython
from RestrictedPython import compile_restricted, safe_globals

class FunctionExecutor:
    def __init__(self, function_code: str):
        self.code = function_code

    async def execute(self, event: dict, context: dict):
        # Compile in restricted mode
        byte_code = compile_restricted(
            self.code,
            filename='<function>',
            mode='exec'
        )

        # Restricted globals (no file I/O, no imports except allowed)
        restricted_globals = safe_globals.copy()
        restricted_globals['__builtins__'] = self._get_safe_builtins()

        # Execute with timeout
        exec(byte_code, restricted_globals)

        # Call handler
        handler = restricted_globals['handler']
        result = handler(event, context)

        return result

    def _get_safe_builtins(self):
        # Only allow safe built-ins
        return {
            'print': print,
            'len': len,
            'range': range,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'dict': dict,
            'list': list,
            # No open, exec, eval, __import__, etc.
        }
```

### 7.4 Function Triggers
```python
# Database model
class ServerlessFunction(Base):
    __tablename__ = "serverless_functions"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), unique=True)
    code = Column(Text)  # Python code
    trigger_type = Column(String(50))  # "http", "event", "schedule"
    trigger_config = Column(JSON)  # Event name, cron schedule, etc.
    timeout = Column(Integer, default=10)  # seconds
    memory_limit = Column(Integer, default=128)  # MB
    enabled = Column(Boolean, default=True)

# HTTP trigger
@router.post("/functions/{function_name}/invoke")
async def invoke_function(function_name: str, payload: dict):
    func = await get_function(function_name)
    executor = FunctionExecutor(func.code)
    result = await executor.execute(
        event={"type": "http", "data": payload},
        context=build_context()
    )
    return result

# Event trigger (automatic)
async def trigger_functions_for_event(event_type: str, data: dict):
    functions = await get_functions_by_trigger("event", event_type)
    for func in functions:
        await invoke_function_async(func, {"type": event_type, "data": data})
```

---

## 8. FIELD-LEVEL PERMISSIONS

### 8.1 Schema Enhancement
```python
# Enhanced collection schema
{
  "name": "posts",
  "schema": [
    {
      "name": "title",
      "type": "text",
      "required": true,
      "read_rule": "",  # Public read
      "write_rule": "@request.auth.id = @record.author_id"
    },
    {
      "name": "draft_notes",
      "type": "text",
      "read_rule": "@request.auth.id = @record.author_id",  # Only author
      "write_rule": "@request.auth.id = @record.author_id"
    },
    {
      "name": "internal_score",
      "type": "number",
      "read_rule": "@request.auth.role = 'admin'",  # Admin only
      "write_rule": "@request.auth.role = 'admin'"
    }
  ]
}
```

### 8.2 Field Filtering Logic
```python
# app/services/field_permissions.py
async def filter_fields_by_permissions(
    record: dict,
    collection: Collection,
    user: User | None
) -> dict:
    filtered = {}

    for field in collection.schema:
        field_name = field["name"]
        read_rule = field.get("read_rule", "")

        # Evaluate read rule
        if await can_read_field(read_rule, user, record):
            filtered[field_name] = record.get(field_name)

    # Always include system fields
    for sys_field in ["id", "created", "updated"]:
        filtered[sys_field] = record.get(sys_field)

    return filtered
```

---

## 9. SCHEDULED JOBS

### 9.1 APScheduler Integration
```python
# app/core/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

class JobScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    def start(self):
        self.scheduler.start()

    def add_job(self, func, cron: str, job_id: str):
        self.scheduler.add_job(
            func,
            CronTrigger.from_crontab(cron),
            id=job_id,
            replace_existing=True
        )

    def remove_job(self, job_id: str):
        self.scheduler.remove_job(job_id)

# Database model
class ScheduledJob(Base):
    __tablename__ = "scheduled_jobs"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), unique=True)
    function_id = Column(String(36), ForeignKey("serverless_functions.id"))
    cron_schedule = Column(String(100))  # "0 0 * * *" (daily at midnight)
    enabled = Column(Boolean, default=True)
    last_run = Column(DateTime)
    next_run = Column(DateTime)

# Example jobs
async def cleanup_expired_tokens():
    # Delete expired refresh tokens
    pass

async def send_daily_digest():
    # Send email summary
    pass

# Register jobs on startup
@app.on_event("startup")
async def start_scheduler():
    scheduler = JobScheduler()
    scheduler.add_job(cleanup_expired_tokens, "0 0 * * *", "cleanup_tokens")
    scheduler.add_job(send_daily_digest, "0 8 * * *", "daily_digest")
    scheduler.start()
```

---

## 10. ADVANCED IMAGE TRANSFORMATIONS

### 10.1 URL-based Transformations
```python
# GET /api/v1/files/{file_id}/transform?width=300&height=200&format=webp&quality=80

from PIL import Image
import io

@router.get("/files/{file_id}/transform")
async def transform_image(
    file_id: str,
    width: int = None,
    height: int = None,
    format: str = None,
    quality: int = 85,
    crop: str = None,  # "center", "top", "bottom", "left", "right"
    blur: int = None,
    grayscale: bool = False
):
    # Load original file
    file = await get_file(file_id)
    img = Image.open(file.storage_path)

    # Resize
    if width or height:
        if crop:
            img = crop_image(img, width, height, crop)
        else:
            img.thumbnail((width or img.width, height or img.height))

    # Filters
    if grayscale:
        img = img.convert('L')

    if blur:
        from PIL import ImageFilter
        img = img.filter(ImageFilter.GaussianBlur(blur))

    # Convert format
    output = io.BytesIO()
    img.save(output, format=format or file.format, quality=quality)
    output.seek(0)

    return StreamingResponse(output, media_type=f"image/{format or file.format}")
```

---

## 11. SQL EDITOR IN ADMIN

### 11.1 Frontend (Monaco Editor)
```html
<!-- app/admin/templates/sql_editor.html -->
<div id="sql-editor" style="height: 400px;"></div>
<button onclick="executeQuery()">Run Query</button>
<div id="results"></div>

<script src="https://cdn.jsdelivr.net/npm/monaco-editor@0.33.0/min/vs/loader.js"></script>
<script>
require.config({ paths: { vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.33.0/min/vs' } });
require(['vs/editor/editor.main'], function() {
  window.editor = monaco.editor.create(document.getElementById('sql-editor'), {
    value: 'SELECT * FROM users LIMIT 10;',
    language: 'sql',
    theme: 'vs-dark',
    automaticLayout: true
  });
});

async function executeQuery() {
  const query = window.editor.getValue();
  const response = await fetch('/api/v1/admin/sql/execute', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  });
  const data = await response.json();
  displayResults(data);
}
</script>
```

### 11.2 Backend (Protected)
```python
# app/api/v1/admin/sql.py
@router.post("/sql/execute")
async def execute_sql(
    query: str,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    # Validate query (read-only)
    if not is_read_only_query(query):
        raise HTTPException(400, "Only SELECT queries allowed")

    # Execute with timeout
    try:
        result = await db.execute(text(query))
        rows = result.fetchall()
        columns = result.keys()

        return {
            "columns": list(columns),
            "rows": [dict(zip(columns, row)) for row in rows],
            "count": len(rows)
        }
    except Exception as e:
        raise HTTPException(400, str(e))

def is_read_only_query(query: str) -> bool:
    # Simple validation (improve with SQL parser)
    query_upper = query.strip().upper()
    dangerous = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE"]
    return not any(keyword in query_upper for keyword in dangerous)
```

---

## 12. IMPLEMENTATION PRIORITIES

### Phase 1: Foundation (Week 1)
1. ✅ CLI Tool basic structure
2. ✅ Full-Text Search (SQLite FTS5)
3. ✅ TypeScript SDK foundations

### Phase 2: Realtime (Week 2)
4. ✅ WebSocket support
5. ✅ Broadcast messaging
6. ✅ Presence tracking

### Phase 3: Auth (Week 3)
7. ✅ Magic Links
8. ✅ Phone/SMS auth
9. ✅ MFA (TOTP)

### Phase 4: Advanced Features (Week 4-5)
10. ✅ GraphQL API
11. ✅ Serverless functions
12. ✅ Field-level permissions
13. ✅ Scheduled jobs

### Phase 5: Polish (Week 6)
14. ✅ SQL Editor
15. ✅ Advanced image transforms
16. ✅ Complete SDK
17. ✅ Documentation

---

## 13. DATABASE MIGRATIONS NEEDED

### New Tables
```sql
-- Magic links
CREATE TABLE magic_links (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at VARCHAR(50) NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created DATETIME NOT NULL
);

-- Phone verifications
CREATE TABLE phone_verifications (
    id VARCHAR(36) PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    code VARCHAR(6) NOT NULL,
    expires_at VARCHAR(50) NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    created DATETIME NOT NULL
);

-- MFA secrets
CREATE TABLE mfa_secrets (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) UNIQUE NOT NULL,
    secret VARCHAR(32) NOT NULL,
    enabled BOOLEAN DEFAULT FALSE,
    backup_codes JSON,
    created DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Serverless functions
CREATE TABLE serverless_functions (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    code TEXT NOT NULL,
    trigger_type VARCHAR(50) NOT NULL,
    trigger_config JSON,
    timeout INTEGER DEFAULT 10,
    memory_limit INTEGER DEFAULT 128,
    enabled BOOLEAN DEFAULT TRUE,
    created DATETIME NOT NULL,
    updated DATETIME NOT NULL
);

-- Scheduled jobs
CREATE TABLE scheduled_jobs (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    function_id VARCHAR(36),
    cron_schedule VARCHAR(100) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    last_run DATETIME,
    next_run DATETIME,
    created DATETIME NOT NULL,
    FOREIGN KEY (function_id) REFERENCES serverless_functions(id)
);

-- Presence tracking
CREATE TABLE presence (
    id VARCHAR(36) PRIMARY KEY,
    channel VARCHAR(100) NOT NULL,
    user_id VARCHAR(36),
    status JSON NOT NULL,
    last_seen DATETIME NOT NULL,
    INDEX (channel, user_id)
);
```

---

## 14. DEPENDENCIES TO ADD

```toml
# pyproject.toml additions

[tool.poetry.dependencies]
# GraphQL
strawberry-graphql = {extras = ["fastapi"], version = "^0.235.0"}

# Full-text search (already using SQLite FTS5, no extra deps for PostgreSQL)

# WebSocket (already in FastAPI)

# Auth enhancements
pyotp = "^2.9.0"  # TOTP for MFA
qrcode = "^7.4.2"  # QR code generation
twilio = "^9.0.0"  # SMS

# Serverless functions
RestrictedPython = "^6.2"  # Sandboxed execution

# Scheduled jobs
APScheduler = "^3.10.4"

# Image processing (already have Pillow)

# CLI
click = "^8.1.7"
rich = "^13.7.0"  # Beautiful terminal output
```

---

## CONCLUSION

This architecture provides a comprehensive plan to implement all missing features while maintaining:
- **Clean code structure**
- **Type safety** (Pydantic, TypeScript)
- **Security** (sandboxing, validation, auth)
- **Performance** (async, caching, indexing)
- **Developer experience** (CLI, SDK, docs)

The phased approach allows for iterative development and testing, ensuring each feature is production-ready before moving to the next.
