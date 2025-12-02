"""
Query parser for advanced filtering and sorting.
Supports filter syntax with AND (&&) and OR (||) operators.
"""

import re
from typing import Any, Dict, List, Optional, Union

from app.schemas.record import RecordFilter


class FilterGroup:
    """Represents a group of filters with logical operators."""

    def __init__(self, operator: str = "AND"):
        """
        Initialize filter group.

        Args:
            operator: Logical operator ('AND' or 'OR')
        """
        self.operator = operator  # 'AND' or 'OR'
        self.filters: List[Union[RecordFilter, "FilterGroup"]] = []

    def add_filter(self, filter_obj: Union[RecordFilter, "FilterGroup"]):
        """Add a filter or subgroup to this group."""
        self.filters.append(filter_obj)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "operator": self.operator,
            "filters": [
                f.to_dict() if isinstance(f, FilterGroup) else f.dict()
                for f in self.filters
            ],
        }


class QueryParser:
    """Parse query strings for filtering and sorting."""

    OPERATOR_MAP = {
        "=": "eq",
        "!=": "ne",
        ">": "gt",
        "<": "lt",
        ">=": "gte",
        "<=": "lte",
        "~": "like",
        "?=": "in",
    }

    @classmethod
    def parse_filter(cls, filter_string: str) -> Union[List[RecordFilter], FilterGroup]:
        """
        Parse filter string into RecordFilter objects or FilterGroup.

        Supported formats:
        - field=value
        - field>value
        - field<value
        - field>=value
        - field<=value
        - field!=value
        - field~value (LIKE)
        - Multiple filters with &&: age>=18&&status=active (AND)
        - Multiple filters with ||: age>=18||status=active (OR)
        - Mixed: (age>=18&&status=active)||(age<10) (grouped)

        Args:
            filter_string: Filter expression

        Returns:
            List of RecordFilter objects (simple case) or FilterGroup (complex case)
        """
        if not filter_string or not filter_string.strip():
            return []

        # Check if expression contains OR operator
        if "||" in filter_string:
            return cls._parse_complex_filter(filter_string)

        # Simple case: only AND operators
        return cls._parse_simple_and_filter(filter_string)

    @classmethod
    def _parse_simple_and_filter(cls, filter_string: str) -> List[RecordFilter]:
        """Parse simple AND-only filter expressions."""
        filters: List[RecordFilter] = []

        # Split by && (AND operator)
        parts = filter_string.split("&&")

        for part in parts:
            part = part.strip()
            if not part:
                continue

            filter_obj = cls._parse_single_filter(part)
            if filter_obj:
                filters.append(filter_obj)

        return filters

    @classmethod
    def _parse_complex_filter(cls, filter_string: str) -> FilterGroup:
        """
        Parse complex filter expressions with OR operators.

        This handles expressions like:
        - age>=18||status=active (simple OR)
        - (age>=18&&status=active)||(age<10) (grouped OR with AND)
        """
        # First split by || to get OR groups
        or_parts = filter_string.split("||")

        if len(or_parts) == 1:
            # No OR, just return AND group
            root_group = FilterGroup("AND")
            filters = cls._parse_simple_and_filter(or_parts[0])
            for f in filters:
                root_group.add_filter(f)
            return root_group

        # Multiple OR parts
        root_group = FilterGroup("OR")

        for or_part in or_parts:
            or_part = or_part.strip()
            if not or_part:
                continue

            # Check if this part has AND operators
            if "&&" in or_part:
                # Create an AND subgroup
                and_group = FilterGroup("AND")
                and_filters = cls._parse_simple_and_filter(or_part)
                for f in and_filters:
                    and_group.add_filter(f)
                root_group.add_filter(and_group)
            else:
                # Single filter in this OR part
                filter_obj = cls._parse_single_filter(or_part)
                if filter_obj:
                    root_group.add_filter(filter_obj)

        return root_group

    @classmethod
    def _parse_single_filter(cls, filter_expr: str) -> Optional[RecordFilter]:
        """
        Parse a single filter expression.

        Args:
            filter_expr: Single filter like "age>=18"

        Returns:
            RecordFilter object or None if invalid
        """
        filter_expr = filter_expr.strip()

        # Remove parentheses if present
        if filter_expr.startswith("(") and filter_expr.endswith(")"):
            filter_expr = filter_expr[1:-1].strip()

        # Match pattern: field operator value
        # Operators: >=, <=, !=, =, >, <, ~, ?=
        pattern = r"^(\w+)\s*(>=|<=|!=|\?=|=|>|<|~)\s*(.+)$"
        match = re.match(pattern, filter_expr)

        if not match:
            return None

        field, operator, value_str = match.groups()

        # Map operator to internal format
        operator_internal = cls.OPERATOR_MAP.get(operator)
        if not operator_internal:
            return None

        # Parse value
        value = cls._parse_value(value_str.strip())

        return RecordFilter(field=field, operator=operator_internal, value=value)

    @classmethod
    def _parse_value(cls, value_str: str) -> Any:
        """Parse value string to appropriate type."""
        # Remove quotes if present
        if (value_str.startswith('"') and value_str.endswith('"')) or (
            value_str.startswith("'") and value_str.endswith("'")
        ):
            return value_str[1:-1]

        # Boolean
        if value_str.lower() == "true":
            return True
        if value_str.lower() == "false":
            return False

        # Null
        if value_str.lower() in ("null", "none"):
            return None

        # Number
        try:
            if "." in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            pass

        # Default to string
        return value_str

    @classmethod
    def parse_sort(cls, sort_string: str) -> tuple[Optional[str], str]:
        """
        Parse sort string.

        Formats:
        - field (ascending)
        - -field (descending)
        - +field (ascending)

        Args:
            sort_string: Sort expression

        Returns:
            Tuple of (field, order)
        """
        if not sort_string or not sort_string.strip():
            return None, "asc"

        sort_string = sort_string.strip()

        if sort_string.startswith("-"):
            return sort_string[1:], "desc"
        elif sort_string.startswith("+"):
            return sort_string[1:], "asc"
        else:
            return sort_string, "asc"
