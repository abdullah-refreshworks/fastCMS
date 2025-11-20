"""
Seed script to populate FastCMS with test data.
Run with: python seed_data.py
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta
import random

BASE_URL = "http://localhost:8000"

# Admin credentials
ADMIN_EMAIL = "admin@fastcms.dev"
ADMIN_PASSWORD = "Admin123!"

async def seed_database():
    """Main seeding function."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        print("=" * 60)
        print("FastCMS Database Seeder")
        print("=" * 60)

        # Step 1: Create admin user via setup
        print("\n[1/5] Creating admin user...")
        token = await create_admin_user(client)
        if not token:
            print("Failed to create admin user or login")
            return

        headers = {"Authorization": f"Bearer {token}"}

        # Step 2: Create collections
        print("\n[2/5] Creating collections...")
        await create_collections(client, headers)

        # Step 3: Create sample users
        print("\n[3/5] Creating sample users...")
        await create_sample_users(client, headers)

        # Step 4: Create sample records
        print("\n[4/5] Creating sample records...")
        await create_sample_records(client, headers)

        # Step 5: Summary
        print("\n[5/5] Seeding complete!")
        print("=" * 60)
        print("\nAdmin credentials:")
        print(f"  Email: {ADMIN_EMAIL}")
        print(f"  Password: {ADMIN_PASSWORD}")
        print("\nAccess the admin panel at: http://localhost:8000/admin")
        print("=" * 60)


async def create_admin_user(client: httpx.AsyncClient) -> str | None:
    """Create admin user and return access token."""

    # First, try to use the setup endpoint
    setup_data = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
        "password_confirm": ADMIN_PASSWORD,
        "name": "Admin User"
    }

    # Try setup endpoint first (POST to /api/v1/setup)
    response = await client.post("/api/v1/setup", json=setup_data)

    if response.status_code == 200:
        data = response.json()
        print(f"  Created admin user: {ADMIN_EMAIL}")
        return data.get("token", {}).get("access_token")
    elif response.status_code == 400 and "already" in response.text.lower():
        print("  Admin user already exists, logging in...")
    else:
        print(f"  Setup response: {response.status_code} - {response.text[:200]}")

    # Try to login
    login_data = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }

    response = await client.post("/api/v1/auth/login", json=login_data)

    if response.status_code == 200:
        data = response.json()
        print(f"  Logged in as: {ADMIN_EMAIL}")
        return data.get("token", {}).get("access_token")
    else:
        print(f"  Login failed: {response.status_code} - {response.text[:200]}")
        return None


