"""Test script for Advanced API Rules."""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@fastcms.dev")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin123!")

async def test_api_rules():
    """Test API rules enforcement."""
    print("=" * 60)
    print("Testing Advanced API Rules")
    print("=" * 60)
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        # 1. Login as admin
        print("\n[1/4] Logging in as admin...")
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return
        
        token = login_response.json()["token"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Logged in successfully")
        
        # 2. Create collection with data rule
        print("\n[2/4] Creating collection with data rule (@request.data.status = 'active')...")
        
        await client.post(
            "/api/v1/collections",
            json={
                "name": "test_rules",
                "type": "base",
                "schema": [
                    {"name": "title", "type": "text", "validation": {"required": True}},
                    {"name": "status", "type": "text", "validation": {"required": True}}
                ],
                "create_rule": "@request.data.status = 'active'"
            },
            headers=headers
        )
        print("✅ Collection created")
        
        # 3. Test Rule Failure
        print("\n[3/4] Testing Rule Failure (status='inactive')...")
        fail_res = await client.post(
            "/api/v1/test_rules/records",
            json={"data": {"title": "Bad Post", "status": "inactive"}},
            headers=headers
        )
        
        if fail_res.status_code == 403:
            print(f"✅ Request correctly denied: {fail_res.status_code}")
        else:
            print(f"❌ Request should have failed but got: {fail_res.status_code} - {fail_res.text}")
            
        # 4. Test Rule Success
        print("\n[4/4] Testing Rule Success (status='active')...")
        success_res = await client.post(
            "/api/v1/test_rules/records",
            json={"data": {"title": "Good Post", "status": "active"}},
            headers=headers
        )
        
        if success_res.status_code == 201:
            print(f"✅ Request succeeded: {success_res.json()['id']}")
        else:
            print(f"❌ Request failed: {success_res.status_code} - {success_res.text}")
            
        # Cleanup
        print("\nCleaning up...")
        await client.delete("/api/v1/collections/test_rules", headers=headers)
        print("✅ Cleanup complete")

if __name__ == "__main__":
    asyncio.run(test_api_rules())
