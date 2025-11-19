#!/usr/bin/env python3
"""
Script to create example collections with relations and populate them with sample data.
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def main():
    print("=== FastCMS Example Data Setup ===\n")

    # Step 1: Login as admin
    print("1. Logging in as admin...")
    async with httpx.AsyncClient() as client:
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

        # Step 2: Create authors collection
        print("2. Creating 'authors' collection...")
        authors_collection = {
            "name": "authors",
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
                    "validation": {"required": True, "unique": True}
                },
                {
                    "name": "bio",
                    "type": "editor"
                },
                {
                    "name": "active",
                    "type": "bool"
                }
            ]
        }

        response = await client.post(
            f"{BASE_URL}/api/v1/collections",
            json=authors_collection,
            headers=headers
        )
        if response.status_code == 201:
            authors_coll_data = response.json()
            authors_coll_id = authors_coll_data["id"]
            print(f"✅ Created 'authors' collection (ID: {authors_coll_id})\n")
        else:
            print(f"❌ Failed to create authors collection: {response.text}")
            return

        # Step 3: Create categories collection
        print("3. Creating 'categories' collection...")
        categories_collection = {
            "name": "categories",
            "type": "base",
            "schema": [
                {
                    "name": "name",
                    "type": "text",
                    "validation": {"required": True, "unique": True}
                },
                {
                    "name": "description",
                    "type": "text"
                },
                {
                    "name": "slug",
                    "type": "text",
                    "validation": {"required": True, "unique": True}
                }
            ]
        }

        response = await client.post(
            f"{BASE_URL}/api/v1/collections",
            json=categories_collection,
            headers=headers
        )
        if response.status_code == 201:
            categories_coll_data = response.json()
            categories_coll_id = categories_coll_data["id"]
            print(f"✅ Created 'categories' collection (ID: {categories_coll_id})\n")
        else:
            print(f"❌ Failed to create categories collection: {response.text}")
            return

        # Step 4: Create blog_posts collection with relations
        print("4. Creating 'blog_posts' collection with relations...")
        blog_posts_collection = {
            "name": "blog_posts",
            "type": "base",
            "schema": [
                {
                    "name": "title",
                    "type": "text",
                    "validation": {"required": True}
                },
                {
                    "name": "slug",
                    "type": "text",
                    "validation": {"required": True, "unique": True}
                },
                {
                    "name": "content",
                    "type": "editor",
                    "validation": {"required": True}
                },
                {
                    "name": "author",
                    "type": "relation",
                    "relation": {
                        "collection_id": authors_coll_id,
                        "cascade_delete": False,
                        "display_fields": ["name", "email"]
                    },
                    "validation": {"required": True}
                },
                {
                    "name": "category",
                    "type": "relation",
                    "relation": {
                        "collection_id": categories_coll_id,
                        "cascade_delete": False,
                        "display_fields": ["name"]
                    }
                },
                {
                    "name": "published",
                    "type": "bool"
                },
                {
                    "name": "views",
                    "type": "number"
                }
            ]
        }

        response = await client.post(
            f"{BASE_URL}/api/v1/collections",
            json=blog_posts_collection,
            headers=headers
        )
        if response.status_code == 201:
            blog_posts_coll_data = response.json()
            blog_posts_coll_id = blog_posts_coll_data["id"]
            print(f"✅ Created 'blog_posts' collection with author & category relations\n")
        else:
            print(f"❌ Failed to create blog_posts collection: {response.text}")
            return

        # Step 5: Create comments collection with relations
        print("5. Creating 'comments' collection with relations...")
        comments_collection = {
            "name": "comments",
            "type": "base",
            "schema": [
                {
                    "name": "post",
                    "type": "relation",
                    "relation": {
                        "collection_id": blog_posts_coll_id,
                        "cascade_delete": True,  # Delete comments when post is deleted
                        "display_fields": ["title"]
                    },
                    "validation": {"required": True}
                },
                {
                    "name": "author",
                    "type": "relation",
                    "relation": {
                        "collection_id": authors_coll_id,
                        "cascade_delete": False,
                        "display_fields": ["name"]
                    },
                    "validation": {"required": True}
                },
                {
                    "name": "content",
                    "type": "text",
                    "validation": {"required": True}
                },
                {
                    "name": "approved",
                    "type": "bool"
                }
            ]
        }

        response = await client.post(
            f"{BASE_URL}/api/v1/collections",
            json=comments_collection,
            headers=headers
        )
        if response.status_code == 201:
            print(f"✅ Created 'comments' collection with post & author relations\n")
        else:
            print(f"❌ Failed to create comments collection: {response.text}")
            return

        # Step 6: Add sample authors
        print("6. Adding sample authors...")
        authors_data = [
            {"name": "John Doe", "email": "john@example.com", "bio": "<p>Tech enthusiast and blogger</p>", "active": True},
            {"name": "Jane Smith", "email": "jane@example.com", "bio": "<p>Professional writer and editor</p>", "active": True},
            {"name": "Bob Johnson", "email": "bob@example.com", "bio": "<p>Software developer</p>", "active": True}
        ]

        author_ids = []
        for author_data in authors_data:
            response = await client.post(
                f"{BASE_URL}/api/v1/authors/records",
                json={"data": author_data},
                headers=headers
            )
            if response.status_code == 201:
                author_id = response.json()["id"]
                author_ids.append(author_id)
                print(f"  ✅ Added author: {author_data['name']} (ID: {author_id})")
            else:
                print(f"  ❌ Failed to add author: {response.text}")
        print()

        # Step 7: Add sample categories
        print("7. Adding sample categories...")
        categories_data = [
            {"name": "Technology", "description": "Tech news and tutorials", "slug": "technology"},
            {"name": "Programming", "description": "Programming guides", "slug": "programming"},
            {"name": "Design", "description": "Design tips and tricks", "slug": "design"}
        ]

        category_ids = []
        for category_data in categories_data:
            response = await client.post(
                f"{BASE_URL}/api/v1/categories/records",
                json={"data": category_data},
                headers=headers
            )
            if response.status_code == 201:
                category_id = response.json()["id"]
                category_ids.append(category_id)
                print(f"  ✅ Added category: {category_data['name']} (ID: {category_id})")
            else:
                print(f"  ❌ Failed to add category: {response.text}")
        print()

        # Step 8: Add sample blog posts with relations
        print("8. Adding sample blog posts with author & category relations...")
        blog_posts_data = [
            {
                "title": "Getting Started with FastAPI",
                "slug": "getting-started-with-fastapi",
                "content": "<h2>Introduction</h2><p>FastAPI is a modern, fast web framework for Python...</p>",
                "author": author_ids[0],  # John Doe
                "category": category_ids[1],  # Programming
                "published": True,
                "views": 150
            },
            {
                "title": "Modern Web Design Principles",
                "slug": "modern-web-design-principles",
                "content": "<h2>Design Basics</h2><p>Learn the fundamentals of modern web design...</p>",
                "author": author_ids[1],  # Jane Smith
                "category": category_ids[2],  # Design
                "published": True,
                "views": 230
            },
            {
                "title": "Python Best Practices 2025",
                "slug": "python-best-practices-2025",
                "content": "<h2>Writing Better Python</h2><p>Tips for writing clean, maintainable Python code...</p>",
                "author": author_ids[2],  # Bob Johnson
                "category": category_ids[1],  # Programming
                "published": True,
                "views": 340
            }
        ]

        post_ids = []
        for post_data in blog_posts_data:
            response = await client.post(
                f"{BASE_URL}/api/v1/blog_posts/records",
                json={"data": post_data},
                headers=headers
            )
            if response.status_code == 201:
                post_id = response.json()["id"]
                post_ids.append(post_id)
                print(f"  ✅ Added post: {post_data['title']}")
                print(f"     → Author: {author_ids.index(post_data['author'])+1}, Category: {category_ids.index(post_data['category'])+1}")
            else:
                print(f"  ❌ Failed to add post: {response.text}")
        print()

        # Step 9: Add sample comments with relations
        print("9. Adding sample comments with post & author relations...")
        comments_data = [
            {
                "post": post_ids[0],  # FastAPI post
                "author": author_ids[1],  # Jane
                "content": "Great tutorial! Very helpful for beginners.",
                "approved": True
            },
            {
                "post": post_ids[0],  # FastAPI post
                "author": author_ids[2],  # Bob
                "content": "I've been using FastAPI for a year now, it's amazing!",
                "approved": True
            },
            {
                "post": post_ids[1],  # Design post
                "author": author_ids[0],  # John
                "content": "These principles really improved my designs.",
                "approved": True
            },
            {
                "post": post_ids[2],  # Python post
                "author": author_ids[1],  # Jane
                "content": "Excellent tips! Will definitely apply these.",
                "approved": True
            }
        ]

        for comment_data in comments_data:
            response = await client.post(
                f"{BASE_URL}/api/v1/comments/records",
                json={"data": comment_data},
                headers=headers
            )
            if response.status_code == 201:
                comment_id = response.json()["id"]
                print(f"  ✅ Added comment on post #{post_ids.index(comment_data['post'])+1} by author #{author_ids.index(comment_data['author'])+1}")
            else:
                print(f"  ❌ Failed to add comment: {response.text}")
        print()

        print("=" * 50)
        print("✅ Example data setup complete!")
        print("=" * 50)
        print("\n📊 Summary:")
        print(f"  • 3 Authors")
        print(f"  • 3 Categories")
        print(f"  • 3 Blog Posts (with author & category relations)")
        print(f"  • 4 Comments (with post & author relations)")
        print("\n🔗 Relation Examples:")
        print("  • blog_posts.author → authors collection")
        print("  • blog_posts.category → categories collection")
        print("  • comments.post → blog_posts collection (cascade delete)")
        print("  • comments.author → authors collection")
        print("\n💡 Try querying:")
        print(f"  • GET /api/v1/blog_posts/records")
        print(f"  • GET /api/v1/comments/records")
        print(f"  • View in admin: http://localhost:8000/admin/collections")

if __name__ == "__main__":
    asyncio.run(main())