async def create_collections(client: httpx.AsyncClient, headers: dict):
    """Create sample collections."""

    collections = [
        # Blog posts collection
        {
            "name": "posts",
            "type": "base",
            "schema": [
                {
                    "name": "title",
                    "type": "text",
                    "validation": {"required": True, "min": 1, "max": 200}
                },
                {
                    "name": "content",
                    "type": "text",
                    "validation": {"required": True}
                },
                {
                    "name": "author",
                    "type": "text",
                    "validation": {"required": True}
                },
                {
                    "name": "published",
                    "type": "bool",
                    "validation": {"required": False}
                },
                {
                    "name": "tags",
                    "type": "json",
                    "validation": {"required": False}
                },
                {
                    "name": "views",
                    "type": "number",
                    "validation": {"required": False, "min": 0}
                }
            ],
            "options": {},
            "list_rule": None,
            "view_rule": None,
            "create_rule": None,
            "update_rule": None,
            "delete_rule": None
        },
        # Products collection
        {
            "name": "products",
            "type": "base",
            "schema": [
                {
                    "name": "name",
                    "type": "text",
                    "validation": {"required": True, "min": 1, "max": 200}
                },
                {
                    "name": "description",
                    "type": "text",
                    "validation": {"required": False}
                },
                {
                    "name": "price",
                    "type": "number",
                    "validation": {"required": True, "min": 0}
                },
                {
                    "name": "stock",
                    "type": "number",
                    "validation": {"required": True, "min": 0}
                },
                {
                    "name": "category",
                    "type": "select",
                    "options": {
                        "values": ["electronics", "clothing", "books", "home", "sports"]
                    },
                    "validation": {"required": True}
                },
                {
                    "name": "active",
                    "type": "bool",
                    "validation": {"required": False}
                },
                {
                    "name": "extra_info",
                    "type": "json",
                    "validation": {"required": False}
                }
            ],
            "options": {},
            "list_rule": None,
            "view_rule": None,
            "create_rule": "@request.auth.role = 'admin'",
            "update_rule": "@request.auth.role = 'admin'",
            "delete_rule": "@request.auth.role = 'admin'"
        },
        # Orders collection
        {
            "name": "orders",
            "type": "base",
            "schema": [
                {
                    "name": "customer_email",
                    "type": "email",
                    "validation": {"required": True}
                },
                {
                    "name": "customer_name",
                    "type": "text",
                    "validation": {"required": True}
                },
                {
                    "name": "items",
                    "type": "json",
                    "validation": {"required": True}
                },
                {
                    "name": "total",
                    "type": "number",
                    "validation": {"required": True, "min": 0}
                },
                {
                    "name": "status",
                    "type": "select",
                    "options": {
                        "values": ["pending", "processing", "shipped", "delivered", "cancelled"]
                    },
                    "validation": {"required": True}
                },
                {
                    "name": "notes",
                    "type": "text",
                    "validation": {"required": False}
                }
            ],
            "options": {},
            "list_rule": None,
            "view_rule": None,
            "create_rule": None,
            "update_rule": None,
            "delete_rule": None
        },
        # Tasks collection
        {
            "name": "tasks",
            "type": "base",
            "schema": [
                {
                    "name": "title",
                    "type": "text",
                    "validation": {"required": True, "min": 1, "max": 200}
                },
                {
                    "name": "description",
                    "type": "text",
                    "validation": {"required": False}
                },
                {
                    "name": "priority",
                    "type": "select",
                    "options": {
                        "values": ["low", "medium", "high", "urgent"]
                    },
                    "validation": {"required": True}
                },
                {
                    "name": "completed",
                    "type": "bool",
                    "validation": {"required": False}
                },
                {
                    "name": "due_date",
                    "type": "text",
                    "validation": {"required": False}
                },
                {
                    "name": "assignee",
                    "type": "text",
                    "validation": {"required": False}
                }
            ],
            "options": {},
            "list_rule": None,
            "view_rule": None,
            "create_rule": None,
            "update_rule": None,
            "delete_rule": None
        },
        # Contacts collection
        {
            "name": "contacts",
            "type": "base",
            "schema": [
                {
                    "name": "name",
                    "type": "text",
                    "validation": {"required": True}
                },
                {
                    "name": "email",
                    "type": "email",
                    "validation": {"required": True}
                },
                {
                    "name": "phone",
                    "type": "text",
                    "validation": {"required": False}
                },
                {
                    "name": "company",
                    "type": "text",
                    "validation": {"required": False}
                },
                {
                    "name": "notes",
                    "type": "text",
                    "validation": {"required": False}
                }
            ],
            "options": {},
            "list_rule": None,
            "view_rule": None,
            "create_rule": None,
            "update_rule": None,
            "delete_rule": None
        },
        # Auth collection - independent customer authentication
        {
            "name": "customers",
            "type": "auth",
            "schema": [
                {
                    "name": "company",
                    "type": "text",
                    "validation": {"required": False}
                },
                {
                    "name": "phone",
                    "type": "text",
                    "validation": {"required": False}
                },
                {
                    "name": "membership_level",
                    "type": "select",
                    "options": {
                        "values": ["bronze", "silver", "gold", "platinum"]
                    },
                    "validation": {"required": False}
                },
                {
                    "name": "total_purchases",
                    "type": "number",
                    "validation": {"required": False, "min": 0}
                }
            ],
            "options": {
                "allowEmailAuth": True,
                "allowOAuth2Auth": False,
                "requireEmail": True,
                "minPasswordLength": 8
            },
            "list_rule": None,
            "view_rule": None,
            "create_rule": None,
            "update_rule": None,
            "delete_rule": None
        },
        # View collection - product statistics aggregation
        {
            "name": "product_stats",
            "type": "view",
            "schema": [
                {
                    "name": "category",
                    "type": "text",
                    "validation": {"required": True}
                },
                {
                    "name": "product_count",
                    "type": "number",
                    "validation": {"required": True}
                },
                {
                    "name": "total_stock",
                    "type": "number",
                    "validation": {"required": True}
                },
                {
                    "name": "avg_price",
                    "type": "number",
                    "validation": {"required": True}
                }
            ],
            "options": {
                "query": {
                    "source": "products",
                    "select": [
                        {"field": "category", "alias": "category"},
                        {"field": "id", "alias": "product_count", "aggregation": {"function": "COUNT", "field": "id", "alias": "product_count"}},
                        {"field": "stock", "alias": "total_stock", "aggregation": {"function": "SUM", "field": "stock", "alias": "total_stock"}},
                        {"field": "price", "alias": "avg_price", "aggregation": {"function": "AVG", "field": "price", "alias": "avg_price"}}
                    ],
                    "group_by": ["category"]
                },
                "cache_ttl": 300
            },
            "list_rule": None,
            "view_rule": None,
            "create_rule": None,
            "update_rule": None,
            "delete_rule": None
        }
    ]

    for collection in collections:
        response = await client.post(
            "/api/v1/collections",
            json=collection,
            headers=headers
        )

        if response.status_code in [200, 201]:
            print(f"  Created collection: {collection['name']}")
        elif response.status_code == 409:
            print(f"  Collection already exists: {collection['name']}")
        else:
            print(f"  Failed to create {collection['name']}: {response.status_code} - {response.text[:100]}")


