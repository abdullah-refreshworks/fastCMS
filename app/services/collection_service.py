"""
Business logic service for collection operations.
"""

from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.core.logging import get_logger
from app.db.models.collection import Collection
from app.db.models.dynamic import DynamicModelGenerator
from app.db.repositories.collection import CollectionRepository
from app.db.session import engine
from app.schemas.collection import (
    CollectionCreate,
    CollectionResponse,
    CollectionUpdate,
)
from app.utils.field_types import FieldSchema

logger = get_logger(__name__)


class CollectionService:
    """Service for managing collections."""

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize service.

        Args:
            db: Async database session
        """
        self.db = db
        self.repo = CollectionRepository(db)

    async def create_collection(
        self,
        data: CollectionCreate,
    ) -> CollectionResponse:
        """
        Create a new collection.

        Args:
            data: Collection creation data

        Returns:
            Created collection response

        Raises:
            ConflictException: If collection with name already exists
            BadRequestException: If schema validation fails
        """
        # Check if collection already exists
        if await self.repo.exists(data.name):
            raise ConflictException(f"Collection '{data.name}' already exists")

        # Handle auth collections - inject required fields
        if data.type == "auth":
            data.schema = self._ensure_auth_fields(data.schema)

        # Convert schema to dict for storage
        schema_dict = [field.model_dump() for field in data.schema]

        # Create collection record
        collection = Collection(
            name=data.name,
            type=data.type,
            schema={"fields": schema_dict},
            options=data.options,
            list_rule=data.list_rule,
            view_rule=data.view_rule,
            create_rule=data.create_rule,
            update_rule=data.update_rule,
            delete_rule=data.delete_rule,
            view_query=data.view_query,
            system=False,
        )

        # Save to database
        collection = await self.repo.create(collection)
        await self.db.commit()

        logger.info(f"Collection '{data.name}' created with ID: {collection.id}")

        # Create dynamic model and table (skip for view collections)
        if data.type != "view":
            try:
                model = DynamicModelGenerator.create_model(
                    collection_name=data.name,
                    fields=data.schema,
                )

                await DynamicModelGenerator.create_table(engine, model)

                logger.info(f"Database table '{data.name}' created successfully")

            except Exception as e:
                # Rollback collection creation if table creation fails
                await self.db.rollback()
                logger.error(f"Failed to create table for collection '{data.name}': {e}")
                raise BadRequestException(f"Failed to create collection table: {str(e)}")
        else:
            logger.info(f"View collection '{data.name}' created (no physical table)")

        return self._to_response(collection)

    async def get_collection(self, collection_id: str) -> CollectionResponse:
        """
        Get collection by ID.

        Args:
            collection_id: Collection ID

        Returns:
            Collection response

        Raises:
            NotFoundException: If collection not found
        """
        collection = await self.repo.get_by_id(collection_id)

        if not collection:
            raise NotFoundException(f"Collection with ID '{collection_id}' not found")

        return self._to_response(collection)

    async def get_collection_by_name(self, name: str) -> CollectionResponse:
        """
        Get collection by name.

        Args:
            name: Collection name

        Returns:
            Collection response

        Raises:
            NotFoundException: If collection not found
        """
        collection = await self.repo.get_by_name(name)

        if not collection:
            raise NotFoundException(f"Collection '{name}' not found")

        return self._to_response(collection)

    async def list_collections(
        self,
        page: int = 1,
        per_page: int = 30,
        include_system: bool = False,
    ) -> tuple[List[CollectionResponse], int]:
        """
        List all collections with pagination.

        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            include_system: Include system collections

        Returns:
            Tuple of (collections, total_count)
        """
        skip = (page - 1) * per_page

        collections = await self.repo.get_all(
            skip=skip,
            limit=per_page,
            include_system=include_system,
        )

        total = await self.repo.count(include_system=include_system)

        return [self._to_response(c) for c in collections], total

    async def update_collection(
        self,
        collection_id: str,
        data: CollectionUpdate,
    ) -> CollectionResponse:
        """
        Update a collection.

        Args:
            collection_id: Collection ID
            data: Update data

        Returns:
            Updated collection response

        Raises:
            NotFoundException: If collection not found
            BadRequestException: If update fails
        """
        collection = await self.repo.get_by_id(collection_id)

        if not collection:
            raise NotFoundException(f"Collection with ID '{collection_id}' not found")

        if collection.system:
            raise BadRequestException("Cannot modify system collection")

        # Update fields
        if data.name is not None:
            # Check name uniqueness
            if data.name != collection.name and await self.repo.exists(data.name):
                raise ConflictException(f"Collection '{data.name}' already exists")
            collection.name = data.name

        if data.schema is not None:
            collection.schema = {"fields": [field.model_dump() for field in data.schema]}

        if data.options is not None:
            collection.options = data.options

        if data.list_rule is not None:
            collection.list_rule = data.list_rule

        if data.view_rule is not None:
            collection.view_rule = data.view_rule

        if data.create_rule is not None:
            collection.create_rule = data.create_rule

        if data.update_rule is not None:
            collection.update_rule = data.update_rule

        if data.delete_rule is not None:
            collection.delete_rule = data.delete_rule

        if data.view_query is not None:
            # Only allow view_query for view collections
            if collection.type != "view":
                raise BadRequestException("view_query can only be set for view collections")
            collection.view_query = data.view_query

            # Recreate the view with new query
            try:
                await self._drop_view(collection.name)
                await self._create_view(collection.name, data.view_query)
                logger.info(f"View '{collection.name}' recreated with updated query")
            except Exception as e:
                raise BadRequestException(f"Failed to update view: {str(e)}")

        collection = await self.repo.update(collection)
        await self.db.commit()

        logger.info(f"Collection '{collection.name}' updated")

        # TODO: Handle schema changes (add/remove columns)
        # For now, we'll just clear the model cache
        if collection.type != "view":
            DynamicModelGenerator.clear_cache(collection.name)

        return self._to_response(collection)

    async def delete_collection(self, collection_id: str) -> None:
        """
        Delete a collection.

        Args:
            collection_id: Collection ID

        Raises:
            NotFoundException: If collection not found
            BadRequestException: If trying to delete system collection
        """
        collection = await self.repo.get_by_id(collection_id)

        if not collection:
            raise NotFoundException(f"Collection with ID '{collection_id}' not found")

        if collection.system:
            raise BadRequestException("Cannot delete system collection")

        # Drop database table or view
        try:
            if collection.type == "view":
                # Drop view for view collections
                await self._drop_view(collection.name)
                logger.info(f"Database view '{collection.name}' dropped")
            else:
                # Drop table for base/auth collections
                model = DynamicModelGenerator.get_model(collection.name)
                if model:
                    await DynamicModelGenerator.drop_table(engine, model)
                    logger.info(f"Database table '{collection.name}' dropped")

                # Clear cache
                DynamicModelGenerator.clear_cache(collection.name)

        except Exception as e:
            logger.warning(f"Failed to drop table/view '{collection.name}': {e}")
            # Continue with collection deletion even if drop fails

        # Delete collection record
        await self.repo.delete(collection)
        await self.db.commit()

        logger.info(f"Collection '{collection.name}' deleted")

    async def _create_view(self, view_name: str, query: str) -> None:
        """
        Create a SQL view.

        Args:
            view_name: Name of the view to create
            query: SQL SELECT query for the view

        Raises:
            BadRequestException: If view creation fails
        """
        from sqlalchemy import text

        # Sanitize view name to prevent SQL injection
        if not view_name.replace("_", "").isalnum():
            raise BadRequestException("Invalid view name")

        # Create view SQL
        create_view_sql = f"CREATE VIEW {view_name} AS {query}"

        try:
            async with engine.begin() as conn:
                await conn.execute(text(create_view_sql))
        except Exception as e:
            logger.error(f"Failed to create view '{view_name}': {e}")
            raise BadRequestException(f"Failed to create view: {str(e)}")

    async def _drop_view(self, view_name: str) -> None:
        """
        Drop a SQL view.

        Args:
            view_name: Name of the view to drop
        """
        from sqlalchemy import text

        # Sanitize view name
        if not view_name.replace("_", "").isalnum():
            return

        drop_view_sql = f"DROP VIEW IF EXISTS {view_name}"

        try:
            async with engine.begin() as conn:
                await conn.execute(text(drop_view_sql))
        except Exception as e:
            logger.warning(f"Failed to drop view '{view_name}': {e}")

    def _to_response(self, collection: Collection) -> CollectionResponse:
        """
        Convert collection model to response schema.

        Args:
            collection: Collection model

        Returns:
            Collection response schema
        """
        # Parse schema from JSON
        fields = [
            FieldSchema(**field_data)
            for field_data in collection.schema.get("fields", [])
        ]

        return CollectionResponse(
            id=collection.id,
            name=collection.name,
            type=collection.type,
            schema=fields,
            options=collection.options,
            list_rule=collection.list_rule,
            view_rule=collection.view_rule,
            create_rule=collection.create_rule,
            update_rule=collection.update_rule,
            delete_rule=collection.delete_rule,
            view_query=collection.view_query,
            system=collection.system,
            created=collection.created,
            updated=collection.updated,
        )

    def _ensure_auth_fields(self, schema: List[FieldSchema]) -> List[FieldSchema]:
        """
        Ensure auth collections have required authentication fields.

        Args:
            schema: Original schema fields

        Returns:
            Schema with auth fields injected
        """
        from app.utils.field_types import FieldSchema, FieldType, FieldValidation

        existing_field_names = {field.name for field in schema}

        # Required auth fields
        required_auth_fields = []

        # Add email field if not exists
        if 'email' not in existing_field_names:
            required_auth_fields.append(FieldSchema(
                name='email',
                type=FieldType.EMAIL,
                validation=FieldValidation(required=True, unique=True),
                label='Email',
                hint='User email address',
                system=True
            ))

        # Add password field if not exists (will be handled specially)
        if 'password' not in existing_field_names:
            required_auth_fields.append(FieldSchema(
                name='password',
                type=FieldType.TEXT,
                validation=FieldValidation(required=True, min_length=8),
                label='Password',
                hint='User password (will be hashed)',
                hidden=True,
                system=True
            ))

        # Add verified field if not exists
        if 'verified' not in existing_field_names:
            required_auth_fields.append(FieldSchema(
                name='verified',
                type=FieldType.BOOL,
                validation=FieldValidation(required=False),
                label='Email Verified',
                hint='Whether email has been verified',
                system=True
            ))

        # Add email_visibility field if not exists
        if 'email_visibility' not in existing_field_names:
            required_auth_fields.append(FieldSchema(
                name='email_visibility',
                type=FieldType.BOOL,
                validation=FieldValidation(required=False),
                label='Email Visibility',
                hint='Whether email is publicly visible',
                system=True
            ))

        # Prepend required fields to the schema
        return required_auth_fields + schema
