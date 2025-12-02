"""Service for CSV import/export operations."""
import csv
import io
import json
from typing import Any, Dict, List
from datetime import datetime

from app.utils.field_types import FieldSchema, FieldType
from app.core.exceptions import ValidationException


class CSVService:
    """Service for handling CSV import and export of collection records."""

    @staticmethod
    def export_to_csv(records: List[Dict[str, Any]], fields: List[FieldSchema]) -> str:
        """
        Export records to CSV format.

        Args:
            records: List of record dictionaries
            fields: Collection field schemas

        Returns:
            CSV string
        """
        if not records:
            # Return empty CSV with headers only
            field_names = [field.name for field in fields]
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=field_names)
            writer.writeheader()
            return output.getvalue()

        # Get all unique field names from schema
        field_names = [field.name for field in fields]

        # Add system fields that are always present
        system_fields = ["id", "created", "updated"]
        all_fields = system_fields + field_names

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=all_fields, extrasaction='ignore')
        writer.writeheader()

        for record in records:
            # Convert datetime objects to ISO format strings
            row = {}
            for key, value in record.items():
                if isinstance(value, datetime):
                    row[key] = value.isoformat()
                elif value is None:
                    row[key] = ""
                elif isinstance(value, (list, dict)):
                    # Convert complex types to JSON string
                    row[key] = json.dumps(value)
                else:
                    row[key] = value
            writer.writerow(row)

        return output.getvalue()

    @staticmethod
    def parse_csv(
        csv_content: str, fields: List[FieldSchema], skip_validation: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Parse CSV content and return list of record dictionaries.

        Args:
            csv_content: CSV string content
            fields: Collection field schemas for validation
            skip_validation: If True, skip field type validation

        Returns:
            List of record dictionaries

        Raises:
            ValidationException: If CSV format is invalid or data doesn't match schema
        """
        try:
            input_io = io.StringIO(csv_content)
            reader = csv.DictReader(input_io)

            if not reader.fieldnames:
                raise ValidationException("CSV file is empty or has no headers")

            records = []
            field_map = {field.name: field for field in fields}

            # System fields to exclude from import
            system_fields = {"id", "created", "updated"}

            for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
                record_data = {}

                for field_name, value in row.items():
                    # Skip system fields
                    if field_name in system_fields:
                        continue

                    # Skip empty values
                    if value == "" or value is None:
                        continue

                    # Get field schema
                    field_schema = field_map.get(field_name)
                    if not field_schema:
                        # Unknown field - skip it
                        continue

                    # Convert value based on field type
                    try:
                        converted_value = CSVService._convert_csv_value(
                            value, field_schema, skip_validation
                        )
                        record_data[field_name] = converted_value
                    except ValueError as e:
                        raise ValidationException(
                            f"Row {row_num}, field '{field_name}': {str(e)}"
                        )

                if record_data:  # Only add non-empty records
                    records.append(record_data)

            return records

        except csv.Error as e:
            raise ValidationException(f"CSV parsing error: {str(e)}")

    @staticmethod
    def _convert_csv_value(
        value: str, field_schema: FieldSchema, skip_validation: bool
    ) -> Any:
        """
        Convert CSV string value to appropriate Python type based on field schema.

        Args:
            value: String value from CSV
            field_schema: Field schema defining the expected type
            skip_validation: If True, return value as-is

        Returns:
            Converted value

        Raises:
            ValueError: If conversion fails
        """
        if skip_validation:
            return value

        field_type = field_schema.type

        try:
            if field_type == FieldType.TEXT:
                return str(value)

            elif field_type == FieldType.NUMBER:
                # Try integer first, then float
                if "." in value:
                    return float(value)
                return int(value)

            elif field_type == FieldType.BOOL:
                value_lower = value.lower().strip()
                if value_lower in ("true", "1", "yes", "y"):
                    return True
                elif value_lower in ("false", "0", "no", "n"):
                    return False
                else:
                    raise ValueError(f"Invalid boolean value: {value}")

            elif field_type == FieldType.EMAIL:
                return str(value)  # Email validation happens in record service

            elif field_type == FieldType.URL:
                return str(value)  # URL validation happens in record service

            elif field_type == FieldType.DATE:
                # Try to parse ISO format datetime
                from datetime import datetime
                return datetime.fromisoformat(value.replace("Z", "+00:00"))

            elif field_type == FieldType.SELECT:
                # For multi-select, value might be JSON array
                if value.startswith("["):
                    return json.loads(value)
                return value

            elif field_type == FieldType.RELATION:
                # Relations can be single ID or array of IDs
                if value.startswith("["):
                    return json.loads(value)
                return value

            elif field_type == FieldType.FILE:
                # File fields should reference file IDs
                if value.startswith("["):
                    return json.loads(value)
                return value

            elif field_type == FieldType.JSON:
                return json.loads(value)

            elif field_type == FieldType.EDITOR:
                return str(value)

            else:
                # Unknown type, return as string
                return str(value)

        except (ValueError, TypeError, json.JSONDecodeError) as e:
            raise ValueError(f"Cannot convert '{value}' to {field_type.value}: {str(e)}")