async def create_sample_users(client: httpx.AsyncClient, headers: dict):
    """Create sample users."""

    # Users with different roles to demonstrate the system
    users = [
        # Regular users - can only access data based on collection rules
        {
            "data": {
                "email": "john@example.com",
                "password": "Password123!",
                "password_confirm": "Password123!",
                "name": "John Doe"
            },
            "role": "user",
            "description": "Regular user - frontend app user"
        },
        {
            "data": {
                "email": "jane@example.com",
                "password": "Password123!",
                "password_confirm": "Password123!",
                "name": "Jane Smith"
            },
            "role": "user",
            "description": "Regular user - can access API with limited permissions"
        },
        # Admin users - full system access
        {
            "data": {
                "email": "manager@example.com",
                "password": "Manager123!",
                "password_confirm": "Manager123!",
                "name": "Sarah Manager"
            },
            "role": "admin",
            "description": "Admin user - full access to admin panel and all data"
        },
        {
            "data": {
                "email": "developer@example.com",
                "password": "Developer123!",
                "password_confirm": "Developer123!",
                "name": "Mike Developer"
            },
            "role": "admin",
            "description": "Admin user - can manage collections and users"
        }
    ]

    for user in users:
        # Role is passed as query parameter, not in body
        response = await client.post(
            f"/api/v1/admin/users?role={user['role']}",
            json=user["data"],
            headers=headers
        )

        if response.status_code in [200, 201]:
            print(f"  Created {user['role']}: {user['data']['email']} - {user['description']}")
        elif response.status_code == 409 or "already" in response.text.lower():
            print(f"  User already exists: {user['data']['email']}")
        else:
            print(f"  Failed to create {user['data']['email']}: {response.status_code} - {response.text[:100]}")


