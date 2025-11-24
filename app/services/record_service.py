"""Service for record CRUD operations with validation."""
import math
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.db.repositories.record import RecordRepository
from app.db.repositories.collection import CollectionRepository
from app.schemas.record import (
    RecordCreate,
    RecordUpdate,
    RecordResponse,
    RecordListResponse,
    RecordFilter,
)
from app.utils.field_types import FieldSchema, FieldType
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    BadRequestException,
)
from app.core.events import event_manager, Event, EventType
from app.core.access_control import access_control, AccessContext
from app.core.dependencies import UserContext


class RecordService:
    """Service for managing records in dynamic collections."""

    def __init__(
        self, db: AsyncSession, collection_name: str, user_context: Optional[UserContext] = None
    ):
        self.db = db
        self.collection_name = collection_name
        self.user_context = user_context
        self.repo = RecordRepository(db, collection_name)
        self.collection_repo = CollectionRepository(db)

    async def create_record(self, data: RecordCreate) -> RecordResponse:
        """Create a new record with validation."""
        # Get collection schema
        collection = await self.collection_repo.get_by_name(self.collection_name)
        if not collection:
            raise NotFoundException(f"Collection '{self.collection_name}' not found")

        # View collections are read-only
        if collection.type == "view":
            raise BadRequestException(f"Cannot create records in view collection '{self.collection_name}'")

        # Check create permission
        context = self._create_access_context(request_data=data.data)
        access_control.check(collection.create_rule, context, "create")

        # Extract fields from schema
        fields = collection.schema.get("fields", [])
        field_schemas = [FieldSchema(**field) for field in fields]

        # Validate data against schema
        validated_data = self._validate_fields(data.data, field_schemas, is_create=True)

        # Create record
        record = await self.repo.create(validated_data)
        await self.db.commit()

        # Broadcast event
        response = self._to_response(record)
        await event_manager.broadcast(
            Event(
                event_type=EventType.RECORD_CREATED,
                collection_name=self.collection_name,
                record_id=record.id,
                data=response.data,
            )
        )

        return response

    async def get_record(
        self, record_id: str, expand: Optional[List[str]] = None
    ) -> RecordResponse:
        """Get a record by ID with optional relation expansion."""
        record = await self.repo.get_by_id(record_id)
        if not record:
            raise NotFoundException(f"Record '{record_id}' not found")

        # Check view permission
        collection = await self.collection_repo.get_by_name(self.collection_name)
        if collection:
            record_data = self._record_to_dict(record)
            context = self._create_access_context(record_data)
            access_control.check(collection.view_rule, context, "view")

        response = self._to_response(record)

        # Expand relations if requested
        if expand and collection:
            response = await self._expand_relations(response, collection, expand)

        return response

    async def list_records(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[List[RecordFilter]] = None,
        sort: Optional[str] = None,
        order: str = "asc",
        expand: Optional[List[str]] = None,
    ) -> RecordListResponse:
        """List records with pagination, filtering, sorting, and relation expansion."""
        # Validate collection exists
        collection = await self.collection_repo.get_by_name(self.collection_name)
        if not collection:
            raise NotFoundException(f"Collection '{self.collection_name}' not found")

        # Check list permission
        context = self._create_access_context()
        access_control.check(collection.list_rule, context, "list")

        skip = (page - 1) * per_page

        # Get records and total count
        records = await self.repo.get_all(
            skip=skip,
            limit=per_page,
            filters=filters,
            sort_field=sort,
            sort_order=order,
        )
        total = await self.repo.count(filters=filters)

        items = [self._to_response(record) for record in records]

        # Expand relations if requested
        if expand:
            items = await self._expand_relations(items, collection, expand)

        total_pages = math.ceil(total / per_page) if total > 0 else 0

        return RecordListResponse(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
        )

    async def update_record(self, record_id: str, data: RecordUpdate) -> RecordResponse:
        """Update a record with validation."""
        # Check if record exists
        existing = await self.repo.get_by_id(record_id)
        if not existing:
            raise NotFoundException(f"Record '{record_id}' not found")

        # Get collection schema
        collection = await self.collection_repo.get_by_name(self.collection_name)
        if not collection:
            raise NotFoundException(f"Collection '{self.collection_name}' not found")

        # View collections are read-only
        if collection.type == "view":
            raise BadRequestException(f"Cannot update records in view collection '{self.collection_name}'")

        # Check update permission
        record_data = self._record_to_dict(existing)
        context = self._create_access_context(record_data=record_data, request_data=data.data)
        access_control.check(collection.update_rule, context, "update")

        # Extract fields from schema
        fields = collection.schema.get("fields", [])
        field_schemas = [FieldSchema(**field) for field in fields]

        # Validate data against schema
        validated_data = self._validate_fields(data.data, field_schemas, is_create=False)

        # Update record
        updated_record = await self.repo.update(record_id, validated_data)
        await self.db.commit()

        # Broadcast event
        response = self._to_response(updated_record)
        await event_manager.broadcast(
            Event(
                event_type=EventType.RECORD_UPDATED,
                collection_name=self.collection_name,
                record_id=updated_record.id,
                data=response.data,
            )
        )

        return response

    async def delete_record(self, record_id: str) -> None:
        """Delete a record."""
        # Get record before deleting
        record = await self.repo.get_by_id(record_id)
        if not record:
            raise NotFoundException(f"Record '{record_id}' not found")

        # Get collection and check delete permission
        collection = await self.collection_repo.get_by_name(self.collection_name)
        if collection:
            # View collections are read-only
            if collection.type == "view":
                raise BadRequestException(f"Cannot delete records in view collection '{self.collection_name}'")

            record_data = self._record_to_dict(record)
            context = self._create_access_context(record_data)
            access_control.check(collection.delete_rule, context, "delete")

        # Delete record
        success = await self.repo.delete(record_id)
        if not success:
            raise NotFoundException(f"Record '{record_id}' not found")

        await self.db.commit()

        # Broadcast event
        await event_manager.broadcast(
            Event(
                event_type=EventType.RECORD_DELETED,
                collection_name=self.collection_name,
                record_id=record_id,
                data={"id": record_id},
            )
        )

    def _validate_fields(
        self, data: Dict[str, Any], field_schemas: List[FieldSchema], is_create: bool
    ) -> Dict[str, Any]:
        """Validate record data against collection schema."""
        validated = {}
        errors = {}

        # Check required fields (only on create)
        if is_create:
            for field_schema in field_schemas:
                if field_schema.validation.required and field_schema.name not in data:
                    errors[field_schema.name] = "This field is required"

        # Validate provided fields
        for field_name, value in data.items():
            # Find field schema
            field_schema = next(
                (f for f in field_schemas if f.name == field_name), None
            )

            if not field_schema:
                # Ignore unknown fields
                continue

            # Skip validation if value is None and field is not required
            if value is None and not field_schema.validation.required:
                validated[field_name] = None
                continue

            # Skip validation if value is empty string and field is not required (for text-based fields)
            if (
                value == ""
                and not field_schema.validation.required
                and field_schema.type in [FieldType.TEXT, FieldType.EMAIL, FieldType.URL, FieldType.EDITOR]
            ):
                validated[field_name] = None
                continue

            # Validate field
            try:
                validated_value = self._validate_field(value, field_schema)
                validated[field_name] = validated_value
            except ValueError as e:
                errors[field_name] = str(e)

        if errors:
            raise ValidationException("Validation failed", details={"fields": errors})

        return validated

    def _validate_field(self, value: Any, field_schema: FieldSchema) -> Any:
        """Validate a single field value."""
        validation = field_schema.validation

        # Type-specific validation
        if field_schema.type == FieldType.TEXT or field_schema.type == FieldType.EDITOR:
            if not isinstance(value, str):
                raise ValueError("Must be a string")

            if validation.min_length and len(value) < validation.min_length:
                raise ValueError(f"Minimum length is {validation.min_length}")

            if validation.max_length and len(value) > validation.max_length:
                raise ValueError(f"Maximum length is {validation.max_length}")

            if validation.pattern:
                import re
                if not re.match(validation.pattern, value):
                    raise ValueError("Does not match required pattern")

        elif field_schema.type == FieldType.NUMBER:
            if not isinstance(value, (int, float)):
                raise ValueError("Must be a number")

            if validation.min is not None and value < validation.min:
                raise ValueError(f"Minimum value is {validation.min}")

            if validation.max is not None and value > validation.max:
                raise ValueError(f"Maximum value is {validation.max}")

        elif field_schema.type == FieldType.BOOL:
            if not isinstance(value, bool):
                raise ValueError("Must be a boolean")

        elif field_schema.type == FieldType.EMAIL:
            if not isinstance(value, str):
                raise ValueError("Must be a string")
            # Basic email validation
            if "@" not in value or "." not in value:
                raise ValueError("Invalid email format")

        elif field_schema.type == FieldType.URL:
            if not isinstance(value, str):
                raise ValueError("Must be a string")
            if not value.startswith(("http://", "https://")):
                raise ValueError("Invalid URL format")

        elif field_schema.type == FieldType.DATE:
            if isinstance(value, str):
                try:
                    datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    raise ValueError("Invalid date format")
            elif not isinstance(value, datetime):
                raise ValueError("Must be a date string or datetime")

        elif field_schema.type == FieldType.SELECT:
            if validation.values and value not in validation.values:
                raise ValueError(f"Must be one of: {', '.join(validation.values)}")

        elif field_schema.type == FieldType.RELATION:
            if not isinstance(value, str):
                raise ValueError("Must be a string (record ID)")

        elif field_schema.type == FieldType.FILE:
            if not isinstance(value, list):
                raise ValueError("Must be an array of file IDs")

        elif field_schema.type == FieldType.JSON:
            # JSON accepts any structure
            pass

        return value

    def _to_response(self, record) -> RecordResponse:
        """Convert record model to response schema."""
        data = self._record_to_dict(record)
        return RecordResponse(
            id=record.id,
            data=data,
            created=record.created,
            updated=record.updated,
        )

    def _record_to_dict(self, record) -> Dict[str, Any]:
        """Extract record data as dictionary."""
        data = {}
        for key in dir(record):
            if not key.startswith("_") and key not in ["id", "created", "updated", "metadata", "registry"]:
                value = getattr(record, key)
                # Skip SQLAlchemy internal attributes
                if not callable(value) and not key.startswith("_sa_"):
                    data[key] = value
        return data

    async def _expand_relations(
        self,
        responses: List[RecordResponse] | RecordResponse,
        collection: Any,
        expand_fields: List[str],
    ) -> List[RecordResponse] | RecordResponse:
        """
        Expand relation fields in record responses using batch fetching.
        
        Args:
            responses: Single RecordResponse or list of RecordResponses
            collection: Collection model containing schema
            expand_fields: List of field names to expand
            
        Returns:
            Same type as input (single or list) with 'expand' field populated
        """
        is_single = isinstance(responses, RecordResponse)
        items = [responses] if is_single else responses
        
        if not items or not expand_fields:
            return responses

        # Get relation fields from collection schema
        fields = collection.schema.get("fields", [])
        relation_fields = {
            f["name"]: f for f in fields if f.get("type") == "relation"
        }

        # Filter valid expand fields
        valid_expand = [f for f in expand_fields if f in relation_fields]
        if not valid_expand:
            return responses

        # Process each expand field
        for field_name in valid_expand:
            field_config = relation_fields[field_name]
            # Try to get collection from relation options, fallback to validation for backward compat
            target_collection_name = (
                field_config.get("relation", {}).get("collection") or 
                field_config.get("validation", {}).get("collection_name")
            )

            if not target_collection_name:
                continue

            # Collect all IDs to fetch
            ids_to_fetch = set()
            for item in items:
                value = item.data.get(field_name)
                if value:
                    if isinstance(value, list):
                        ids_to_fetch.update(value)
                    else:
                        ids_to_fetch.add(value)

            if not ids_to_fetch:
                continue

            # Batch fetch related records
            try:
                target_repo = RecordRepository(self.db, target_collection_name)
                # We need a way to fetch multiple IDs. 
                # Since get_all supports filters, we can use 'id in [...]'
                
                # Chunk IDs to avoid query limits (e.g. 100 at a time)
                fetched_records = {}
                id_list = list(ids_to_fetch)
                chunk_size = 100
                
                for i in range(0, len(id_list), chunk_size):
                    chunk = id_list[i : i + chunk_size]
                    records = await target_repo.get_all(
                        limit=len(chunk),
                        filters=[RecordFilter(field="id", operator="in", value=chunk)]
                    )
                    for r in records:
                        fetched_records[r.id] = self._to_response(r).model_dump()

                # Map back to items
                for item in items:
                    value = item.data.get(field_name)
                    if not value:
                        continue

                    if item.expand is None:
                        item.expand = {}

                    if isinstance(value, list):
                        item.expand[field_name] = [
                            fetched_records[rid] for rid in value if rid in fetched_records
                        ]
                    else:
                        if value in fetched_records:
                            item.expand[field_name] = fetched_records[value]

            except Exception as e:
                # Log error but don't fail the request
                # logger.warning(f"Failed to expand field {field_name}: {e}")
                pass

        return items[0] if is_single else items

    def _create_access_context(
        self, 
        record_data: Optional[Dict[str, Any]] = None,
        request_data: Optional[Dict[str, Any]] = None
    ) -> AccessContext:
        """Create access context for permission evaluation."""
        return AccessContext(
            user_id=self.user_context.user_id if self.user_context else None,
            user_role=self.user_context.role if self.user_context else "user",
            record_data=record_data,
            request_data=request_data,
        )
