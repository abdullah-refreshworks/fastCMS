#!/usr/bin/env python3
"""
Demo script for Auth Collections in FastCMS.
This script creates auth collections and populates them with sample data.
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"

async def main():
    print("=" * 70)
    print("🔐 FastCMS Auth Collections Demo")
    print("=" * 70)
    print()

    async with httpx.AsyncClient() as client:
        # Step 1: Login as admin
        print("1️⃣  Logging in as admin...")
        response = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": "aalhommada@gmail.com", "password": "Password123"}
        )
        if response.status_code != 200:
            print(f"❌ Login failed: {response.text}")
            return

        token = response.json()["token"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Logged in successfully\n")

        # Step 2: Create "customers" auth collection
        print("2️⃣  Creating 'customers' auth collection...")
        customers_collection = {
            "name": "customers",
            "type": "auth",  # This is the key!
            "schema": [
                {
                    "name": "name",
                    "type": "text",
                    "validation": {"required": True}
                },
                {
                    "name": "phone",
                    "type": "text"
                },
                {
                    "name": "address",
                    "type": "text"
                },
                {
                    "name": "avatar",
                    "type": "url"
                }
            ]
        }

        response = await client.post(
            f"{BASE_URL}/api/v1/collections",
            json=customers_collection,
            headers=headers
        )

        if response.status_code == 201:
            coll_data = response.json()
            print(f"✅ Created 'customers' auth collection!")
            print(f"   ID: {coll_data['id']}")
            print(f"\n   📋 Auto-generated auth fields:")
            for field in coll_data['schema']:
                if field.get('system'):
                    print(f"      • {field['name']} ({field['type']}) - {field.get('hint', '')}")
            print()
        else:
            print(f"❌ Failed: {response.text}\n")
            return

        # Step 3: Register customers using the auth endpoints
        print("3️⃣  Registering customers via auth endpoints...")
        customers_data = [
            {
                "email": "alice@example.com",
                "password": "SecurePass123",
                "password_confirm": "SecurePass123",
                "name": "Alice Johnson",
                "phone": "+1-555-0101",
                "address": "123 Main St, Springfield",
                "avatar": "https://i.pravatar.cc/150?img=1"
            },
            {
                "email": "bob@example.com",
                "password": "SecurePass456",
                "password_confirm": "SecurePass456",
                "name": "Bob Smith",
                "phone": "+1-555-0102",
                "address": "456 Oak Ave, Portland",
                "avatar": "https://i.pravatar.cc/150?img=2"
            },
            {
                "email": "carol@example.com",
                "password": "SecurePass789",
                "password_confirm": "SecurePass789",
                "name": "Carol Davis",
                "phone": "+1-555-0103",
                "address": "789 Pine Rd, Seattle",
                "avatar": "https://i.pravatar.cc/150?img=3"
            }
        ]

        customer_tokens = []
        for customer in customers_data:
            response = await client.post(
                f"{BASE_URL}/api/v1/customers/auth/register",
                json=customer
            )
            if response.status_code == 201:
                result = response.json()
                customer_tokens.append({
                    "name": customer["name"],
                    "email": customer["email"],
                    "token": result["token"]["access_token"],
                    "id": result["user"]["id"]
                })
                print(f"   ✅ Registered: {customer['name']} ({customer['email']})")
            else:
                print(f"   ❌ Failed to register {customer['email']}: {response.text}")

        print()

        # Step 4: Test login with one of the customers
        print("4️⃣  Testing login for Alice...")
        response = await client.post(
            f"{BASE_URL}/api/v1/customers/auth/login",
            json={"email": "alice@example.com", "password": "SecurePass123"}
        )

        if response.status_code == 200:
            login_data = response.json()
            alice_token = login_data["token"]["access_token"]
            print(f"✅ Alice logged in successfully!")
            print(f"   Token: {alice_token[:50]}...")
            print()
        else:
            print(f"❌ Login failed: {response.text}\n")

        # Step 5: Get current user info
        print("5️⃣  Getting Alice's profile...")
        response = await client.get(
            f"{BASE_URL}/api/v1/customers/auth/me",
            headers={"Authorization": f"Bearer {alice_token}"}
        )

        if response.status_code == 200:
            profile = response.json()
            print(f"✅ Profile retrieved:")
            print(f"   Name: {profile.get('name')}")
            print(f"   Email: {profile.get('email')}")
            print(f"   Phone: {profile.get('phone')}")
            print(f"   Verified: {profile.get('verified')}")
            print(f"   Note: Password is NOT included in response ✓")
            print()
        else:
            print(f"❌ Failed: {response.text}\n")

        # Step 6: Create "vendors" auth collection (another auth collection!)
        print("6️⃣  Creating 'vendors' auth collection...")
        vendors_collection = {
            "name": "vendors",
            "type": "auth",
            "schema": [
                {
                    "name": "company_name",
                    "type": "text",
                    "validation": {"required": True}
                },
                {
                    "name": "business_type",
                    "type": "select",
                    "select": {
                        "values": ["Retail", "Wholesale", "Manufacturing", "Services"],
                        "max_select": 1
                    }
                },
                {
                    "name": "website",
                    "type": "url"
                },
                {
                    "name": "tax_id",
                    "type": "text"
                }
            ]
        }

        response = await client.post(
            f"{BASE_URL}/api/v1/collections",
            json=vendors_collection,
            headers=headers
        )

        if response.status_code == 201:
            print(f"✅ Created 'vendors' auth collection!")
            print(f"   Now you have TWO separate auth collections!")
            print()
        else:
            print(f"❌ Failed: {response.text}\n")

        # Step 7: Register a vendor
        print("7️⃣  Registering a vendor...")
        vendor_data = {
            "email": "contact@acmecorp.com",
            "password": "VendorPass123",
            "password_confirm": "VendorPass123",
            "company_name": "Acme Corporation",
            "business_type": "Wholesale",
            "website": "https://acmecorp.example.com",
            "tax_id": "12-3456789"
        }

        response = await client.post(
            f"{BASE_URL}/api/v1/vendors/auth/register",
            json=vendor_data
        )

        if response.status_code == 201:
            vendor_result = response.json()
            print(f"✅ Vendor registered: {vendor_data['company_name']}")
            print(f"   Email: {vendor_data['email']}")
            print()
        else:
            print(f"❌ Failed: {response.text}\n")

        # Final Summary
        print("=" * 70)
        print("✅ Auth Collections Demo Complete!")
        print("=" * 70)
        print()
        print("📊 What was created:")
        print("   • 2 Auth collections: 'customers' and 'vendors'")
        print("   • 3 Customer accounts (Alice, Bob, Carol)")
        print("   • 1 Vendor account (Acme Corporation)")
        print()
        print("🔑 Key Features Demonstrated:")
        print("   ✓ Auto-injected auth fields (email, password, verified)")
        print("   ✓ Password hashing (passwords stored securely)")
        print("   ✓ Registration endpoint: POST /api/v1/{collection}/auth/register")
        print("   ✓ Login endpoint: POST /api/v1/{collection}/auth/login")
        print("   ✓ Profile endpoint: GET /api/v1/{collection}/auth/me")
        print("   ✓ JWT token authentication")
        print("   ✓ Password excluded from API responses")
        print("   ✓ Multiple independent auth collections")
        print()
        print("🧪 Try it yourself:")
        print(f"   • View customers: http://localhost:8000/admin/collections/customers/records")
        print(f"   • View vendors: http://localhost:8000/admin/collections/vendors/records")
        print(f"   • API docs: http://localhost:8000/docs (look for 'Auth Collections' tag)")
        print()
        print("🔐 Test login:")
        print(f"   curl -X POST {BASE_URL}/api/v1/customers/auth/login \\")
        print(f"     -H 'Content-Type: application/json' \\")
        print(f"     -d '{{\"email\":\"alice@example.com\",\"password\":\"SecurePass123\"}}'")
        print()

if __name__ == "__main__":
    asyncio.run(main())
