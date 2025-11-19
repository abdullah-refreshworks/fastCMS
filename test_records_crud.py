#!/usr/bin/env python3
"""
End-to-end test script for FastCMS record CRUD operations.
Tests creating collections, creating records, updating, and deleting.
"""

import asyncio
import json
import sys
from datetime import datetime

import httpx


BASE_URL = "http://localhost:8000/api/v1"
ADMIN_EMAIL = "testuser@example.com"
ADMIN_PASSWORD = "testpassword123"

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def log_success(message: str):
    print(f"{GREEN}✓ {message}{RESET}")


def log_error(message: str):
    print(f"{RED}✗ {message}{RESET}")


def log_info(message: str):
    print(f"{BLUE}ℹ {message}{RESET}")


def log_warning(message: str):
    print(f"{YELLOW}⚠ {message}{RESET}")


async def login(client: httpx.AsyncClient) -> str:
    """Login and return access token."""
    log_info("Logging in as admin...")
    response = await client.post(
        f"{BASE_URL}/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )

    if response.status_code != 200:
        log_error(f"Login failed: {response.text}")
        sys.exit(1)

    data = response.json()
    log_success(f"Logged in as {ADMIN_EMAIL}")
    # Response structure: {"user": {...}, "token": {"access_token": "...", ...}}
    return data["token"]["access_token"]


async def create_test_collection(client: httpx.AsyncClient, token: str, collection_name: str) -> dict:
    """Create a test collection."""
    log_info(f"Creating test collection '{collection_name}'...")

    collection_data = {
        "name": collection_name,
        "type": "base",
        "schema": [
            {
                "name": "title",
                "type": "text",
                "validation": {
                    "required": True,
                    "min_length": 3,
                    "max_length": 100
                }
            },
            {
                "name": "content",
                "type": "editor",
                "validation": {
                    "required": False
                }
            },
            {
                "name": "views",
                "type": "number",
                "validation": {
                    "required": False,
                    "min": 0
                }
            },
            {
                "name": "published",
                "type": "bool",
                "validation": {
                    "required": False
                }
            },
            {
                "name": "author_email",
                "type": "email",
                "validation": {
                    "required": False
                }
            },
            {
                "name": "extra_data",
                "type": "json",
                "validation": {
                    "required": False
                }
            }
        ]
    }

    response = await client.post(
        f"{BASE_URL}/collections",
        json=collection_data,
        headers={"Authorization": f"Bearer {token}"},
    )

    if response.status_code != 201:
        log_error(f"Failed to create collection: {response.text}")
        sys.exit(1)

    collection = response.json()
    log_success(f"Created collection '{collection_name}' with ID: {collection['id']}")
    return collection


async def create_record(client: httpx.AsyncClient, token: str, collection_name: str, record_data: dict) -> dict:
    """Create a record in the collection."""
    log_info(f"Creating record in '{collection_name}'...")

    response = await client.post(
        f"{BASE_URL}/{collection_name}/records",
        json={"data": record_data},
        headers={"Authorization": f"Bearer {token}"},
    )

    if response.status_code != 201:
        log_error(f"Failed to create record: {response.text}")
        print(f"Request data: {json.dumps({'data': record_data}, indent=2)}")
        raise Exception(f"Record creation failed with status {response.status_code}")

    record = response.json()
    log_success(f"Created record with ID: {record['id']}")
    return record


async def get_record(client: httpx.AsyncClient, token: str, collection_name: str, record_id: str) -> dict:
    """Get a record by ID."""
    log_info(f"Fetching record {record_id} from '{collection_name}'...")

    response = await client.get(
        f"{BASE_URL}/{collection_name}/records/{record_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    if response.status_code != 200:
        log_error(f"Failed to get record: {response.text}")
        raise Exception(f"Get record failed with status {response.status_code}")

    record = response.json()
    log_success(f"Retrieved record: {record['id']}")
    return record


async def update_record(client: httpx.AsyncClient, token: str, collection_name: str, record_id: str, update_data: dict) -> dict:
    """Update a record."""
    log_info(f"Updating record {record_id} in '{collection_name}'...")

    response = await client.patch(
        f"{BASE_URL}/{collection_name}/records/{record_id}",
        json={"data": update_data},
        headers={"Authorization": f"Bearer {token}"},
    )

    if response.status_code != 200:
        log_error(f"Failed to update record: {response.text}")
        raise Exception(f"Update record failed with status {response.status_code}")

    record = response.json()
    log_success(f"Updated record: {record['id']}")
    return record


async def list_records(client: httpx.AsyncClient, token: str, collection_name: str) -> list:
    """List all records in a collection."""
    log_info(f"Listing records in '{collection_name}'...")

    response = await client.get(
        f"{BASE_URL}/{collection_name}/records",
        headers={"Authorization": f"Bearer {token}"},
    )

    if response.status_code != 200:
        log_error(f"Failed to list records: {response.text}")
        raise Exception(f"List records failed with status {response.status_code}")

    data = response.json()
    log_success(f"Found {data['total']} record(s)")
    return data['items']


async def delete_record(client: httpx.AsyncClient, token: str, collection_name: str, record_id: str):
    """Delete a record."""
    log_info(f"Deleting record {record_id} from '{collection_name}'...")

    response = await client.delete(
        f"{BASE_URL}/{collection_name}/records/{record_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    if response.status_code != 204:
        log_error(f"Failed to delete record: {response.text}")
        raise Exception(f"Delete record failed with status {response.status_code}")

    log_success(f"Deleted record: {record_id}")


async def delete_collection(client: httpx.AsyncClient, token: str, collection_id: str):
    """Delete a collection."""
    log_info(f"Cleaning up: deleting collection {collection_id}...")

    response = await client.delete(
        f"{BASE_URL}/collections/{collection_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    if response.status_code != 204:
        log_warning(f"Failed to delete collection: {response.text}")
    else:
        log_success(f"Deleted collection: {collection_id}")


async def main():
    """Run the complete test suite."""
    print("\n" + "=" * 60)
    print("FastCMS Record CRUD Test Suite")
    print("=" * 60 + "\n")

    collection_name = f"test_posts_{int(datetime.now().timestamp())}"
    collection_id = None
    record_ids = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Step 1: Login
            token = await login(client)

            # Step 2: Create test collection
            collection = await create_test_collection(client, token, collection_name)
            collection_id = collection["id"]

            # Step 3: Test creating records with different field types
            print("\n" + "-" * 60)
            print("Testing Record Creation")
            print("-" * 60)

            # Test 1: Record with all required fields
            record1 = await create_record(client, token, collection_name, {
                "title": "My First Post",
                "content": "This is a test post with content.",
                "views": 42,
                "published": True,
                "author_email": "author@example.com",
                "extra_data": {"tags": ["test", "demo"], "featured": True}
            })
            record_ids.append(record1["id"])

            # Test 2: Record with only required fields
            record2 = await create_record(client, token, collection_name, {
                "title": "Minimal Post"
            })
            record_ids.append(record2["id"])

            # Test 3: Record with empty optional fields (should be filtered out)
            record3 = await create_record(client, token, collection_name, {
                "title": "Post with Nulls",
                "published": False
            })
            record_ids.append(record3["id"])

            # Step 4: Test reading records
            print("\n" + "-" * 60)
            print("Testing Record Reading")
            print("-" * 60)

            retrieved = await get_record(client, token, collection_name, record1["id"])
            assert retrieved["data"]["title"] == "My First Post", "Record data mismatch!"
            assert retrieved["data"]["views"] == 42, "Number field mismatch!"
            assert retrieved["data"]["published"] is True, "Boolean field mismatch!"
            log_success("Record data validation passed!")

            # Step 5: Test listing records
            records = await list_records(client, token, collection_name)
            assert len(records) == 3, f"Expected 3 records, got {len(records)}"
            log_success("Record listing validation passed!")

            # Step 6: Test updating records
            print("\n" + "-" * 60)
            print("Testing Record Updates")
            print("-" * 60)

            updated = await update_record(client, token, collection_name, record1["id"], {
                "title": "Updated Post Title",
                "views": 100
            })
            assert updated["data"]["title"] == "Updated Post Title", "Update failed!"
            assert updated["data"]["views"] == 100, "Number update failed!"
            log_success("Record update validation passed!")

            # Step 7: Test deleting records
            print("\n" + "-" * 60)
            print("Testing Record Deletion")
            print("-" * 60)

            await delete_record(client, token, collection_name, record2["id"])

            # Verify deletion
            records_after = await list_records(client, token, collection_name)
            assert len(records_after) == 2, f"Expected 2 records after deletion, got {len(records_after)}"
            log_success("Record deletion validation passed!")

            # Final summary
            print("\n" + "=" * 60)
            print(f"{GREEN}All tests passed! ✓{RESET}")
            print("=" * 60)
            print("\nTest Summary:")
            print(f"  - Created collection: {collection_name}")
            print(f"  - Created 3 records")
            print(f"  - Read and validated record data")
            print(f"  - Updated record successfully")
            print(f"  - Deleted record successfully")
            print(f"  - Final record count: 2")

        except Exception as e:
            log_error(f"Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

        finally:
            # Cleanup
            if collection_id:
                print("\n" + "-" * 60)
                print("Cleanup")
                print("-" * 60)
                await delete_collection(client, token, collection_id)


if __name__ == "__main__":
    asyncio.run(main())
