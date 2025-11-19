"""
Full-Text Search Service using SQLite FTS5
"""
import uuid
import json
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.search import SearchIndex
from app.db.models.collection import Collection


class SearchService:
    """Service for full-text search operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_search_index(
        self, collection_name: str, fields: List[str]
    ) -> SearchIndex:
        """
        Create FTS5 virtual table for a collection
        """
        # Check if index already exists
        result = await self.db.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"),
            {"table_name": f"{collection_name}_fts"},
        )
        if result.fetchone():
            raise ValueError(f"Search index already exists for {collection_name}")

        # Create FTS5 virtual table
        fields_list = ", ".join(fields)
        create_fts_sql = f"""
        CREATE VIRTUAL TABLE {collection_name}_fts USING fts5(
            record_id UNINDEXED,
            {fields_list},
            tokenize='porter unicode61'
        )
        """
        await self.db.execute(text(create_fts_sql))

        # Create triggers to keep FTS in sync
        # Insert trigger
        insert_trigger_sql = f"""
        CREATE TRIGGER {collection_name}_fts_insert AFTER INSERT ON {collection_name}
        BEGIN
            INSERT INTO {collection_name}_fts(record_id, {fields_list})
            VALUES (new.id, {", ".join(f"new.{f}" for f in fields)});
        END
        """
        await self.db.execute(text(insert_trigger_sql))

        # Update trigger
        update_trigger_sql = f"""
        CREATE TRIGGER {collection_name}_fts_update AFTER UPDATE ON {collection_name}
        BEGIN
            UPDATE {collection_name}_fts
            SET {", ".join(f"{f}=new.{f}" for f in fields)}
            WHERE record_id = old.id;
        END
        """
        await self.db.execute(text(update_trigger_sql))

        # Delete trigger
        delete_trigger_sql = f"""
        CREATE TRIGGER {collection_name}_fts_delete AFTER DELETE ON {collection_name}
        BEGIN
            DELETE FROM {collection_name}_fts WHERE record_id = old.id;
        END
        """
        await self.db.execute(text(delete_trigger_sql))

        # Save index metadata
        search_index = SearchIndex(
            id=str(uuid.uuid4()),
            collection_name=collection_name,
            indexed_fields=json.dumps(fields),
        )
        self.db.add(search_index)
        await self.db.commit()

        return search_index

    async def delete_search_index(self, collection_name: str) -> None:
        """
        Drop FTS5 virtual table and triggers
        """
        # Drop triggers
        await self.db.execute(
            text(f"DROP TRIGGER IF EXISTS {collection_name}_fts_insert")
        )
        await self.db.execute(
            text(f"DROP TRIGGER IF EXISTS {collection_name}_fts_update")
        )
        await self.db.execute(
            text(f"DROP TRIGGER IF EXISTS {collection_name}_fts_delete")
        )

        # Drop FTS table
        await self.db.execute(text(f"DROP TABLE IF EXISTS {collection_name}_fts"))

        # Remove metadata
        result = await self.db.execute(
            text("DELETE FROM search_indexes WHERE collection_name = :collection"),
            {"collection": collection_name},
        )
        await self.db.commit()

    async def search(
        self,
        collection_name: str,
        query: str,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Perform full-text search on a collection
        Returns list of record IDs with rank scores
        """
        # Check if search index exists
        result = await self.db.execute(
            text("SELECT indexed_fields FROM search_indexes WHERE collection_name = :collection"),
            {"collection": collection_name},
        )
        row = result.fetchone()
        if not row:
            raise ValueError(f"No search index found for collection {collection_name}")

        indexed_fields = json.loads(row[0])

        # Perform FTS5 search
        search_sql = f"""
        SELECT
            fts.record_id,
            fts.rank,
            t.*
        FROM {collection_name}_fts fts
        JOIN {collection_name} t ON t.id = fts.record_id
        WHERE {collection_name}_fts MATCH :query
        ORDER BY fts.rank
        LIMIT :limit OFFSET :offset
        """

        result = await self.db.execute(
            text(search_sql),
            {"query": query, "limit": limit, "offset": offset},
        )

        rows = result.fetchall()
        columns = result.keys()

        # Convert to list of dicts
        results = []
        for row in rows:
            record = dict(zip(columns, row))
            results.append(record)

        return results

    async def get_search_index(self, collection_name: str) -> Optional[SearchIndex]:
        """Get search index metadata"""
        result = await self.db.execute(
            text("SELECT * FROM search_indexes WHERE collection_name = :collection"),
            {"collection": collection_name},
        )
        row = result.fetchone()
        if not row:
            return None

        return SearchIndex(
            id=row[0],
            collection_name=row[1],
            indexed_fields=row[2],
            created=row[3],
            updated=row[4],
        )

    async def list_search_indexes(self) -> List[SearchIndex]:
        """List all search indexes"""
        result = await self.db.execute(text("SELECT * FROM search_indexes"))
        rows = result.fetchall()

        indexes = []
        for row in rows:
            indexes.append(
                SearchIndex(
                    id=row[0],
                    collection_name=row[1],
                    indexed_fields=row[2],
                    created=row[3],
                    updated=row[4],
                )
            )

        return indexes

    async def reindex_collection(self, collection_name: str) -> int:
        """
        Rebuild FTS index for a collection
        Returns number of records indexed
        """
        # Get indexed fields
        search_index = await self.get_search_index(collection_name)
        if not search_index:
            raise ValueError(f"No search index found for collection {collection_name}")

        indexed_fields = json.loads(search_index.indexed_fields)
        fields_list = ", ".join(indexed_fields)

        # Clear FTS table
        await self.db.execute(text(f"DELETE FROM {collection_name}_fts"))

        # Rebuild from main table
        insert_sql = f"""
        INSERT INTO {collection_name}_fts(record_id, {fields_list})
        SELECT id, {fields_list}
        FROM {collection_name}
        """
        result = await self.db.execute(text(insert_sql))
        await self.db.commit()

        return result.rowcount
