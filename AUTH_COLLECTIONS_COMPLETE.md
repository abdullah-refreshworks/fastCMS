# ✅ Auth Collections - FULLY IMPLEMENTED!

## 🎉 What's New

Auth collections are now **fully implemented** in FastCMS! You can create multiple independent authentication systems, each with its own user base.

---

## 🔑 What Are Auth Collections?

Auth collections are special collections that provide built-in authentication features:

- **Automatic auth fields**: `email`, `password`, `verified`, `email_visibility`
- **Password hashing**: Passwords are automatically hashed with bcrypt
- **JWT authentication**: Built-in login/register with token generation
- **Secure by default**: Passwords never exposed in API responses
- **Multiple auth systems**: Create separate auth for customers, vendors, admins, etc.

---

## 📚 How to Create an Auth Collection

### Via Admin UI:

1. Go to **Collections** → **Create Collection**
2. Enter collection name (e.g., `customers`)
3. Select type: **"Auth"**
4. Add custom fields (name, phone, address, etc.)
5. Click **Create Collection**

**Auto-generated fields:**
- ✅ `email` (unique, required)
- ✅ `password` (hashed, hidden, required)
- ✅ `verified` (boolean)
- ✅ `email_visibility` (boolean)

### Via API:

```bash
curl -X POST http://localhost:8000/api/v1/collections \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "customers",
    "type": "auth",
    "schema": [
      {"name": "name", "type": "text", "validation": {"required": true}},
      {"name": "phone", "type": "text"},
      {"name": "address", "type": "text"}
    ]
  }'
```

---

## 🚀 Authentication Endpoints

Once you create an auth collection named `customers`, you automatically get:

### 1. **Register** - `POST /api/v1/customers/auth/register`

```bash
curl -X POST http://localhost:8000/api/v1/customers/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "SecurePass123",
    "password_confirm": "SecurePass123",
    "name": "Alice Johnson",
    "phone": "+1-555-0101"
  }'
```

Response:
```json
{
  "user": {
    "id": "uuid-here",
    "email": "alice@example.com",
    "name": "Alice Johnson",
    "phone": "+1-555-0101",
    "verified": false,
    "email_visibility": true
    // password is NOT included!
  },
  "token": {
    "access_token": "eyJhbGc...",
    "token_type": "bearer"
  }
}
```

### 2. **Login** - `POST /api/v1/customers/auth/login`

```bash
curl -X POST http://localhost:8000/api/v1/customers/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "SecurePass123"
  }'
```

Response:
```json
{
  "user": {...},
  "token": {
    "access_token": "eyJhbGc...",
    "token_type": "bearer"
  }
}
```

### 3. **Get Current User** - `GET /api/v1/customers/auth/me`

```bash
curl -X GET http://localhost:8000/api/v1/customers/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. **Refresh Token** - `POST /api/v1/customers/auth/refresh`

```bash
curl -X POST http://localhost:8000/api/v1/customers/auth/refresh \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 💡 Use Cases

### 1. **E-commerce Platform**

```
• customers (auth) - Customer accounts
• vendors (auth) - Seller accounts
• admins (auth) - Admin panel users
```

Each has separate authentication and can't cross-login!

### 2. **Multi-tenant SaaS**

```
• organizations (auth) - Company accounts
• team_members (auth) - Individual users
```

### 3. **Social Platform**

```
• users (auth) - Regular users
• moderators (auth) - Moderation team
• creators (auth) - Content creators
```

---

## 🔐 Security Features

✅ **Password Hashing**: Automatic bcrypt hashing
✅ **Hidden Passwords**: Never returned in API responses
✅ **JWT Tokens**: Secure token-based authentication
✅ **Email Uniqueness**: Automatic unique constraint
✅ **Verified Flag**: Track email verification status
✅ **Separate Auth**: Each collection has independent authentication

---

## 📊 Demo Data

