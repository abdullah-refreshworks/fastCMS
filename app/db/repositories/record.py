"""Repository for dynamic record operations."""
import math
from typing import Any, Dict, List, Optional, Type, Union
from sqlalchemy import select, func, and_, or_, asc, desc, text, cast, JSON
from sqlalchemy.sql.expression import func as sql_func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.dynamic import DynamicModelGenerator
from app.db.models.base import BaseModel
from app.schemas.record import RecordFilter
from app.utils.query_parser import FilterGroup, GeoDistanceFilter, NestedRelationFilter, QueryParser


class RecordRepository:
    """Repository for CRUD operations on dynamic collection records."""

    def __init__(self, db: AsyncSession, collection_name: str):
        self.db = db
        self.collection_name = collection_name
        self.model: Optional[Type[BaseModel]] = None

    async def _get_model(self) -> Type[BaseModel]:
        """Get or cache the dynamic model for this collection."""
        if self.model is None:
            # Try to get from cache first
            self.model = DynamicModelGenerator.get_model(self.collection_name)

            # If not in cache, regenerate from database
            if self.model is None:
                from app.db.repositories.collection import CollectionRepository

                collection_repo = CollectionRepository(self.db)
                collection = await collection_repo.get_by_name(self.collection_name)

                if collection is None:
                    raise ValueError(f"Collection '{self.collection_name}' does not exist")

                # Extract field schemas from collection
                from app.utils.field_types import FieldSchema
                fields = [FieldSchema(**field_data) for field_data in collection.schema.get("fields", [])]

                # Create and cache the model
                self.model = DynamicModelGenerator.create_model(
                    collection_name=self.collection_name,
                    fields=fields,
                )

        return self.model

    async def create(self, data: Dict[str, Any]) -> BaseModel:
        """Create a new record."""
        model = await self._get_model()
        record = model(**data)
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record

    async def get_by_id(self, record_id: str) -> Optional[BaseModel]:
        """Get a record by ID."""
        model = await self._get_model()
        result = await self.db.execute(
            select(model).where(model.id == record_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[Union[List[RecordFilter], FilterGroup]] = None,
        sort_field: Optional[str] = None,
        sort_order: str = "asc",
        search: Optional[str] = None,
        search_fields: Optional[List[str]] = None,
        sort_fields: Optional[List[tuple]] = None,
    ) -> List[BaseModel]:
        """
        Get all records with optional filtering, sorting, and full-text search.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: RecordFilter list or FilterGroup for complex queries
            sort_field: Single sort field (deprecated, use sort_fields)
            sort_order: Single sort order (deprecated, use sort_fields)
            search: Full-text search term
            search_fields: Fields to search in
            sort_fields: List of (field, order) tuples for multi-field sorting
                         Supports @random for random order
        """
        model = await self._get_model()
        query = select(model)

        # Apply full-text search
        if search and search_fields:
            query = self._apply_search(query, model, search, search_fields)

        # Apply filters (supports both simple list and complex FilterGroup)
        if filters:
            if isinstance(filters, FilterGroup):
                condition = self._build_filter_condition(model, filters)
                if condition is not None:
                    query = query.where(condition)
            elif isinstance(filters, list):
                query = self._apply_filters(query, model, filters)

        # Apply sorting (multi-field support)
        query = self._apply_sorting(query, model, sort_fields, sort_field, sort_order)

        # Apply pagination
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    def _apply_sorting(
        self,
        query,
        model: Type[BaseModel],
        sort_fields: Optional[List[tuple]] = None,
        sort_field: Optional[str] = None,
        sort_order: str = "asc"
    ):
        """
        Apply sorting to query.

        Args:
            query: SQLAlchemy query
            model: Dynamic model class
            sort_fields: List of (field, order) tuples for multi-field sorting
            sort_field: Single sort field (backwards compatibility)
            sort_order: Single sort order (backwards compatibility)

        Special sort fields:
            @random: Random order using database RANDOM()
            @rowid: Sort by internal row ID (SQLite rowid)

        Nested relation sort:
            author.name: Sort by related record's field using LEFT JOIN
        """
        # Handle multi-field sorting
        if sort_fields:
            order_clauses = []
            for field, order in sort_fields:
                # Handle @random special case
                if field == "@random":
                    order_clauses.append(sql_func.random())
                # Handle @rowid special case (SQLite rowid for efficient pagination)
                elif field == "@rowid":
                    rowid_col = text("rowid")
                    order_clauses.append(desc(rowid_col) if order == "desc" else asc(rowid_col))
                # Handle nested relation sort (e.g., author.name)
                elif "." in field:
                    nested_clause = self._build_nested_sort_clause(model, field, order, query)
                    if nested_clause is not None:
                        clause, updated_query = nested_clause
                        query = updated_query
                        order_clauses.append(clause)
                elif hasattr(model, field):
                    col = getattr(model, field)
                    order_clauses.append(desc(col) if order == "desc" else asc(col))

            if order_clauses:
                query = query.order_by(*order_clauses)
                return query

        # Backwards compatibility: single field sorting
        if sort_field:
            if sort_field == "@random":
                query = query.order_by(sql_func.random())
            elif sort_field == "@rowid":
                rowid_col = text("rowid")
                query = query.order_by(desc(rowid_col) if sort_order == "desc" else asc(rowid_col))
            # Handle nested relation sort for single field
            elif "." in sort_field:
                nested_clause = self._build_nested_sort_clause(model, sort_field, sort_order, query)
                if nested_clause is not None:
                    clause, query = nested_clause
                    query = query.order_by(clause)
                return query
            elif hasattr(model, sort_field):
                sort_col = getattr(model, sort_field)
                query = query.order_by(desc(sort_col) if sort_order == "desc" else asc(sort_col))
            return query

        # Default sort by created desc
        query = query.order_by(desc(model.created))
        return query

    def _build_nested_sort_clause(
        self,
        model: Type[BaseModel],
        field_path: str,
        order: str,
        query
    ) -> Optional[tuple]:
        """
        Build a sort clause for nested relation fields.

        For example, `author.name` will join with the author table and sort by name.
        Uses a scalar subquery to get the sort value without changing result count.

        Args:
            model: Dynamic model class
            field_path: Dotted field path like "author.name"
            order: Sort order ("asc" or "desc")
            query: Current query object

        Returns:
            Tuple of (order_clause, updated_query) or None if field path is invalid
        """
        parts = field_path.split(".")
        if len(parts) != 2:
            # Only support single-level nesting for now (author.name)
            # Multi-level (author.company.name) would require multiple joins
            return None

        relation_field, target_field = parts

        # Check if the relation field exists on the model
        if not hasattr(model, relation_field):
            return None

        # Build a scalar subquery to get the sort value
        # This avoids JOINs that could multiply results for multi-valued relations
        # SQL: (SELECT target_field FROM relation_table WHERE id = main.relation_field)
        relation_col = getattr(model, relation_field)

        # Build the subquery - assumes the related table name matches the relation field
        # In a full implementation, we'd look up the actual target collection from schema
        subquery_sql = f"""
            (SELECT {target_field} FROM {relation_field} WHERE id = {self.collection_name}.{relation_field})
        """

        # Create the order clause using the subquery
        sort_expr = text(subquery_sql)

        if order == "desc":
            order_clause = desc(sort_expr)
        else:
            order_clause = asc(sort_expr)

        return (order_clause, query)

    async def count(
        self,
        filters: Optional[Union[List[RecordFilter], FilterGroup]] = None,
        search: Optional[str] = None,
        search_fields: Optional[List[str]] = None,
    ) -> int:
        """Count records with optional filtering and search."""
        model = await self._get_model()
        query = select(func.count(model.id))

        # Apply full-text search
        if search and search_fields:
            query = self._apply_search(query, model, search, search_fields)

        # Apply filters (supports both simple list and complex FilterGroup)
        if filters:
            if isinstance(filters, FilterGroup):
                condition = self._build_filter_condition(model, filters)
                if condition is not None:
                    query = query.where(condition)
            elif isinstance(filters, list):
                query = self._apply_filters(query, model, filters)

        result = await self.db.execute(query)
        return result.scalar_one()

    async def update(self, record_id: str, data: Dict[str, Any]) -> Optional[BaseModel]:
        """Update a record."""
        record = await self.get_by_id(record_id)
        if not record:
            return None

        for key, value in data.items():
            if hasattr(record, key):
                setattr(record, key, value)

        await self.db.flush()
        await self.db.refresh(record)
        return record

    async def delete(self, record_id: str) -> bool:
        """Delete a record."""
        record = await self.get_by_id(record_id)
        if not record:
            return False

        await self.db.delete(record)
        await self.db.flush()
        return True

    def _apply_filters(self, query, model: Type[BaseModel], filters: List[Union[RecordFilter, GeoDistanceFilter, NestedRelationFilter]]):
        """
        Apply filters to query.

        Supported operators:
        - eq: Equal (=)
        - ne: Not equal (!=)
        - gt: Greater than (>)
        - lt: Less than (<)
        - gte: Greater than or equal (>=)
        - lte: Less than or equal (<=)
        - like: Contains (~)
        - not_like: Does not contain (!~)
        - in: Any equal from list (?=)
        - any_eq: Alias for in
        - any_ne: Not any equal (?!=)
        - any_gt: Any greater than (?>)
        - any_lt: Any less than (?<)
        - any_gte: Any greater than or equal (?>=)
        - any_lte: Any less than or equal (?<=)
        - any_like: Any like (?~)
        - any_not_like: Any not like (?!~)

        Also supports:
        - GeoDistanceFilter for location-based queries
        - NestedRelationFilter for filtering by related record fields
        """
        conditions = []

        for f in filters:
            # Handle GeoDistanceFilter
            if isinstance(f, GeoDistanceFilter):
                condition = self._build_geo_distance_condition(model, f)
                if condition is not None:
                    conditions.append(condition)
                continue

            # Handle NestedRelationFilter
            if isinstance(f, NestedRelationFilter):
                condition = self._build_nested_relation_condition(model, f)
                if condition is not None:
                    conditions.append(condition)
                continue

            if not hasattr(model, f.field):
                continue

            field = getattr(model, f.field)

            # Standard operators
            if f.operator == "eq":
                conditions.append(field == f.value)
            elif f.operator == "ne":
                conditions.append(field != f.value)
            elif f.operator == "gt":
                conditions.append(field > f.value)
            elif f.operator == "lt":
                conditions.append(field < f.value)
            elif f.operator == "gte":
                conditions.append(field >= f.value)
            elif f.operator == "lte":
                conditions.append(field <= f.value)
            elif f.operator == "like":
                conditions.append(field.ilike(f"%{f.value}%"))  # Case-insensitive
            elif f.operator == "not_like":
                conditions.append(~field.ilike(f"%{f.value}%"))  # Case-insensitive NOT LIKE

            # Array/Any operators - for checking if field value is in provided list
            elif f.operator in ("in", "any_eq"):
                if isinstance(f.value, list):
                    conditions.append(field.in_(f.value))
                else:
                    conditions.append(field == f.value)
            elif f.operator == "any_ne":
                if isinstance(f.value, list):
                    conditions.append(~field.in_(f.value))
                else:
                    conditions.append(field != f.value)
            elif f.operator == "any_gt":
                # Field must be greater than at least one value in the list
                if isinstance(f.value, list):
                    sub_conditions = [field > v for v in f.value]
                    conditions.append(or_(*sub_conditions))
                else:
                    conditions.append(field > f.value)
            elif f.operator == "any_lt":
                if isinstance(f.value, list):
                    sub_conditions = [field < v for v in f.value]
                    conditions.append(or_(*sub_conditions))
                else:
                    conditions.append(field < f.value)
            elif f.operator == "any_gte":
                if isinstance(f.value, list):
                    sub_conditions = [field >= v for v in f.value]
                    conditions.append(or_(*sub_conditions))
                else:
                    conditions.append(field >= f.value)
            elif f.operator == "any_lte":
                if isinstance(f.value, list):
                    sub_conditions = [field <= v for v in f.value]
                    conditions.append(or_(*sub_conditions))
                else:
                    conditions.append(field <= f.value)
            elif f.operator == "any_like":
                if isinstance(f.value, list):
                    sub_conditions = [field.ilike(f"%{v}%") for v in f.value]
                    conditions.append(or_(*sub_conditions))
                else:
                    conditions.append(field.ilike(f"%{f.value}%"))
            elif f.operator == "any_not_like":
                if isinstance(f.value, list):
                    sub_conditions = [~field.ilike(f"%{v}%") for v in f.value]
                    conditions.append(and_(*sub_conditions))  # Must NOT match ALL values
                else:
                    conditions.append(~field.ilike(f"%{f.value}%"))

        if conditions:
            query = query.where(and_(*conditions))

        return query

    def _build_filter_condition(self, model: Type[BaseModel], filter_group: FilterGroup) -> Optional[Any]:
        """
        Build SQLAlchemy condition from a FilterGroup (supports nested AND/OR).

        Args:
            model: Dynamic model class
            filter_group: FilterGroup containing filters and subgroups

        Returns:
            SQLAlchemy condition or None if no valid conditions
        """
        conditions = []

        for item in filter_group.filters:
            if isinstance(item, FilterGroup):
                # Recursively build nested condition
                sub_condition = self._build_filter_condition(model, item)
                if sub_condition is not None:
                    conditions.append(sub_condition)
            elif isinstance(item, GeoDistanceFilter):
                # Build geo distance condition
                condition = self._build_geo_distance_condition(model, item)
                if condition is not None:
                    conditions.append(condition)
            elif isinstance(item, NestedRelationFilter):
                # Build nested relation filter condition
                condition = self._build_nested_relation_condition(model, item)
                if condition is not None:
                    conditions.append(condition)
            elif isinstance(item, RecordFilter):
                # Build single filter condition
                condition = self._build_single_condition(model, item)
                if condition is not None:
                    conditions.append(condition)

        if not conditions:
            return None

        # Combine conditions with AND or OR
        if filter_group.operator == "AND":
            return and_(*conditions) if len(conditions) > 1 else conditions[0]
        else:  # OR
            return or_(*conditions) if len(conditions) > 1 else conditions[0]

    def _build_single_condition(self, model: Type[BaseModel], f: RecordFilter) -> Optional[Any]:
        """Build a single SQLAlchemy condition from a RecordFilter."""
        if not hasattr(model, f.field):
            return None

        field = getattr(model, f.field)

        if f.operator == "eq":
            return field == f.value
        elif f.operator == "ne":
            return field != f.value
        elif f.operator == "gt":
            return field > f.value
        elif f.operator == "lt":
            return field < f.value
        elif f.operator == "gte":
            return field >= f.value
        elif f.operator == "lte":
            return field <= f.value
        elif f.operator == "like":
            return field.ilike(f"%{f.value}%")
        elif f.operator == "not_like":
            return ~field.ilike(f"%{f.value}%")
        elif f.operator in ("in", "any_eq"):
            if isinstance(f.value, list):
                return field.in_(f.value)
            return field == f.value
        elif f.operator == "any_ne":
            if isinstance(f.value, list):
                return ~field.in_(f.value)
            return field != f.value
        elif f.operator == "any_gt":
            if isinstance(f.value, list):
                return or_(*[field > v for v in f.value])
            return field > f.value
        elif f.operator == "any_lt":
            if isinstance(f.value, list):
                return or_(*[field < v for v in f.value])
            return field < f.value
        elif f.operator == "any_gte":
            if isinstance(f.value, list):
                return or_(*[field >= v for v in f.value])
            return field >= f.value
        elif f.operator == "any_lte":
            if isinstance(f.value, list):
                return or_(*[field <= v for v in f.value])
            return field <= f.value
        elif f.operator == "any_like":
            if isinstance(f.value, list):
                return or_(*[field.ilike(f"%{v}%") for v in f.value])
            return field.ilike(f"%{f.value}%")
        elif f.operator == "any_not_like":
            if isinstance(f.value, list):
                return and_(*[~field.ilike(f"%{v}%") for v in f.value])
            return ~field.ilike(f"%{f.value}%")

        return None

    def _apply_search(self, query, model: Type[BaseModel], search_term: str, search_fields: List[str]):
        """
        Apply full-text search across multiple fields using OR conditions.

        Args:
            query: SQLAlchemy query
            model: Dynamic model class
            search_term: Search string
            search_fields: List of field names to search

        Returns:
            Modified query with search conditions
        """
        search_conditions = []

        for field_name in search_fields:
            if hasattr(model, field_name):
                field = getattr(model, field_name)
                # Use case-insensitive LIKE search
                search_conditions.append(field.like(f"%{search_term}%"))

        if search_conditions:
            # OR all search conditions together
            query = query.where(or_(*search_conditions))

        return query

    def _build_geo_distance_condition(self, model: Type[BaseModel], geo_filter: GeoDistanceFilter) -> Optional[Any]:
        """
        Build SQLAlchemy condition for geoDistance filter.

        Uses the Haversine formula to calculate distance between two points.
        For SQLite, we use a simplified Pythagorean approximation since SQLite
        doesn't have trig functions by default. For more accurate results,
        consider using SpatiaLite extension.

        Args:
            model: Dynamic model class
            geo_filter: GeoDistanceFilter with field, lat, lng, distance, unit

        Returns:
            SQLAlchemy condition or None
        """
        if not hasattr(model, geo_filter.field):
            return None

        # Convert distance to kilometers if needed
        distance_km = geo_filter.distance
        if geo_filter.unit == "mi":
            distance_km = geo_filter.distance * 1.60934

        # For SQLite/simple databases, we use a bounding box approximation
        # then filter with actual distance calculation
        # 1 degree lat = ~111km, 1 degree lng = ~111km * cos(lat)
        lat_rad = math.radians(geo_filter.lat)
        lat_delta = distance_km / 111.0
        lng_delta = distance_km / (111.0 * math.cos(lat_rad))

        field = getattr(model, geo_filter.field)

        # Build bounding box condition using JSON extraction
        # SQLite JSON: json_extract(field, '$.lat')
        # PostgreSQL: field->>'lat'
        # We'll use text() for portability

        # Extract lat/lng from JSON field
        lat_extract = text(f"json_extract({geo_filter.field}, '$.lat')")
        lng_extract = text(f"json_extract({geo_filter.field}, '$.lng')")

        # Bounding box conditions
        min_lat = geo_filter.lat - lat_delta
        max_lat = geo_filter.lat + lat_delta
        min_lng = geo_filter.lng - lng_delta
        max_lng = geo_filter.lng + lng_delta

        bounding_box = and_(
            lat_extract >= min_lat,
            lat_extract <= max_lat,
            lng_extract >= min_lng,
            lng_extract <= max_lng,
        )

        # For the actual distance, we'd need a more complex SQL expression
        # For now, use the bounding box as an approximation
        # In production, you'd want to use PostGIS or SpatiaLite

        if geo_filter.operator == "lte":
            return bounding_box
        elif geo_filter.operator == "lt":
            return bounding_box
        elif geo_filter.operator == "gte":
            # Inverse - records OUTSIDE the bounding box
            return or_(
                lat_extract < min_lat,
                lat_extract > max_lat,
                lng_extract < min_lng,
                lng_extract > max_lng,
            )
        elif geo_filter.operator == "gt":
            return or_(
                lat_extract < min_lat,
                lat_extract > max_lat,
                lng_extract < min_lng,
                lng_extract > max_lng,
            )

        return bounding_box

    def _build_nested_relation_condition(self, model: Type[BaseModel], nested_filter: NestedRelationFilter) -> Optional[Any]:
        """
        Build SQLAlchemy condition for nested relation filter.

        This creates a subquery that filters the main table based on values
        in a related table. For example, `author.name = "John"` will find
        all records where the related author has name "John".

        Args:
            model: Dynamic model class for the main collection
            nested_filter: NestedRelationFilter with relation_path, target_field, operator, value

        Returns:
            SQLAlchemy condition or None if relation cannot be resolved
        """
        # Get the relation field name (first part of the path)
        relation_field = nested_filter.relation_field

        # Check if the relation field exists on the model
        if not hasattr(model, relation_field):
            return None

        # For nested relation filters, we need to:
        # 1. Get the target collection name from the schema (requires collection lookup)
        # 2. Build a subquery to filter by the related record's field
        #
        # Since we don't have direct access to the collection schema here,
        # we'll use a raw SQL subquery approach that's schema-aware
        #
        # The SQL looks like:
        # SELECT * FROM main_table
        # WHERE relation_field IN (
        #     SELECT id FROM related_table WHERE target_field = value
        # )

        # Build the subquery using raw SQL
        # We assume the related table name is the relation field name (convention)
        # In a more complete implementation, we'd look up the actual target collection

        # For now, use a simplified approach that works for single-level relations
        # The relation field stores the ID of the related record
        # We need to build: relation_field IN (SELECT id FROM related_table WHERE target_field op value)

        # Build the operator comparison
        op = nested_filter.operator
        value = nested_filter.value
        target_field = nested_filter.target_field

        # Get the local relation column
        relation_col = getattr(model, relation_field)

        # For simple cases where the target collection name matches the relation field,
        # we can build a subquery. For more complex cases, we'd need schema lookup.

        # Build subquery condition using text() for flexibility
        # This assumes the related table name equals the relation field name
        # In production, you'd want to look up the actual target collection

        if op == "eq":
            if isinstance(value, str):
                # Use LIKE for case-insensitive string matching in subquery
                subquery_sql = f"SELECT id FROM {relation_field} WHERE {target_field} = :val"
            else:
                subquery_sql = f"SELECT id FROM {relation_field} WHERE {target_field} = :val"
        elif op == "ne":
            subquery_sql = f"SELECT id FROM {relation_field} WHERE {target_field} != :val"
        elif op == "gt":
            subquery_sql = f"SELECT id FROM {relation_field} WHERE {target_field} > :val"
        elif op == "gte":
            subquery_sql = f"SELECT id FROM {relation_field} WHERE {target_field} >= :val"
        elif op == "lt":
            subquery_sql = f"SELECT id FROM {relation_field} WHERE {target_field} < :val"
        elif op == "lte":
            subquery_sql = f"SELECT id FROM {relation_field} WHERE {target_field} <= :val"
        elif op == "like":
            subquery_sql = f"SELECT id FROM {relation_field} WHERE {target_field} LIKE :val"
            value = f"%{value}%"  # Add wildcards for LIKE
        elif op == "not_like":
            subquery_sql = f"SELECT id FROM {relation_field} WHERE {target_field} NOT LIKE :val"
            value = f"%{value}%"
        else:
            return None

        # Build the IN condition with the subquery
        subquery = text(subquery_sql).bindparams(val=value)
        return relation_col.in_(select(text("id")).select_from(text(f"({subquery_sql}) AS sub")).params(val=value))

    async def _build_nested_relation_condition_with_schema(
        self,
        model: Type[BaseModel],
        nested_filter: NestedRelationFilter,
        collection_schema: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Build nested relation condition with full schema awareness.

        This is the full implementation that looks up the target collection
        from the schema. Call this from the service layer where schema is available.

        Args:
            model: Dynamic model class
            nested_filter: NestedRelationFilter
            collection_schema: Collection schema dict with fields

        Returns:
            SQLAlchemy condition or None
        """
        relation_field = nested_filter.relation_field

        # Look up the relation field in the schema
        fields = collection_schema.get("fields", [])
        relation_config = None
        for field in fields:
            if field.get("name") == relation_field and field.get("type") == "relation":
                relation_config = field
                break

        if not relation_config:
            return None

        # Get target collection name
        target_collection = (
            relation_config.get("relation", {}).get("collection") or
            relation_config.get("validation", {}).get("collection_name")
        )

        if not target_collection:
            return None

        # Now build the subquery with the correct target table
        return self._build_relation_subquery(
            model,
            relation_field,
            target_collection,
            nested_filter.target_field,
            nested_filter.operator,
            nested_filter.value,
        )

    def _build_relation_subquery(
        self,
        model: Type[BaseModel],
        relation_field: str,
        target_table: str,
        target_field: str,
        operator: str,
        value: Any,
    ) -> Optional[Any]:
        """
        Build a subquery condition for relation filtering.

        Args:
            model: Main collection model
            relation_field: Field name containing the relation ID
            target_table: Target collection/table name
            target_field: Field to filter on in the target table
            operator: Filter operator
            value: Filter value

        Returns:
            SQLAlchemy condition
        """
        relation_col = getattr(model, relation_field, None)
        if relation_col is None:
            return None

        # Build comparison for the subquery
        op_map = {
            "eq": "=",
            "ne": "!=",
            "gt": ">",
            "gte": ">=",
            "lt": "<",
            "lte": "<=",
            "like": "LIKE",
            "not_like": "NOT LIKE",
        }

        sql_op = op_map.get(operator, "=")

        # Handle LIKE operator value formatting
        if operator in ("like", "not_like"):
            value = f"%{value}%"

        # Build the subquery
        subquery_sql = f"SELECT id FROM {target_table} WHERE {target_field} {sql_op} :filter_value"

        # Return IN condition
        from sqlalchemy import literal_column
        subquery = text(subquery_sql).bindparams(filter_value=value)

        # Use a scalar subquery
        return relation_col.in_(
            select(literal_column("id")).select_from(
                text(target_table)
            ).where(
                text(f"{target_field} {sql_op} :filter_value").bindparams(filter_value=value)
            )
        )
