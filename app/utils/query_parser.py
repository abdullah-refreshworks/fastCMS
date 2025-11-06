"""
Query parser for advanced filtering and sorting.
Supports PocketBase-like filter syntax.
"""

import re
from typing import Any, List, Optional

from app.schemas.record import RecordFilter


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
    def parse_filter(cls, filter_string: str) -> List[RecordFilter]:
        """
        Parse filter string into RecordFilter objects.

        Supported formats:
        - field=value
        - field>value
        - field<value
        - field>=value
        - field<=value
        - field!=value
        - field~value (LIKE)
        - Multiple filters with &&: age>=18&&status=active

        Args:
            filter_string: Filter expression

        Returns:
            List of RecordFilter objects
        """
        if not filter_string or not filter_string.strip():
            return []

        filters: List[RecordFilter] = []

        # Split by && (AND operator)
        parts = filter_string.split("&&")

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Match pattern: field operator value
            # Operators: >=, <=, !=, =, >, <, ~
            pattern = r"^(\w+)\s*(>=|<=|!=|=|>|<|~)\s*(.+)$"
            match = re.match(pattern, part)

            if not match:
                continue

            field, operator, value_str = match.groups()

            # Map operator to internal format
            operator_internal = cls.OPERATOR_MAP.get(operator)
            if not operator_internal:
                continue

            # Parse value
            value = cls._parse_value(value_str.strip())

            filters.append(
                RecordFilter(field=field, operator=operator_internal, value=value)
            )

        return filters

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
