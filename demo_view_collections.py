#!/usr/bin/env python3
"""
Demo script for View Collections in FastCMS.
This script creates base collections with data, then creates view collections
that compute statistics and aggregated data from those base collections.
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"

async def main():
    print("=" * 70)
    print("📊 FastCMS View Collections Demo")
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

        # Step 2: Create "posts" base collection
        print("2️⃣  Creating 'posts' base collection...")
        posts_collection = {
            "name": "posts",
            "type": "base",
            "schema": [
                {"name": "title", "type": "text", "validation": {"required": True}},
                {"name": "content", "type": "text"},
                {"name": "author", "type": "text", "validation": {"required": True}},
                {"name": "category", "type": "select", "select": {
                    "values": ["Technology", "Business", "Lifestyle", "Science"],
                    "max_select": 1
                }},
                {"name": "published", "type": "bool"},
                {"name": "views", "type": "number"}
            ]
        }

        response = await client.post(
            f"{BASE_URL}/api/v1/collections",
            json=posts_collection,
            headers=headers
        )

        if response.status_code == 201:
            print("✅ Created 'posts' collection\n")
        elif "already exists" in response.text:
            print("⚠️  'posts' collection already exists (skipping)\n")
        else:
            print(f"❌ Failed: {response.text}\n")
            return

        # Step 3: Create "comments" base collection
        print("3️⃣  Creating 'comments' base collection...")
        comments_collection = {
            "name": "comments",
            "type": "base",
            "schema": [
                {"name": "post_id", "type": "text", "validation": {"required": True}},
                {"name": "author", "type": "text", "validation": {"required": True}},
                {"name": "content", "type": "text", "validation": {"required": True}},
                {"name": "rating", "type": "number"}
            ]
        }

        response = await client.post(
            f"{BASE_URL}/api/v1/collections",
            json=comments_collection,
            headers=headers
        )

        if response.status_code == 201:
            print("✅ Created 'comments' collection\n")
        elif "already exists" in response.text:
            print("⚠️  'comments' collection already exists (skipping)\n")
        else:
            print(f"❌ Failed: {response.text}\n")
            return

        # Step 4: Add sample posts
        print("4️⃣  Adding sample posts...")
        posts_data = [
            {
                "title": "Introduction to AI",
                "content": "Artificial Intelligence is transforming our world...",
                "author": "John Doe",
                "category": "Technology",
                "published": True,
                "views": 150
            },
            {
                "title": "Python Best Practices",
                "content": "Learn the best practices for writing Python code...",
                "author": "Jane Smith",
                "category": "Technology",
                "published": True,
                "views": 230
            },
            {
                "title": "Startup Success Stories",
                "content": "How successful startups were built from scratch...",
                "author": "Mike Johnson",
                "category": "Business",
                "published": True,
                "views": 95
            },
            {
                "title": "Healthy Living Tips",
                "content": "Simple tips for maintaining a healthy lifestyle...",
                "author": "Sarah Williams",
                "category": "Lifestyle",
                "published": True,
                "views": 310
            },
            {
                "title": "Future of AI (Draft)",
                "content": "Exploring what the future holds for AI...",
                "author": "John Doe",
                "category": "Technology",
                "published": False,
                "views": 5
            }
        ]

        post_ids = []
        for post in posts_data:
            response = await client.post(
                f"{BASE_URL}/api/v1/posts/records",
                json={"data": post},  # Wrap in data object
                headers=headers
            )
            if response.status_code == 201:
                post_id = response.json()["id"]
                post_ids.append(post_id)
                print(f"   ✅ Created post: {post['title']}")
            else:
                print(f"   ❌ Failed to create post: {response.text}")

        print()

        # Step 5: Add sample comments
        print("5️⃣  Adding sample comments...")
        if len(post_ids) >= 4:
            comments_data = [
                # Comments on first post
                {"post_id": post_ids[0], "author": "Alice", "content": "Great article!", "rating": 5},
                {"post_id": post_ids[0], "author": "Bob", "content": "Very informative", "rating": 4},
                {"post_id": post_ids[0], "author": "Carol", "content": "Loved it!", "rating": 5},
                # Comments on second post
                {"post_id": post_ids[1], "author": "David", "content": "Helpful tips", "rating": 5},
                {"post_id": post_ids[1], "author": "Eve", "content": "Nice post", "rating": 4},
                # Comments on third post
                {"post_id": post_ids[2], "author": "Frank", "content": "Inspiring!", "rating": 5},
                {"post_id": post_ids[2], "author": "Grace", "content": "Good read", "rating": 4},
                {"post_id": post_ids[2], "author": "Henry", "content": "Thanks for sharing", "rating": 4},
                {"post_id": post_ids[2], "author": "Ivy", "content": "Well written", "rating": 5},
                # Comments on fourth post
                {"post_id": post_ids[3], "author": "Jack", "content": "Very useful", "rating": 5},
                {"post_id": post_ids[3], "author": "Kate", "content": "Will try these tips", "rating": 5},
            ]

            for comment in comments_data:
                response = await client.post(
                    f"{BASE_URL}/api/v1/comments/records",
                    json={"data": comment},  # Wrap in data object
                    headers=headers
                )
                if response.status_code == 201:
                    print(f"   ✅ Added comment by {comment['author']}")

        print()

        # Step 6: Create view collection for post statistics
        print("6️⃣  Creating 'post_stats' view collection...")
        post_stats_view = {
            "name": "post_stats",
            "type": "view",
            "options": {
                "query": {
                    "source": "posts",
                    "select": [
                        "posts.id",
                        "posts.title",
                        "posts.author",
                        "posts.category",
                        "posts.views",
                        "COUNT(comments.id) as comment_count",
                        "AVG(comments.rating) as avg_rating"
                    ],
                    "joins": [
                        {
                            "type": "LEFT",
                            "collection": "comments",
                            "on": "posts.id = comments.post_id"
                        }
                    ],
                    "where": "posts.published = 1",
                    "group_by": ["posts.id", "posts.title", "posts.author", "posts.category", "posts.views"],
                    "order_by": ["-comment_count", "-posts.views"]
                },
                "cache_ttl": 300
            },
            "schema": []
        }

        response = await client.post(
            f"{BASE_URL}/api/v1/collections",
            json=post_stats_view,
            headers=headers
        )

        if response.status_code == 201:
            print("✅ Created 'post_stats' view collection!")
            print("   This view shows post statistics with comment counts and ratings\n")
        elif "already exists" in response.text:
            print("⚠️  'post_stats' view collection already exists (skipping)\n")
        else:
            print(f"❌ Failed: {response.text}\n")
            return

        # Step 7: Create view collection for category summary
        print("7️⃣  Creating 'category_summary' view collection...")
        category_summary_view = {
            "name": "category_summary",
            "type": "view",
            "options": {
                "query": {
                    "source": "posts",
                    "select": [
                        "posts.category",
                        "COUNT(posts.id) as total_posts",
                        "SUM(posts.views) as total_views",
                        "AVG(posts.views) as avg_views_per_post"
                    ],
                    "joins": [],
                    "where": "posts.published = 1",
                    "group_by": ["posts.category"],
                    "order_by": ["-total_views"]
                },
                "cache_ttl": 600
            },
            "schema": []
        }

        response = await client.post(
            f"{BASE_URL}/api/v1/collections",
            json=category_summary_view,
            headers=headers
        )

        if response.status_code == 201:
            print("✅ Created 'category_summary' view collection!")
            print("   This view shows aggregated statistics by category\n")
        elif "already exists" in response.text:
            print("⚠️  'category_summary' view collection already exists (skipping)\n")
        else:
            print(f"❌ Failed: {response.text}\n")
            return

        # Step 8: Query the post_stats view
        print("8️⃣  Querying 'post_stats' view...")
        response = await client.get(
            f"{BASE_URL}/api/v1/views/post_stats/records",
            headers=headers
        )

        if response.status_code == 200:
            results = response.json()
            print(f"✅ Retrieved {results['total']} post statistics:\n")
            print(f"{'Title':<30} {'Author':<15} {'Views':<8} {'Comments':<10} {'Avg Rating':<12}")
            print("-" * 80)
            for item in results['items']:
                title = item.get('title', 'N/A')[:28]
                author = item.get('author', 'N/A')[:13]
                views = item.get('views', 0)
                comment_count = item.get('comment_count', 0)
                avg_rating = item.get('avg_rating')
                avg_rating_str = f"{avg_rating:.1f}" if avg_rating else "N/A"
                print(f"{title:<30} {author:<15} {views:<8} {comment_count:<10} {avg_rating_str:<12}")
            print()
        else:
            print(f"❌ Failed: {response.text}\n")

        # Step 9: Query the category_summary view
        print("9️⃣  Querying 'category_summary' view...")
        response = await client.get(
            f"{BASE_URL}/api/v1/views/category_summary/records",
            headers=headers
        )

        if response.status_code == 200:
            results = response.json()
            print(f"✅ Retrieved category statistics:\n")
            print(f"{'Category':<15} {'Posts':<8} {'Total Views':<15} {'Avg Views/Post':<15}")
            print("-" * 55)
            for item in results['items']:
                category = item.get('category', 'N/A')
                total_posts = item.get('total_posts', 0)
                total_views = item.get('total_views', 0)
                avg_views = item.get('avg_views_per_post', 0)
                print(f"{category:<15} {total_posts:<8} {total_views:<15} {avg_views:<15.1f}")
            print()
        else:
            print(f"❌ Failed: {response.text}\n")

        # Final Summary
        print("=" * 70)
        print("✅ View Collections Demo Complete!")
        print("=" * 70)
        print()
        print("📊 What was created:")
        print("   • 2 Base collections: 'posts' and 'comments'")
        print("   • 5 Posts with varying view counts")
        print("   • 11 Comments across the posts")
        print("   • 2 View collections:")
        print("     - 'post_stats': Shows post statistics with comment counts and ratings")
        print("     - 'category_summary': Shows aggregated statistics by category")
        print()
        print("🔑 Key Features Demonstrated:")
        print("   ✓ Virtual collections (no physical storage)")
        print("   ✓ JOIN operations (posts + comments)")
        print("   ✓ Aggregation functions (COUNT, AVG, SUM)")
        print("   ✓ GROUP BY for grouping data")
        print("   ✓ WHERE filters (only published posts)")
        print("   ✓ ORDER BY for sorting results")
        print("   ✓ Caching for performance")
        print()
        print("🧪 Try it yourself:")
        print(f"   • View post stats: {BASE_URL}/api/v1/views/post_stats/records")
        print(f"   • View category summary: {BASE_URL}/api/v1/views/category_summary/records")
        print(f"   • Admin UI: {BASE_URL}/admin/collections")
        print(f"   • API docs: {BASE_URL}/docs (look for 'View Collections' tag)")
        print()
        print("💡 Add more data and watch the views update automatically!")
        print(f"   curl -X POST {BASE_URL}/api/v1/posts/records \\")
        print(f"     -H 'Authorization: Bearer YOUR_TOKEN' \\")
        print(f"     -d '{{\"title\":\"New Post\",\"author\":\"You\",\"category\":\"Technology\",\"published\":true,\"views\":0}}'")
        print()

if __name__ == "__main__":
    asyncio.run(main())
