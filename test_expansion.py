"""Test script for relation expansion."""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@fastcms.dev"
ADMIN_PASSWORD = "Admin123!"

async def test_expansion():
    """Test relation expansion."""
    print("=" * 60)
    print("Testing Relation Expansion")
    print("=" * 60)
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        # 1. Login as admin
        print("\n[1/5] Logging in as admin...")
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
        
        # 2. Create collections
        print("\n[2/5] Creating test collections (authors, books)...")
        
        # Authors collection
        await client.post(
            "/api/v1/collections",
            json={
                "name": "test_authors",
                "type": "base",
                "schema": [
                    {"name": "name", "type": "text", "validation": {"required": True}}
                ]
            },
            headers=headers
        )
        
        # Books collection with relation
        await client.post(
            "/api/v1/collections",
            json={
                "name": "test_books",
                "type": "base",
                "schema": [
                    {"name": "title", "type": "text", "validation": {"required": True}},
                    {
                        "name": "author", 
                        "type": "relation", 
                        "relation": {
                            "collection": "test_authors",
                            "type": "one-to-many"
                        },
                        "validation": {"required": True}
                    }
                ]
            },
            headers=headers
        )
        print("✅ Collections created")
        
        # 3. Create records
        print("\n[3/5] Creating records...")
        
        # Create Author
        author_res = await client.post(
            "/api/v1/test_authors/records",
            json={"data": {"name": "J.K. Rowling"}},
            headers=headers
        )
        author_id = author_res.json()["id"]
        print(f"✅ Created author: {author_id}")
        
        # Create Book
        book_res = await client.post(
            "/api/v1/test_books/records",
            json={"data": {"title": "Harry Potter", "author": author_id}},
            headers=headers
        )
        book_id = book_res.json()["id"]
        print(f"✅ Created book: {book_id}")
        
        # 4. Test Expansion (Get One)
        print("\n[4/5] Testing Expansion (Get One)...")
        res = await client.get(
            f"/api/v1/test_books/records/{book_id}?expand=author",
            headers=headers
        )
        
        data = res.json()
        if "expand" in data and "author" in data["expand"]:
            expanded_author = data["expand"]["author"]
            print(f"✅ Expansion successful!")
            print(f"   Book: {data['data']['title']}")
            print(f"   Expanded Author: {expanded_author['data']['name']}")
        else:
            print(f"❌ Expansion failed: {data}")
            
        # 5. Test Expansion (List)
        print("\n[5/5] Testing Expansion (List)...")
        res = await client.get(
            "/api/v1/test_books/records?expand=author",
            headers=headers
        )
        
        data = res.json()
        item = data["items"][0]
        if "expand" in item and "author" in item["expand"]:
            print(f"✅ List Expansion successful!")
        else:
            print(f"❌ List Expansion failed: {item}")
            
        # Cleanup
        print("\nCleaning up...")
        await client.delete("/api/v1/collections/test_books", headers=headers)
        await client.delete("/api/v1/collections/test_authors", headers=headers)
        print("✅ Cleanup complete")

if __name__ == "__main__":
    asyncio.run(test_expansion())
