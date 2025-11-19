# ✅ View Collections - FULLY IMPLEMENTED!

## 🎉 What's New

View collections are now **fully implemented** in FastCMS! You can create virtual collections that compute data from other collections on-the-fly.

---

## 📊 What Are View Collections?

View collections are **virtual collections** that don't store data but compute it from other collections in real-time:

- **No physical storage**: View collections don't have database tables
- **Computed data**: Results are calculated from queries on other collections
- **Read-only**: You can only query views, not create/update/delete records
- **Cached for performance**: Results are cached to improve query speed
- **Real-time**: Data updates automatically when source collections change

---

## 📚 How to Create a View Collection

### Via Admin UI:

1. Go to **Collections** → **Create Collection**
2. Enter collection name (e.g., `post_stats`)
3. Select type: **"View"**
4. Configure the query:
   - **Source Collection**: Select the main collection to query from
   - **Select Fields**: Specify which fields to include (supports aggregations)
   - **Group By**: Group results by specific fields (for aggregations)
   - **Order By**: Sort the results
   - **Cache TTL**: How long to cache results (in seconds)
5. Click **Create Collection**

### Via API:

```bash
curl -X POST http://localhost:8000/api/v1/collections \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "post_stats",
    "type": "view",
    "options": {
      "query": {
        "source": "posts",
        "select": [
          "posts.id",
          "posts.title",
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
        "group_by": ["posts.id", "posts.title"],
        "order_by": ["-comment_count"]
      },
      "cache_ttl": 300
    },
    "schema": []
  }'
```

---

## 🔍 Query View Collections

Once created, query view collections like regular collections (but read-only):

```bash
# Query the view
curl http://localhost:8000/api/v1/views/post_stats/records \
  -H "Authorization: Bearer YOUR_TOKEN"

# With pagination
curl "http://localhost:8000/api/v1/views/post_stats/records?page=1&per_page=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Refresh cache manually
curl -X POST http://localhost:8000/api/v1/views/post_stats/refresh \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 💡 Use Cases

### 1. **Post Statistics Dashboard**

Show posts with comment counts and average ratings:

```json
{
  "name": "post_stats",
  "type": "view",
  "options": {
    "query": {
      "source": "posts",
      "select": [
        "posts.id",
        "posts.title",
        "posts.author",
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
      "group_by": ["posts.id", "posts.title", "posts.author"],
      "order_by": ["-comment_count"]
    }
  }
}
```

Result:
```json
[
  {
    "id": "abc123",
    "title": "Introduction to AI",
    "author": "John Doe",
    "comment_count": 15,
    "avg_rating": 4.7
  },
  ...
]
```

### 2. **Category Summary Report**

Aggregate statistics by category:

```json
{
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
      "where": "posts.published = 1",
      "group_by": ["posts.category"],
      "order_by": ["-total_views"]
    }
  }
}
```

Result:
```json
[
  {
    "category": "Technology",
    "total_posts": 25,
    "total_views": 12500,
    "avg_views_per_post": 500
  },
  ...
]
```

### 3. **User Activity Summary**

Track user engagement across collections:

```json
{
  "name": "user_activity",
  "type": "view",
  "options": {
    "query": {
      "source": "users",
      "select": [
        "users.id",
        "users.name",
        "COUNT(posts.id) as posts_created",
        "COUNT(comments.id) as comments_made"
      ],
      "joins": [
        {
          "type": "LEFT",
          "collection": "posts",
          "on": "users.id = posts.author_id"
        },
        {
          "type": "LEFT",
          "collection": "comments",
          "on": "users.id = comments.author_id"
        }
      ],
      "group_by": ["users.id", "users.name"],
      "order_by": ["-posts_created"]
    }
  }
}
```

---

## 🔧 Query Configuration Options

### Select Fields

Supports both simple fields and aggregations:

```json
"select": [
  "posts.id",                              // Simple field
  "posts.title",                           // Simple field
  "COUNT(comments.id) as comment_count",   // Aggregation
  "AVG(comments.rating) as avg_rating",    // Aggregation
  "SUM(orders.total) as revenue"           // Aggregation
]
```

### Supported Aggregations

- `COUNT(field)` - Count records
- `SUM(field)` - Sum numeric values
- `AVG(field)` - Average of numeric values
- `MIN(field)` - Minimum value
- `MAX(field)` - Maximum value

### Joins

Support multiple join types:

```json
"joins": [
  {
    "type": "LEFT",        // LEFT, RIGHT, INNER, OUTER
    "collection": "comments",
    "on": "posts.id = comments.post_id",
    "alias": "c"           // Optional alias
  }
]
```

### Where Clause

Filter results with SQL-like conditions:

```json
"where": "posts.published = 1 AND posts.views > 100"
```

### Group By

Group results for aggregations:

```json
"group_by": ["posts.category", "posts.author"]
```

### Order By

Sort results (prefix with `-` for descending):

```json
"order_by": ["-comment_count", "posts.title"]
```

---

## ⚡ Performance & Caching

### Cache TTL

Control how long results are cached:

```json
"cache_ttl": 300  // Cache for 5 minutes (default)
"cache_ttl": 0    // Disable caching
"cache_ttl": 3600 // Cache for 1 hour
```

### Manual Cache Refresh

Force recalculation of results:

```bash
curl -X POST http://localhost:8000/api/v1/views/post_stats/refresh \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Automatic Updates

View results automatically reflect changes in source collections:
- Add a new post → next query shows updated counts
- Add a comment → average ratings recalculate
- Publish/unpublish posts → filtered results update