Run the demo script to see it in action:

```bash
python demo_auth_collections.py
```

This creates:
- **customers** auth collection with 3 users
- **vendors** auth collection with 1 vendor
- Demonstrates register, login, and profile endpoints

---

## 🎯 Example: Customer & Vendor Auth

### Step 1: Create Collections

```python
# Customers auth collection
{
  "name": "customers",
  "type": "auth",
  "schema": [
    {"name": "name", "type": "text"},
    {"name": "shipping_address", "type": "text"},
    {"name": "phone", "type": "text"}
  ]
}

# Vendors auth collection
{
  "name": "vendors",
  "type": "auth",
  "schema": [
    {"name": "company_name", "type": "text"},
    {"name": "business_type", "type": "select", "select": {...}},
    {"name": "tax_id", "type": "text"}
  ]
}
```

### Step 2: Register Users

**Customer registration:**
```bash
POST /api/v1/customers/auth/register
{
  "email": "customer@example.com",
  "password": "pass123",
  "name": "John Doe"
}
```

**Vendor registration:**
```bash
POST /api/v1/vendors/auth/register
{
  "email": "vendor@example.com",
  "password": "pass123",
  "company_name": "Acme Corp"
}
```

### Step 3: Login

Each collection has its own login:
- Customers: `POST /api/v1/customers/auth/login`
- Vendors: `POST /api/v1/vendors/auth/login`

Tokens are scoped to the collection!

---

## 🆚 Auth vs Base Collections

| Feature | Base | Auth |
|---------|------|------|
| **Purpose** | General data | User authentication |
| **Auto Fields** | None | email, password, verified, email_visibility |
| **Password** | Manual | Auto-hashed |
| **Auth Endpoints** | No | Yes (`/auth/login`, `/auth/register`) |
| **JWT Tokens** | No | Yes |
| **Use For** | Posts, products, etc. | Users, customers, vendors |

---

## 📖 API Documentation

Visit **http://localhost:8000/docs** and look for the **"Auth Collections"** tag to see all available endpoints with interactive testing!

---

## 🎨 Admin UI

View your auth collection users in the admin panel:
- `http://localhost:8000/admin/collections/customers/records`
- `http://localhost:8000/admin/collections/vendors/records`

**Note**: Passwords will show as hashed values starting with `$2b$`

---

## ✨ What Makes This Special?

1. **Multiple Auth Systems**: Not limited to one "users" table
2. **Auto-Configuration**: Auth fields injected automatically
3. **Secure by Default**: Passwords hashed, never exposed
4. **Standard Endpoints**: Familiar REST API pattern
5. **JWT Integration**: Works with existing auth infrastructure
6. **Flexible Schema**: Add any custom fields you need

---

## 🚦 Current Status

**✅ FULLY IMPLEMENTED:**
- Auth collection creation
- Auto-injected auth fields
- Password hashing
- Registration endpoint
- Login endpoint
- Profile endpoint
- Token refresh
- Multiple independent auth collections

**🔜 Coming Soon:**
- Email verification flow
- Password reset
- OAuth integration for auth collections
- Two-factor authentication

---

## 🧪 Quick Test

```bash
# 1. Create auth collection
curl -X POST http://localhost:8000/api/v1/collections \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{"name":"users","type":"auth","schema":[]}'

# 2. Register
curl -X POST http://localhost:8000/api/v1/users/auth/register \
  -d '{"email":"test@example.com","password":"test123","password_confirm":"test123"}'

# 3. Login
curl -X POST http://localhost:8000/api/v1/users/auth/login \
  -d '{"email":"test@example.com","password":"test123"}'
```

---

## 🎉 Conclusion

Auth collections transform FastCMS into a **multi-tenant authentication platform**. You can now build:
- Multi-sided marketplaces
- SaaS platforms
- Social networks
- Any app needing multiple user types

Each with **independent**, **secure** authentication! 🔐
