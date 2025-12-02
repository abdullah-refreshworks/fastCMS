"""
Unit tests for CSV Service.
Tests CSV export, import, and type conversion logic without database.
"""

import pytest
from datetime import datetime

from app.services.csv_service import CSVService
from app.utils.field_types import FieldSchema, FieldType
from app.core.exceptions import ValidationException


class TestCSVExport:
    """Test CSV export functionality."""

    def test_export_empty_records(self):
        """Test exporting empty record list."""
        fields = [
            FieldSchema(name="title", type=FieldType.TEXT, validation={}),
            FieldSchema(name="price", type=FieldType.NUMBER, validation={}),
        ]

        csv_content = CSVService.export_to_csv([], fields)

        # Should have headers only
        assert "title,price" in csv_content
        lines = csv_content.strip().split("\n")
        assert len(lines) == 1  # Only header

    def test_export_with_records(self):
        """Test exporting records with data."""
        fields = [
            FieldSchema(name="name", type=FieldType.TEXT, validation={}),
            FieldSchema(name="price", type=FieldType.NUMBER, validation={}),
        ]

        records = [
            {"id": "1", "created": datetime(2025, 1, 1), "updated": datetime(2025, 1, 1), "name": "Product 1", "price": 10.99},
            {"id": "2", "created": datetime(2025, 1, 2), "updated": datetime(2025, 1, 2), "name": "Product 2", "price": 20.50},
        ]

        csv_content = CSVService.export_to_csv(records, fields)

        # Check headers
        assert "id,created,updated,name,price" in csv_content

        # Check data
        assert "Product 1" in csv_content
        assert "Product 2" in csv_content
        assert "10.99" in csv_content
        assert "20.5" in csv_content

    def test_export_with_null_values(self):
        """Test exporting records with null values."""
        fields = [
            FieldSchema(name="name", type=FieldType.TEXT, validation={}),
            FieldSchema(name="optional_field", type=FieldType.TEXT, validation={}),
        ]

        records = [
            {"id": "1", "created": datetime(2025, 1, 1), "updated": datetime(2025, 1, 1), "name": "Test", "optional_field": None},
        ]

        csv_content = CSVService.export_to_csv(records, fields)

        # Null should be empty string in CSV
        lines = csv_content.strip().split("\n")
        data_line = lines[1]
        assert data_line.endswith(",Test,")  # Empty value at end


class TestCSVImport:
    """Test CSV import functionality."""

    def test_parse_basic_csv(self):
        """Test parsing basic CSV."""
        fields = [
            FieldSchema(name="name", type=FieldType.TEXT, validation={}),
            FieldSchema(name="quantity", type=FieldType.NUMBER, validation={}),
        ]

        csv_content = """name,quantity
Item 1,100
Item 2,200"""

        records = CSVService.parse_csv(csv_content, fields)

        assert len(records) == 2
        assert records[0]["name"] == "Item 1"
        assert records[0]["quantity"] == 100
        assert records[1]["name"] == "Item 2"
        assert records[1]["quantity"] == 200

    def test_parse_csv_with_types(self):
        """Test parsing CSV with different field types."""
        fields = [
            FieldSchema(name="name", type=FieldType.TEXT, validation={}),
            FieldSchema(name="price", type=FieldType.NUMBER, validation={}),
            FieldSchema(name="active", type=FieldType.BOOL, validation={}),
        ]

        csv_content = """name,price,active
Product 1,10.99,true
Product 2,20.50,false"""

        records = CSVService.parse_csv(csv_content, fields)

        assert len(records) == 2
        assert records[0]["price"] == 10.99
        assert records[0]["active"] is True
        assert records[1]["active"] is False

    def test_parse_csv_skips_system_fields(self):
        """Test that system fields are ignored during import."""
        fields = [
            FieldSchema(name="name", type=FieldType.TEXT, validation={}),
        ]

        csv_content = """id,created,updated,name
some-uuid,2025-01-01,2025-01-01,Test"""

        records = CSVService.parse_csv(csv_content, fields)

        assert len(records) == 1
        assert "id" not in records[0]
        assert "created" not in records[0]
        assert "updated" not in records[0]
        assert records[0]["name"] == "Test"

    def test_parse_csv_with_skip_validation(self):
        """Test parsing with validation skipped."""
        fields = [
            FieldSchema(name="number_field", type=FieldType.NUMBER, validation={}),
        ]

        csv_content = """number_field
invalid_number"""

        # With skip_validation=True, should return string
        records = CSVService.parse_csv(csv_content, fields, skip_validation=True)

        assert len(records) == 1
        assert records[0]["number_field"] == "invalid_number"

    def test_parse_empty_csv_fails(self):
        """Test that empty CSV raises validation error."""
        fields = [
            FieldSchema(name="name", type=FieldType.TEXT, validation={}),
        ]

        with pytest.raises(ValidationException) as exc_info:
            CSVService.parse_csv("", fields)

        assert "empty" in str(exc_info.value).lower()


class TestCSVTypeConversion:
    """Test CSV type conversion logic."""

    def test_convert_boolean_values(self):
        """Test boolean value conversion."""
        field = FieldSchema(name="active", type=FieldType.BOOL, validation={})

        # True values
        assert CSVService._convert_csv_value("true", field, False) is True
        assert CSVService._convert_csv_value("1", field, False) is True
        assert CSVService._convert_csv_value("yes", field, False) is True
        assert CSVService._convert_csv_value("y", field, False) is True

        # False values
        assert CSVService._convert_csv_value("false", field, False) is False
        assert CSVService._convert_csv_value("0", field, False) is False
        assert CSVService._convert_csv_value("no", field, False) is False
        assert CSVService._convert_csv_value("n", field, False) is False

    def test_convert_number_values(self):
        """Test number value conversion."""
        field = FieldSchema(name="price", type=FieldType.NUMBER, validation={})

        # Integer
        assert CSVService._convert_csv_value("100", field, False) == 100

        # Float
        assert CSVService._convert_csv_value("10.99", field, False) == 10.99

    def test_convert_invalid_number_raises_error(self):
        """Test that invalid number raises ValueError."""
        field = FieldSchema(name="price", type=FieldType.NUMBER, validation={})

        with pytest.raises(ValueError):
            CSVService._convert_csv_value("not_a_number", field, False)

    def test_convert_invalid_boolean_raises_error(self):
        """Test that invalid boolean raises ValueError."""
        field = FieldSchema(name="active", type=FieldType.BOOL, validation={})

        with pytest.raises(ValueError):
            CSVService._convert_csv_value("maybe", field, False)

    def test_skip_validation_returns_string(self):
        """Test that skip_validation returns value as-is."""
        field = FieldSchema(name="number", type=FieldType.NUMBER, validation={})

        result = CSVService._convert_csv_value("invalid", field, True)

        assert result == "invalid"
        assert isinstance(result, str)