---

## 🆚 View vs Base vs Auth Collections

| Feature | Base | Auth | View |
|---------|------|------|------|
| **Storage** | ✅ Physical table | ✅ Physical table | ❌ Virtual (no table) |
| **CRUD Operations** | ✅ Full | ✅ Full + Auth | 📖 Read-only |
| **Custom Schema** | ✅ Yes | ✅ Yes + Auth fields | ⚙️ Computed from query |
| **Relations** | ✅ Yes | ✅ Yes | 🔗 Via JOINs |
| **Aggregations** | ❌ No | ❌ No | ✅ Yes (COUNT, SUM, AVG) |
| **Performance** | Fast (direct query) | Fast (direct query) | Fast (cached) |
| **Use For** | Regular data | User auth | Statistics, reports |

---

## 📖 API Documentation

Visit **http://localhost:8000/docs** and look for the **"View Collections"** tag to see all available endpoints with interactive testing!

### Endpoints

- `GET /api/v1/views/{view_name}/records` - Query a view collection
- `POST /api/v1/views/{view_name}/refresh` - Refresh cache

---

## 🎨 Admin UI

View your view collection results in the admin panel:
- `http://localhost:8000/admin/collections/post_stats/records`
- `http://localhost:8000/admin/collections/category_summary/records`

**Note**: View collections are read-only, so you won't see "Create" or "Edit" buttons for records.

---

## ✨ What Makes This Special?

1. **No Data Duplication**: Views don't store data, saving database space
2. **Always Fresh**: Results reflect the latest data from source collections
3. **Powerful Queries**: Support for JOINs, aggregations, filtering, grouping
4. **Performance**: Built-in caching for fast repeated queries
5. **Flexible**: Create unlimited views from the same data
6. **Standard API**: Works just like regular collections (read-only)

---

## 🚦 Current Status

**✅ FULLY IMPLEMENTED:**
- View collection creation
- Query DSL (select, joins, where, group by, order by)
- Aggregation functions (COUNT, SUM, AVG, MIN, MAX)
- JOIN support (LEFT, RIGHT, INNER, OUTER)
- Query execution engine
- Result caching
- Cache invalidation
- Admin UI integration
- API endpoints

**🔜 Coming Soon:**
- More complex JOIN conditions
- Subqueries support
- HAVING clause for filtered aggregations
- Materialized views (pre-computed and stored)
- Real-time cache invalidation on source changes

---

## 🧪 Quick Test

Run the demo script to see view collections in action:

```bash
python demo_view_collections.py
```

This creates:
- **posts** collection with 5 sample posts
- **comments** collection with 11 sample comments
- **post_stats** view showing post statistics
- **category_summary** view showing category aggregations

---

## 🎯 Examples

### Simple Aggregation

Get total users and posts:

```json
{
  "name": "platform_stats",
  "type": "view",
  "options": {
    "query": {
      "source": "users",
      "select": [
        "COUNT(users.id) as total_users",
        "COUNT(posts.id) as total_posts"
      ],
      "joins": [
        {
          "type": "LEFT",
          "collection": "posts",
          "on": "users.id = posts.author_id"
        }
      ]
    }
  }
}
```

### Top Performers

Find most active authors:

```json
{
  "name": "top_authors",
  "type": "view",
  "options": {
    "query": {
      "source": "users",
      "select": [
        "users.name",
        "COUNT(posts.id) as post_count",
        "SUM(posts.views) as total_views"
      ],
      "joins": [
        {
          "type": "LEFT",
          "collection": "posts",
          "on": "users.id = posts.author_id"
        }
      ],
      "where": "posts.published = 1",
      "group_by": ["users.id", "users.name"],
      "order_by": ["-total_views"],
      "limit": 10
    },
    "cache_ttl": 600
  }
}
```

### Multi-Collection Join

Combine data from 3 collections:

```json
{
  "name": "engagement_report",
  "type": "view",
  "options": {
    "query": {
      "source": "posts",
      "select": [
        "posts.title",
        "users.name as author_name",
        "COUNT(comments.id) as comments",
        "COUNT(likes.id) as likes"
      ],
      "joins": [
        {
          "type": "LEFT",
          "collection": "users",
          "on": "posts.author_id = users.id"
        },
        {
          "type": "LEFT",
          "collection": "comments",
          "on": "posts.id = comments.post_id"
        },
        {
          "type": "LEFT",
          "collection": "likes",
          "on": "posts.id = likes.post_id"
        }
      ],
      "group_by": ["posts.id", "posts.title", "users.name"],
      "order_by": ["-comments", "-likes"]
    }
  }
}
```

---

## 🎉 Conclusion

View collections transform FastCMS into a **powerful analytics and reporting platform**. You can now:
- Build dashboards with real-time statistics
- Generate reports without writing SQL
- Aggregate data across multiple collections
- Monitor platform metrics
- Track user engagement

All through a simple, RESTful API! 📊

---

## 🆘 Troubleshooting

**Q: My view returns empty results**
- Check that source collections exist and have data
- Verify JOIN conditions are correct
- Check WHERE clause doesn't filter out all records

**Q: Query is slow**
- Increase cache_ttl for better performance
- Ensure proper indexes on source collections
- Simplify complex JOINs if possible

**Q: How do I update view data?**
- Views are read-only
- Update the source collections instead
- Refresh the view cache to see changes immediately

**Q: Can I create views from other views?**
- Not yet - views can only query base/auth collections
- Coming in future releases!
