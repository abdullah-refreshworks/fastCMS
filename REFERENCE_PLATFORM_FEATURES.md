# Reference Backend Platform - Complete Feature List

This document provides a comprehensive inventory of all features, capabilities, and functionalities from a reference backend-as-a-service platform, organized by category.

## Table of Contents
1. [Core Architecture](#core-architecture)
2. [Collections & Data Models](#collections--data-models)
3. [Field Types](#field-types)
4. [Record CRUD Operations](#record-crud-operations)
5. [Authentication & Authorization](#authentication--authorization)
6. [Access Control & API Rules](#access-control--api-rules)
7. [File Management](#file-management)
8. [Realtime Features](#realtime-features)
9. [Relations & Expansion](#relations--expansion)
10. [Admin/Superuser Features](#adminsuperuser-features)
11. [Settings Management](#settings-management)
12. [Logging & Monitoring](#logging--monitoring)
13. [Backup & Restore](#backup--restore)
14. [Event Hooks & Extensibility](#event-hooks--extensibility)
15. [Database Operations](#database-operations)
16. [Email System](#email-system)
17. [Production Features](#production-features)
18. [SDK & Client Features](#sdk--client-features)

---

## Core Architecture

### Platform Characteristics
- **Embedded Database**: SQLite with async operations
- **Single Binary**: Portable executable with no external dependencies
- **Admin Dashboard**: Web-based UI at `/_/` path
- **REST API**: Available at `/api/` path
- **Data Directory**: `pb_data` for all application data
- **Migration Directory**: `pb_migrations` for version control
- **Extension Support**: JavaScript and Go plugins via hooks
- **Stateless Architecture**: No traditional sessions, JWT-based auth

### Default Routes
- Static content serving at root path
- Admin dashboard at `/_/`
- REST API at `/api/`
- OAuth2 redirect endpoint at `/api/oauth2-redirect`
- Health check endpoint at `/api/health`

---

## Collections & Data Models

### Collection Types

#### 1. Base Collections
- Standard data storage for general application data
- Full CRUD operations (Create, Read, Update, Delete)
- Backed by SQLite tables
- Support all field types
- Custom indexes
- API rules for access control

#### 2. Auth Collections
- Extended collections for user management
- Special system fields:
  - `email`: User email address
  - `emailVisibility`: Control email visibility
  - `verified`: Email verification status
  - `password`: Hashed password storage
  - `tokenKey`: JWT token key
- Independent login endpoints per auth collection
- Support for multiple auth collections
- Role-based restrictions
- Relation-based ownership models
- Cross-collection user administration via `manageRule`

#### 3. View Collections
- Read-only collections
- Populated by custom SQL `SELECT` statements
- Support for aggregations and complex queries
- No create/update/delete operations
- No realtime events
- Support all field types for output

### Collection Management API

#### Endpoints
- `GET /api/collections` - List all collections (paginated)
- `GET /api/collections/{id}` - View single collection
- `POST /api/collections` - Create new collection
- `PATCH /api/collections/{id}` - Update collection
- `DELETE /api/collections/{id}` - Delete collection
- `DELETE /api/collections/{id}/truncate` - Delete all records
- `PUT /api/collections/import` - Bulk import collections
- `GET /api/collections/meta/scaffolds` - Get default templates

#### Collection Configuration
- Name and type
- Schema definition (fields)
- Indexes (single and composite)
- CRUD API rules (list, view, create, update, delete)
- Auth-specific options (for auth collections):
  - Password authentication settings
  - OAuth2 provider configurations
  - MFA settings
  - OTP settings
  - Email templates

---

## Field Types

### Basic Fields

#### BoolField
- Stores boolean values (`true`/`false`)
- Default value: `false`
- Non-nullable with zero-default fallback

#### NumberField
- Stores numeric/float64 values
- Supports modifiers:
  - `+` for addition
  - `-` for subtraction
- Non-nullable with zero-default fallback

#### TextField
- Stores string values
- Autogenerate modifier for pattern-based values
- Non-nullable with empty string default

### Text-Based Fields

#### EmailField
- Validates email addresses
- Stores single email string
- Built-in email validation

#### URLField
- Validates and stores single URL string
- URL format validation

#### EditorField
- Stores HTML formatted text
- Rich text content support

### Date & Time Fields

#### DateField
- Stores datetime in RFC3339 format
- Single datetime string value
- Manual date setting

#### AutodateField
- Auto-sets on record create/update
- Timestamp management
- Automatic value generation

### Selection Fields

#### SelectField
- Single or multiple selections
- Predefined options
- Modifiers:
  - Append new selections
  - Prepend selections
  - Remove selections

### Relationship Fields

#### RelationField
- References records from other collections
- Single or multiple relations
- Modifiers for managing relations:
  - `+` to append relation IDs
  - `-` to remove relation IDs
- Supports nested expansion (up to 6 levels)
- Back-relations via `collection_via_field` syntax

#### FileField
- Single or multiple file uploads
- File metadata storage
- Image transformation support
- File validation (type, size)

### Data Structure Fields

#### JSONField
- Stores any serialized JSON value
- Supports `null` values
- Flexible data structures

#### GeoPoint
- Stores geographic coordinates
- Format: longitude, latitude
- JSON object storage
- Supports geospatial queries via `geoDistance()` function

---

## Record CRUD Operations

### Core Endpoints

#### List/Search Records
- `GET /api/collections/{collection}/records`
- Paginated results
- Filtering support
- Sorting support
- Field selection
- Relation expansion

#### View Single Record
- `GET /api/collections/{collection}/records/{id}`
- Single record retrieval
- Relation expansion
- Field selection

#### Create Record
- `POST /api/collections/{collection}/records`
- JSON or multipart/form-data
- File upload support
- Validation based on schema
- Access control via createRule

#### Update Record
- `PATCH /api/collections/{collection}/records/{id}`
- Partial updates
- File upload support
- Field modifiers support
- Access control via updateRule

#### Delete Record
- `DELETE /api/collections/{collection}/records/{id}`
- Permanent deletion
- Cascade options for relations
- Access control via deleteRule

### Batch Operations
- `POST /api/batch`
- Transactional operations
- Create, update, upsert, delete in single request
- Must be explicitly enabled in settings
- All-or-nothing execution
- Configurable limits:
  - Max requests per batch
  - Timeout duration
  - Body size limits

### Query Parameters

#### Pagination
- `page` - Page number (default: 1)
- `perPage` - Records per page (default: 30)
- `skipTotal` - Skip total count calculation for performance

#### Sorting
- `sort` parameter
- Prefix: `+` for ASC, `-` for DESC
- Multiple fields: `sort=-created,id`
- Special sorts:
  - `@random` - Random order
  - `@rowid` - SQLite internal rowid
- Schema field sorting

#### Filtering
- `filter` parameter
- Operators:
  - `=`, `!=` - Equality
  - `>`, `>=`, `<`, `<=` - Comparison
  - `~`, `!~` - Like/Contains pattern matching
- Array operators (any/at least one):
  - `?=`, `?!=`, `?>`, `?>=`, `?<`, `?<=`, `?~`, `?!~`
- Logical operators:
  - `&&` - AND
  - `||` - OR
  - Parentheses for grouping
- Single-line comments with `//`

#### Field Selection
- `fields` parameter
- Comma-separated field list
- `*` wildcard for all fields at depth level
- `:excerpt(maxLength, withEllipsis?)` modifier for text summaries

#### Relation Expansion
- `expand` parameter
- Comma-separated relation fields
- Nested expansion: `expand=relField.subRelField`
- Up to 6 levels deep
- Respects view rules for expanded collections

---

## Authentication & Authorization

### Authentication Methods

#### 1. Password-Based Authentication
- `POST /api/collections/{collection}/auth-with-password`
- Identity field (default: email, configurable)
- Unique index requirement
- Password hashing
- JWT token generation
- Refresh token support

#### 2. One-Time Password (OTP)
- `POST /api/collections/{collection}/request-otp`
- `POST /api/collections/{collection}/auth-with-otp`
- Email-based verification
- Automatic email verification on success
- 0-9 digit passwords
- Security considerations noted

#### 3. OAuth2 Integration
- `POST /api/collections/{collection}/auth-with-oauth2`
- Supported providers:
  - Google
  - GitHub
  - Microsoft
  - Apple (with client secret generation)
  - And others (extensible)
- Two implementation approaches:
  - All-in-one popup method (recommended)
  - Manual code exchange flow
- OAuth2 redirect: `/api/oauth2-redirect`
- Not supported for superusers collection

#### 4. Multi-Factor Authentication (MFA)
- Requires two different authentication methods
- Authentication flow:
  - Initial auth returns 401 with `mfaId`
  - Secondary auth with mfaId parameter
- Available for auth collections
- Email-based OTP for second factor

### Token Management
- Fully stateless (no sessions)
- JWT-based authentication
- Authorization header: `Authorization: YOUR_AUTH_TOKEN`
- Auto-refresh token handling
- Configurable refresh thresholds
- No logout endpoint (client-side token disposal)
- Non-renewable impersonate tokens

### Auth-Related Endpoints

#### Token Refresh
- `POST /api/collections/{collection}/auth-refresh`
- Renew authentication tokens
- Automatic in SDKs

#### User Impersonation (Superuser Only)
- `POST /api/collections/{collection}/impersonate/{id}`
- Generate non-refreshable tokens
- Authenticate as different users
- API key functionality for server-to-server
- Use with extreme care

#### Password Management
- `POST /api/collections/{collection}/request-password-reset`
- `POST /api/collections/{collection}/confirm-password-reset`
- Auto-invalidates existing auth tokens on reset

#### Email Verification
- `POST /api/collections/{collection}/request-verification`
- `POST /api/collections/{collection}/confirm-verification`
- Email verification tokens

#### Email Change
- `POST /api/collections/{collection}/request-email-change`
- `POST /api/collections/{collection}/confirm-email-change`
- Requires authentication
- Invalidates existing tokens

---

## Access Control & API Rules

### Rule Types (Per Collection)
1. `listRule` - Who can list/search records
2. `viewRule` - Who can view single record
3. `createRule` - Who can create records
4. `updateRule` - Who can update records
5. `deleteRule` - Who can delete records
6. `manageRule` - Cross-user management (auth collections only)

### Rule Settings
- **Locked (null)**: Only superusers can access
- **Empty string ("")**: Public access (anyone)
- **Expression**: Filter-based access control

### Filter Expression Syntax

#### Field Groups
- Collection schema fields (including nested relations)
- `@request.*` - Request context fields:
  - `@request.method` - HTTP method
  - `@request.query.*` - Query parameters
  - `@request.headers.*` - Request headers
  - `@request.auth.*` - Authenticated user properties
  - `@request.body.*` - Request body data
  - `@request.context` - Custom context values
- `@collection.*` - Access unrelated collections via shared values
- `@record.*` - Current record being accessed

#### Operators
- **Comparison**: `=`, `!=`, `>`, `>=`, `<`, `<=`
- **String Matching**: `~` (Like/Contains), `!~` (NOT Like/Contains)
- **Array Operations**: `?=`, `?!=`, `?>`, `?>=`, `?<`, `?<=`, `?~`, `?!~`
- **Logical**: `&&` (AND), `||` (OR), parentheses for grouping

#### Special Modifiers
- `:isset` - Check if request data was submitted
- `:length` - Count array items in multi-field types
- `:each` - Apply conditions to every array element
- `:lower` - Case-insensitive comparisons

#### Datetime Macros (UTC-based)
- `@now` - Current timestamp
- `@second`, `@minute`, `@hour`, `@weekday`
- `@day`, `@month`, `@year`
- `@yesterday`, `@tomorrow`
- `@todayStart`, `@todayEnd`
- `@monthStart`, `@monthEnd`
- `@yearStart`, `@yearEnd`

#### Functions
- `geoDistance(lonA, latA, lonB, latB)` - Calculate Haversine distance in kilometers

### Access Control Behavior
- Rules act as both access control AND data filters
- Only records matching the rule are returned
- Superusers bypass all collection API rules
- Unauthenticated requests have empty `@request.auth`

---

## File Management

### File Operations

#### Upload
- Part of record create/update
- Multipart/form-data support
- Single or multiple files per field
- File validation:
  - MIME type checking
  - Size limits
  - File count limits

#### Download
- `GET /api/files/{collection}/{record}/{filename}`
- Direct file access
- Optional authentication via file tokens
- Image transformation support

#### File Tokens
- `POST /api/files/token`
- Generate temporary access tokens
- Secure file downloads
- Time-limited access

#### Delete
- Via record update (remove file from field)
- Automatic on record deletion
- Supports `-` modifier for removal

### Image Transformations (Thumbs)
- On-the-fly image resizing
- Thumbnail generation
- Query parameter based:
  - Size specifications
  - Crop options
  - Format conversion

### Storage Backends
- **Local Filesystem**: Default storage
- **S3-Compatible**: AWS S3, MinIO, etc.
  - Bucket configuration
  - Region settings
  - Endpoint customization
  - Access key management
  - Path style options
- **Azure Blob Storage**: Microsoft Azure integration

### File Management in Extensions
- `$app.newFilesystem()` - Create filesystem instance
- Operations:
  - `upload(content, key)` - Direct upload
  - `uploadFile(file, key)` - File-based upload
  - `uploadMultipart(mfh, key)` - Multipart upload
  - `getReader(key)` - Read file content
  - `list(prefix)` - List files by prefix
  - `delete(key)` - Remove files
- Record file keys: `collectionId/recordId/filename`
- Auto-managed for record attachments
- Resource cleanup with `close()`

---

## Realtime Features

### Implementation
- **Server-Sent Events (SSE)** protocol
- Two-step process:
  1. Establish SSE connection
  2. Submit client subscriptions

### Event Types
- **create** - New record created
- **update** - Record updated
- **delete** - Record deleted

### Subscription Scopes
- **Single Record**: `COLLECTION_ID_OR_NAME/RECORD_ID`
  - Uses collection's `viewRule` for access control
- **Entire Collection**: `COLLECTION_ID_OR_NAME`
  - Uses collection's `listRule` for access control

### Realtime Endpoints

#### Establish Connection
- `GET /api/realtime`
- Creates SSE connection
- Sends `PB_CONNECT` event with client ID
- Authorization on first subscription call

#### Manage Subscriptions
- `POST /api/realtime`
- Add/remove subscriptions
- Optional query parameters via `options`
- JSON or multipart/form-data support

### Connection Management
- Auto-disconnect after 5 minutes of inactivity
- Automatic reconnection support
- Abandoned connection prevention
- Client ID tracking

### SDK Integration
- Simplified `subscribe()` and `unsubscribe()` methods
- Auto-handles SSE complexity
- Available in JavaScript and Dart SDKs

### Limitations
- View collections don't support realtime (no write operations)
- Maximum 6-level nested expansion in events
- Access control applied to subscriptions

---

## Relations & Expansion

### Relation Types
- **Single Relations**: One-to-one or many-to-one
- **Multiple Relations**: One-to-many or many-to-many

### Setting Relations
- Direct ID assignment in create/update
- Array of IDs for multiple relations
- Modifiers for incremental updates:
  - `field+` - Append IDs to existing relations
  - `field-` - Remove IDs from relations

### Expanding Relations
- `expand` query parameter
- Retrieves related records without additional requests
- Access control: Only viewable relations are expanded
- Nested expansion with dot-notation
- Up to 6 levels deep

### Back-Relations
- Reference collections pointing TO the main collection
- Notation: `referenceCollection_via_relField`
- Query posts with associated comments
- Default to multiple relation behavior
- UNIQUE index constraint for single behavior
- Limited to 1000 records per field

### Relation Features
- Filtering via nested relation fields (dot-notation)
- Sorting via nested relation fields
- Programmatic expansion: `$app.expandRecord()`
- Two expansion methods:
  - `expandedOne(relField)` - Single relations
  - `expandedAll(relField)` - Multiple relations

---

## Admin/Superuser Features

### Superuser Collection
- Special `_superusers` collection
- Elevated privileges
- Bypass collection API rules
- No OAuth2 support
- Admin dashboard access

### Admin Capabilities

#### User Management
- Create/update/delete users across collections
- User impersonation
- Password reset management
- Email verification management

#### Collection Management
- Full CRUD on collections
- Schema modifications
- Index management
- Rule configuration
- Import/export collections

#### Settings Management
- Application settings
- SMTP configuration
- S3 storage settings
- OAuth2 provider setup
- Rate limiting rules
- Batch operation settings

#### System Operations
- Backup creation
- Backup restoration
- Database migrations
- Log viewing
- Health monitoring

### Admin Authentication
- Separate from auth collections
- Long-lived API keys via impersonation
- MFA support for superusers
- Enhanced security recommendations

---

## Settings Management

### Settings API

#### Endpoints
- `GET /api/settings` - List all settings (superuser only)
- `PATCH /api/settings` - Bulk update settings (superuser only)
- `POST /api/settings/test/s3` - Test S3 connection
- `POST /api/settings/test/email` - Send test email
- `POST /api/settings/apple/generate-client-secret` - Generate Apple OAuth secret

### Configurable Settings Categories

#### Meta Settings
- Application name
- Public URL
- Sender name and address
- Control visibility options

#### Logs Settings
- Retention period
- Minimum log level
- IP address logging
- Authentication ID logging

#### Backups Settings
- Cron scheduling
- Maximum backup count
- S3 configuration for remote backups

#### SMTP Settings
- Host and port
- Credentials
- TLS configuration
- Authentication method

#### S3 Storage Settings
- Bucket name
- Region
- Endpoint
- Access keys
- Path style options
- Force path style toggle

#### Batch Processing Settings
- Enable/disable batch API
- Max requests per batch
- Timeout duration
- Body size limits

#### Rate Limiting Settings
- Enable/disable rate limiter
- Rules with labels
- Max requests per duration
- IP-based or user-based

#### Trusted Proxy Settings
- Header configuration
- Leftmost IP usage
- Reverse proxy support

---

## Logging & Monitoring

### Request Logging
- Automatic incoming request tracking
- Superuser-only access
- Detailed metadata capture

### Log Endpoints

#### List Logs
- `GET /api/logs`
- Paginated results
- Filtering support
- Sorting options
- Field selection

#### View Single Log
- `GET /api/logs/{id}`
- Detailed log entry
- Custom field selection

#### Log Statistics
- `GET /api/logs/stats`
- Hourly aggregated statistics
- Analysis and monitoring data

### Logged Data
- HTTP method, URL, status code
- Execution time
- Authentication type
- User agent and referrer
- IP addresses
- Custom message and severity level
- Request/response data

### Log Query Features
- Complex filter expressions
- Sortable fields:
  - rowid, created, level, message
  - Data attributes
- Parentheses, AND, OR operators
- Single-line comment support

### Log Management
- Configurable retention period
- Minimum log level setting
- IP logging toggle
- Auth ID logging toggle

---

## Backup & Restore

### Backup Operations

#### List Backups
- `GET /api/backups`
- All available backup files
- Metadata: key, modification date, size
- Field selection support

#### Create Backup
- `POST /api/backups`
- Generate new backup
- Optional custom naming (`[a-z0-9_-].zip`)
- Auto-generated names
- Prevents concurrent operations
- Temporarily sets read-only mode

#### Upload Backup
- `POST /api/backups/upload`
- Accept existing zip archives
- Multipart/form-data
- `application/zip` MIME type validation

#### Delete Backup
- `DELETE /api/backups/{key}`
- Remove single backup
- Blocks during generation/restore

#### Download Backup
- `GET /api/backups/{key}`
- Download backup file
- Requires superuser file token

### Restore Operations
- `POST /api/backups/{key}/restore`
- Restore data from backup
- Automatic application restart
- Prevents concurrent operations
- All-or-nothing process

### Backup Configuration
- Cron-based scheduling
- Maximum backup count
- Local or S3 storage
- Superuser authorization required

### Best Practices
- For large datasets (2GB+):
  - Use `sqlite3 .backup` command
  - Combine with `rsync`
  - Alternative to API method

---

## Event Hooks & Extensibility

### Hook System
- Event-driven architecture
- Go and JavaScript support
- Pre and post operation hooks
- Transaction-aware hooks

### Hook Manipulation Methods
- `Bind(handler)` - Register with ID and priority
- `BindFunc(func)` - Simplified registration
- `Trigger(event)` - Manual event dispatch

### App Lifecycle Hooks
- `OnBootstrap` - Database and resource initialization
- `OnServe` - Web server startup and routing
- `OnSettingsReload` - Configuration changes
- `OnBackupCreate` - Backup creation events
- `OnBackupRestore` - Backup restoration events
- `OnTerminate` - Graceful shutdown handling

### Email System Hooks
- `OnMailerSend` - Intercept all email transmission
- `OnMailerRecordAuthAlertSend` - Device login notifications
- `OnMailerRecordPasswordResetSend` - Password recovery emails
- `OnMailerRecordVerificationSend` - Email verification
- `OnMailerRecordEmailChangeSend` - Email change confirmations
- `OnMailerRecordOTPSend` - OTP delivery

### Realtime Communication Hooks
- `OnRealtimeConnectRequest` - Client connection establishment
- `OnRealtimeSubscribeRequest` - Subscription modifications
- `OnRealtimeMessageSend` - Message dispatch to clients

### Record Model Hooks
- `OnRecordEnrich` - Add computed fields, redact data
- `OnRecordValidate` - Custom validation logic
- **Create Lifecycle**:
  - `OnRecordCreate` - Before create
  - `OnRecordCreateExecute` - During create
  - `OnRecordAfterCreateSuccess` - After successful create
  - `OnRecordAfterCreateError` - After failed create
- **Update Lifecycle**:
  - `OnRecordUpdate` - Before update
  - `OnRecordUpdateExecute` - During update
  - `OnRecordAfterUpdateSuccess` - After successful update
  - `OnRecordAfterUpdateError` - After failed update
- **Delete Lifecycle**:
  - `OnRecordDelete` - Before delete
  - `OnRecordDeleteExecute` - During delete
  - `OnRecordAfterDeleteSuccess` - After successful delete
  - `OnRecordAfterDeleteError` - After failed delete

### Record Authentication Hooks
- `OnRecordAuthRequest` - Post-authentication processing
- `OnRecordAuthWithPasswordRequest` - Password login
- `OnRecordAuthWithOAuth2Request` - OAuth provider linking
- `OnRecordAuthWithOTPRequest` - OTP authentication
- `OnRecordRequestPasswordResetRequest` - Reset initiation
- `OnRecordConfirmPasswordResetRequest` - Password update
- `OnRecordRequestVerificationRequest` - Verification email
- `OnRecordConfirmVerificationRequest` - Email confirmation
- `OnRecordRequestEmailChangeRequest` - Change initiation
- `OnRecordConfirmEmailChangeRequest` - Change confirmation

### Collection Model Hooks
- `OnCollectionValidate` - Schema validation
- **Create Lifecycle**: `OnCollectionCreate`, `OnCollectionCreateExecute`, Success/Error variants
- **Update Lifecycle**: `OnCollectionUpdate`, `OnCollectionUpdateExecute`, Success/Error variants
- **Delete Lifecycle**: `OnCollectionDelete`, `OnCollectionDeleteExecute`, Success/Error variants

### API Request Hooks
- **Records**: `OnRecordsListRequest`, `OnRecordViewRequest`, `OnRecordCreateRequest`, `OnRecordUpdateRequest`, `OnRecordDeleteRequest`
- **Collections**: `OnCollectionsListRequest`, `OnCollectionViewRequest`, `OnCollectionCreateRequest`, `OnCollectionUpdateRequest`, `OnCollectionDeleteRequest`, `OnCollectionsImportRequest`
- **Files**: `OnFileDownloadRequest`, `OnFileTokenRequest`
- **Settings**: `OnSettingsListRequest`, `OnSettingsUpdateRequest`
- **Batch**: `OnBatchRequest`

### Base Model Hooks
- `OnModelValidate` - All model types
- `OnModelCreate`, `OnModelUpdate`, `OnModelDelete`
- Success/Error variants for all operations

### Extension Patterns
- Transaction safety with `e.Next()`
- Request context access in request hooks
- Avoid global mutexes
- Use `e.App` over parent-scope variables
- Deadlock prevention strategies

---

## Database Operations

### Database Interface
- `$app.db()` - Access database functionality
- Returns `dbx.Builder` for SQL operations
- SQLite embedded database

### Query Execution Methods
- `execute()` - Non-data retrieval queries (INSERT, UPDATE, DELETE)
- `one()` - Single row into DynamicModel
- `all()` - Multiple rows into array

### Parameter Binding
- Named parameters: `{:paramName}` placeholders
- `bind(params)` method
- SQL injection prevention

### Query Builder Methods

#### Selection
- `select()` - Initial selection
- `andSelect()` - Add fields
- `distinct()` - Unique results

#### Tables
- `from()` - Specify table

#### Joins
- `join()` - Generic join
- `innerJoin()` - Inner join
- `leftJoin()` - Left outer join
- `rightJoin()` - Right outer join

#### Conditions
- `where()` - Initial condition
- `andWhere()` - AND condition
- `orWhere()` - OR condition

#### Ordering
- `orderBy()` - Initial sort
- `andOrderBy()` - Additional sort

#### Grouping
- `groupBy()` - Initial grouping
- `andGroupBy()` - Additional grouping
- `having()` - Group filter
- `andHaving()`, `orHaving()` - Additional group filters

#### Limits
- `limit()` - Maximum rows
- `offset()` - Skip rows

### Expression Methods ($dbx)
- `exp()` - Raw query fragments
- `hashExp()` - Column-value filtering
- `not()`, `and()`, `or()` - Logical operators
- `in()`, `notIn()` - List matching
- `like()`, `notLike()`, `orLike()`, `orNotLike()` - Pattern matching
- `exists()`, `notExists()` - Subquery existence
- `between()`, `notBetween()` - Range queries

### Transactions
- `$app.runInTransaction(fn)` - Atomic operations
- All-or-nothing execution
- Rollback on error
- Commit on success

### Record Access Methods
- `$app.findRecordById()` - Get by ID
- `$app.findRecordsByIds()` - Get multiple by IDs
- `$app.findFirstRecordByData()` - Find by field values
- `$app.findRecordsByFilter()` - Filter-based search
- `$app.save()` - Create or update record
- `$app.delete()` - Remove record
- `$app.expandRecord()` - Expand relations programmatically
- `$app.canAccessRecord()` - Check view rule access

---

## Email System

### Email Configuration
- SMTP server settings
- Host, port, credentials
- TLS configuration
- Authentication method
- Sender name and address

### Email Templates
- Password reset emails
- Email verification emails
- Email change confirmation
- OTP delivery emails
- Device login alerts
- Custom template support

### Email Operations
- Send email via `$app.newMail()`
- HTML and plain text support
- Attachment support
- Template rendering
- Variable substitution

### Email Hooks
- Intercept all email sending
- Modify email content
- Add custom logic
- Prevent email sending conditionally

### Test Email
- `POST /api/settings/test/email`
- Send test user email
- Template testing
- SMTP connection verification

### Production Recommendations
- Use external SMTP services
- Avoid internal `sendmail`
- Services: MailerSend, Brevo, SendGrid
- Better deliverability
- Email analytics

---

## Production Features

### Deployment Options

#### Minimal Deployment
- Single binary executable
- No external dependencies
- Completely portable
- Direct server upload
- Systemd service management (Linux)

#### Reverse Proxy
- NGINX, Apache, or Caddy
- Multiple application hosting
- Network controls
- SSL/TLS termination
- User IP proxy headers configuration

#### Docker Deployment
- Alpine-based minimal image
- Volume mount for `pb_data`
- Data persistence
- Container orchestration support

### Security Features

#### MFA for Superusers
- Multi-factor authentication
- Email-based OTP
- Enhanced admin security
- Required for production

#### Rate Limiting
- Built-in rate limiter
- Configurable rules
- IP or user-based
- API abuse prevention
- Dashboard configuration

#### Settings Encryption
- 32-character encryption key
- `--encryptionEnv` flag
- Encrypt SMTP passwords
- Encrypt S3 credentials
- Secure sensitive settings

#### Trusted Proxy Configuration
- Reverse proxy support
- Correct client IP detection
- `X-Real-IP`, `X-Forwarded-For` headers
- Leftmost IP usage

### Performance Optimizations

#### File Descriptors
- Increase system limits
- `ulimit -n 4096` or higher
- Concurrent realtime connections
- High-traffic applications

#### Memory Management
- `GOMEMLIMIT` environment variable
- Memory-constrained environments
- Garbage collection tuning

#### Connection Pooling
- Pre-warmed JavaScript runtimes
- Default: 15 runtime pool
- Adjustable via `--hooksPool` flag
- Performance parity with Go

### Health Monitoring
- `GET/HEAD /api/health`
- Server status check
- `canBackup` status
- Uptime monitoring
- Load balancer health checks

---

## SDK & Client Features

### Available SDKs
1. **JavaScript SDK**
   - Browser support
   - Node.js support
   - React Native support
2. **Dart SDK**
   - Web platform
   - Mobile (iOS/Android)
   - Desktop
   - CLI applications

### SDK Features

#### Global Instance Safety
- Single/global SDK instance
- Safe for application lifecycle
- Client-side optimized

#### Authentication
- Email/password authentication
- Superuser authentication
- Long-lived API keys
- Auto-refresh token handling
- Customizable refresh thresholds

#### Async Storage Support
- Custom persistence stores
- Mobile app state preservation
- AsyncAuthStore implementation
- Cross-session authentication

#### Realtime Capabilities
- Subscribe to collections
- Subscribe to records
- Auto-handle SSE complexity
- EventSource polyfill (React Native)

#### Platform-Specific Features

**React Native**
- FormData handling for uploads
- Object syntax: `{uri, type, name}`
- Android/iOS file upload support
- EventSource polyfill requirement

**Mobile Platforms**
- AsyncAuthStore for persistence
- App session state management
- Background reconnection

### SDK Operations
- All CRUD operations
- File upload/download
- Realtime subscriptions
- Authentication flows
- Collection management (admin)
- Settings management (admin)

---

## Custom Routing & Middleware

### Routing System
- Go's `net/http.ServeMux`
- Custom endpoint registration via `app.OnServe()`
- HTTP methods: GET, POST, PUT, PATCH, DELETE
- Path parameters: `{paramName}`
- Wildcards: `{paramName...}` for multi-segment
- Route groups with shared base paths

### Middleware System

#### Middleware Capabilities
- Request interception and filtering
- Global, group-level, or per-route registration
- Chain execution with `e.Next()`
- Selective removal with `Unbind(id)`

#### Built-in Middlewares
- `apis.RequireAuth()` - Require authentication
- Rate limiting middleware
- CORS handling
- `apis.BodyLimit()` - Request body size limits
- Gzip compression
- Activity logging
- Panic recovery

### Response Handling
- `e.JSON()` - JSON responses
- `e.String()` - Plain text
- `e.HTML()` - HTML markup
- `e.Stream()` - Streaming data
- `e.BadRequestError()` - 400 errors
- `e.NotFoundError()` - 404 errors
- Auto-sanitized error responses
- Full details in dashboard logs

---

## Database Migrations

### Migration System
- Built-in migration utility
- Version control for database structure
- Programmatic collection creation
- Application settings initialization
- Go function-based migrations
- One-time execution

### Migration Structure
- `.go` files embedded in executable
- `m.Register(upFunc, downFunc)` pattern
- `upFunc` - Upgrade operations
- `downFunc` - Optional downgrade operations

### Migration Commands
- `migrate create` - Generate blank migration
- `migrate up` - Apply unapplied migrations
- `migrate down [number]` - Revert migrations
- `migrate collections` - Snapshot current collections
- `migrate history-sync` - Clean migration history

### Migration Features
- Automatic execution on server start
- Raw SQL execution support
- Programmatic collection building
- Settings initialization
- Superuser creation
- Custom fields and access rules
- `Automigrate` option for development

### Migration History
- Internal `_migrations` table
- Applied migration tracking
- Clean up intermediate steps
- Production deployment preparation

---

## Additional Features

### View Collections Advanced
- Custom SQL SELECT statements
- JOIN support across collections
- Aggregation functions
- Computed fields
- Read-only data presentation
- No realtime events

### Batch Request Features
- Transactional create/update/upsert/delete
- Multiple records in single request
- All-or-nothing execution
- Explicit enabling required
- Configurable limits and timeouts

### GeoPoint & Spatial Queries
- Geographic coordinate storage
- `geoDistance()` function
- Haversine distance calculation
- Kilometer-based results
- Location-based filtering

### Field Validation
- Required fields
- Min/max values (numbers)
- Min/max length (text)
- Pattern matching (regex)
- Email format validation
- URL format validation
- Custom validation via hooks
- File type restrictions
- File size limits

### Indexes
- Single field indexes
- Composite indexes
- Unique constraints
- Performance optimization
- Back-relation behavior control

### TypeScript Support
- Ambient type declarations
- `pb_data/types.d.ts` generation
- Triple-slash directive reference
- Code completion in IDEs
- Type safety for extensions

### Console Commands
- Custom CLI commands via extensions
- `$app.rootCmd` access
- Cobra command framework
- Subcommand support
- Flag definitions

### Job Scheduling
- Cron-based scheduling in extensions
- Background task execution
- Periodic operations
- Cleanup tasks

### HTTP Requests (Extensions)
- Custom HTTP client
- External API calls
- Webhook dispatching
- Third-party integrations

### Logging (Extensions)
- Custom log messages
- Multiple log levels
- Structured logging
- Request correlation

### Template Rendering
- Email template system
- HTML template rendering
- Variable substitution
- Custom template functions

---

## Summary Statistics

**Total Features Documented**: 500+ individual features and capabilities

**API Endpoints**: 50+ REST endpoints

**Event Hooks**: 80+ lifecycle and request hooks

**Field Types**: 12 distinct field types with modifiers

**Collection Types**: 3 (Base, Auth, View)

**Authentication Methods**: 4 (Password, OAuth2, OTP, MFA)

**Storage Backends**: 3 (Local, S3, Azure)

**SDK Support**: 2 official SDKs (JavaScript, Dart)

**Extension Languages**: 2 (Go, JavaScript)

---

*This document represents a comprehensive feature inventory as of the reference platform's current version. Features are subject to updates and additions in future releases.*