async def create_sample_records(client: httpx.AsyncClient, headers: dict):
    """Create sample records for each collection."""

    # Sample posts
    posts = [
        {
            "title": "Getting Started with FastCMS",
            "content": "FastCMS is a powerful, AI-native backend-as-a-service built with FastAPI. It provides a complete solution for building modern applications with features like collections, authentication, file storage, and more.",
            "author": "Admin",
            "published": True,
            "tags": ["fastcms", "tutorial", "getting-started"],
            "views": 150
        },
        {
            "title": "Building RESTful APIs",
            "content": "Learn how to build robust RESTful APIs using FastCMS. This guide covers creating collections, defining schemas, and implementing CRUD operations.",
            "author": "John Doe",
            "published": True,
            "tags": ["api", "rest", "tutorial"],
            "views": 89
        },
        {
            "title": "Authentication Best Practices",
            "content": "Security is crucial for any application. This post covers authentication best practices including JWT tokens, password hashing, and access control rules.",
            "author": "Jane Smith",
            "published": True,
            "tags": ["security", "authentication", "jwt"],
            "views": 234
        },
        {
            "title": "Draft: Upcoming Features",
            "content": "We're working on exciting new features including AI-powered content generation, advanced search capabilities, and more.",
            "author": "Admin",
            "published": False,
            "tags": ["roadmap", "features"],
            "views": 0
        },
        {
            "title": "Working with File Uploads",
            "content": "FastCMS makes file handling easy. Learn how to upload, manage, and serve files with automatic thumbnail generation and S3 support.",
            "author": "Bob Wilson",
            "published": True,
            "tags": ["files", "uploads", "storage"],
            "views": 67
        }
    ]

    # Sample products
    products = [
        {
            "name": "Wireless Bluetooth Headphones",
            "description": "Premium noise-canceling headphones with 30-hour battery life",
            "price": 199.99,
            "stock": 50,
            "category": "electronics",
            "active": True,
            "extra_info": {"brand": "AudioPro", "color": "black"}
        },
        {
            "name": "Running Shoes",
            "description": "Lightweight running shoes with advanced cushioning",
            "price": 129.99,
            "stock": 100,
            "category": "sports",
            "active": True,
            "extra_info": {"brand": "SpeedRun", "sizes": ["8", "9", "10", "11"]}
        },
        {
            "name": "Python Programming Book",
            "description": "Comprehensive guide to Python programming for beginners to advanced",
            "price": 49.99,
            "stock": 200,
            "category": "books",
            "active": True,
            "extra_info": {"author": "Tech Writer", "pages": 500}
        },
        {
            "name": "Smart Watch",
            "description": "Fitness tracker with heart rate monitor and GPS",
            "price": 299.99,
            "stock": 25,
            "category": "electronics",
            "active": True,
            "extra_info": {"brand": "FitTech", "waterproof": True}
        },
        {
            "name": "Cotton T-Shirt",
            "description": "Comfortable 100% cotton t-shirt",
            "price": 24.99,
            "stock": 500,
            "category": "clothing",
            "active": True,
            "extra_info": {"material": "cotton", "colors": ["white", "black", "blue"]}
        },
        {
            "name": "Desk Lamp",
            "description": "LED desk lamp with adjustable brightness",
            "price": 45.99,
            "stock": 75,
            "category": "home",
            "active": True,
            "extra_info": {"wattage": 12, "adjustable": True}
        },
        {
            "name": "Yoga Mat",
            "description": "Non-slip yoga mat with carrying strap",
            "price": 35.99,
            "stock": 150,
            "category": "sports",
            "active": True,
            "extra_info": {"thickness": "6mm", "material": "TPE"}
        },
        {
            "name": "Vintage Camera (Discontinued)",
            "description": "Classic film camera for photography enthusiasts",
            "price": 399.99,
            "stock": 0,
            "category": "electronics",
            "active": False,
            "extra_info": {"brand": "RetroShot", "type": "film"}
        }
    ]

    # Sample orders
    orders = [
        {
            "customer_email": "john@example.com",
            "customer_name": "John Doe",
            "items": [
                {"product": "Wireless Bluetooth Headphones", "quantity": 1, "price": 199.99},
                {"product": "Python Programming Book", "quantity": 2, "price": 49.99}
            ],
            "total": 299.97,
            "status": "delivered",
            "notes": "Leave at door"
        },
        {
            "customer_email": "jane@example.com",
            "customer_name": "Jane Smith",
            "items": [
                {"product": "Running Shoes", "quantity": 1, "price": 129.99},
                {"product": "Yoga Mat", "quantity": 1, "price": 35.99}
            ],
            "total": 165.98,
            "status": "shipped",
            "notes": ""
        },
        {
            "customer_email": "bob@example.com",
            "customer_name": "Bob Wilson",
            "items": [
                {"product": "Smart Watch", "quantity": 1, "price": 299.99}
            ],
            "total": 299.99,
            "status": "processing",
            "notes": "Gift wrap please"
        },
        {
            "customer_email": "alice@example.com",
            "customer_name": "Alice Brown",
            "items": [
                {"product": "Cotton T-Shirt", "quantity": 3, "price": 24.99},
                {"product": "Desk Lamp", "quantity": 1, "price": 45.99}
            ],
            "total": 120.96,
            "status": "pending",
            "notes": ""
        }
    ]

    # Sample tasks
    tasks = [
        {
            "title": "Review Q4 reports",
            "description": "Analyze quarterly financial reports and prepare summary",
            "priority": "high",
            "completed": False,
            "due_date": (datetime.now() + timedelta(days=3)).isoformat(),
            "assignee": "John Doe"
        },
        {
            "title": "Update documentation",
            "description": "Update API documentation with new endpoints",
            "priority": "medium",
            "completed": True,
            "due_date": (datetime.now() - timedelta(days=1)).isoformat(),
            "assignee": "Jane Smith"
        },
        {
            "title": "Fix login bug",
            "description": "Users unable to login with special characters in password",
            "priority": "urgent",
            "completed": False,
            "due_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "assignee": "Bob Wilson"
        },
        {
            "title": "Design new landing page",
            "description": "Create mockups for the new product landing page",
            "priority": "low",
            "completed": False,
            "due_date": (datetime.now() + timedelta(days=14)).isoformat(),
            "assignee": "Alice Brown"
        },
        {
            "title": "Database optimization",
            "description": "Optimize slow queries and add missing indexes",
            "priority": "medium",
            "completed": False,
            "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "assignee": "Admin"
        }
    ]

    # Sample contacts
    contacts = [
        {
            "name": "Michael Johnson",
            "email": "michael@techcorp.com",
            "phone": "+1-555-0101",
            "company": "TechCorp Inc.",
            "notes": "Met at conference 2024"
        },
        {
            "name": "Sarah Williams",
            "email": "sarah@startup.io",
            "phone": "+1-555-0102",
            "company": "StartUp.io",
            "notes": "Interested in partnership"
        },
        {
            "name": "David Lee",
            "email": "david@enterprise.com",
            "phone": "+1-555-0103",
            "company": "Enterprise Solutions",
            "notes": "Enterprise customer prospect"
        },
        {
            "name": "Emily Chen",
            "email": "emily@design.co",
            "phone": "+1-555-0104",
            "company": "Design Co",
            "notes": "UI/UX consultant"
        }
    ]

    # Create records for each collection
    collections_data = [
        ("posts", posts),
        ("products", products),
        ("orders", orders),
        ("tasks", tasks),
        ("contacts", contacts)
    ]

    for collection_name, records in collections_data:
        created = 0
        for record in records:
            # Wrap record in 'data' field as expected by RecordCreate schema
            response = await client.post(
                f"/api/v1/{collection_name}/records",
                json={"data": record},
                headers=headers
            )

            if response.status_code in [200, 201]:
                created += 1
            else:
                print(f"    Failed to create record in {collection_name}: {response.status_code}")

        print(f"  Created {created}/{len(records)} records in '{collection_name}'")

    # Create sample customers in auth collection via register endpoint
    customers = [
        {
            "email": "customer1@example.com",
            "password": "Customer123!",
            "company": "Acme Corp",
            "phone": "+1-555-1001",
            "membership_level": "gold",
            "total_purchases": 1500.00
        },
        {
            "email": "customer2@example.com",
            "password": "Customer123!",
            "company": "Tech Solutions",
            "phone": "+1-555-1002",
            "membership_level": "silver",
            "total_purchases": 750.00
        },
        {
            "email": "customer3@example.com",
            "password": "Customer123!",
            "company": "StartUp Inc",
            "phone": "+1-555-1003",
            "membership_level": "bronze",
            "total_purchases": 250.00
        }
    ]

    created = 0
    for customer in customers:
        response = await client.post(
            "/api/v1/customers/auth/register",
            json=customer
        )

        if response.status_code in [200, 201]:
            created += 1
        else:
            print(f"    Failed to register customer: {response.status_code} - {response.text[:100]}")

    print(f"  Registered {created}/{len(customers)} customers in 'customers' (auth collection)")


if __name__ == "__main__":
    asyncio.run(seed_database())
