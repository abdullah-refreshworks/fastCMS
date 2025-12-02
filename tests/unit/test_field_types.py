"""
Unit tests for field type schemas and validation.
Tests the enhanced relation schema with advanced relation types.
"""

import pytest
from pydantic import ValidationError

from app.utils.field_types import (
    FieldSchema,
    FieldType,
    FieldValidation,
    RelationCascade,
    RelationOptions,
    RelationType,
    SelectOptions,
    FileOptions,
)


class TestRelationTypes:
    """Test relation type enum values."""

    def test_relation_type_values(self):
        """Test all relation type enum values."""
        assert RelationType.ONE_TO_MANY == "one-to-many"
        assert RelationType.MANY_TO_ONE == "many-to-one"
        assert RelationType.MANY_TO_MANY == "many-to-many"
        assert RelationType.ONE_TO_ONE == "one-to-one"
        assert RelationType.POLYMORPHIC == "polymorphic"


class TestRelationCascade:
    """Test cascade action enum values."""

    def test_cascade_values(self):
        """Test all cascade action enum values."""
        assert RelationCascade.CASCADE == "cascade"
        assert RelationCascade.SET_NULL == "set_null"
        assert RelationCascade.RESTRICT == "restrict"
        assert RelationCascade.NO_ACTION == "no_action"


class TestRelationOptions:
    """Test RelationOptions validation and configuration."""

    def test_basic_relation_options(self):
        """Test basic relation options with required fields."""
        options = RelationOptions(collection_id="users")

        assert options.collection_id == "users"
        assert options.type == RelationType.ONE_TO_MANY
        assert options.cascade_delete == RelationCascade.RESTRICT
        assert options.display_fields == ["id"]
        assert options.max_depth == 1

    def test_one_to_many_relation(self):
        """Test one-to-many relation configuration."""
        options = RelationOptions(
            collection_id="posts",
            type=RelationType.ONE_TO_MANY,
            cascade_delete=RelationCascade.CASCADE,
            display_fields=["title", "content"],
        )

        assert options.collection_id == "posts"
        assert options.type == RelationType.ONE_TO_MANY
        assert options.cascade_delete == RelationCascade.CASCADE
        assert options.display_fields == ["title", "content"]

    def test_many_to_one_relation(self):
        """Test many-to-one relation configuration."""
        options = RelationOptions(
            collection_id="users",
            type=RelationType.MANY_TO_ONE,
            cascade_delete=RelationCascade.SET_NULL,
            display_fields=["name", "email"],
        )

        assert options.collection_id == "users"
        assert options.type == RelationType.MANY_TO_ONE
        assert options.cascade_delete == RelationCascade.SET_NULL

    def test_many_to_many_relation(self):
        """Test many-to-many relation with junction table."""
        options = RelationOptions(
            collection_id="tags",
            type=RelationType.MANY_TO_MANY,
            junction_table="posts_tags",
            junction_field="post_id",
            target_field="tag_id",
            display_fields=["name"],
        )

        assert options.collection_id == "tags"
        assert options.type == RelationType.MANY_TO_MANY
        assert options.junction_table == "posts_tags"
        assert options.junction_field == "post_id"
        assert options.target_field == "tag_id"

    def test_one_to_one_relation(self):
        """Test one-to-one relation configuration."""
        options = RelationOptions(
            collection_id="user_profiles",
            type=RelationType.ONE_TO_ONE,
            cascade_delete=RelationCascade.CASCADE,
            display_fields=["bio", "avatar"],
        )

        assert options.collection_id == "user_profiles"
        assert options.type == RelationType.ONE_TO_ONE
        assert options.cascade_delete == RelationCascade.CASCADE

    def test_polymorphic_relation(self):
        """Test polymorphic relation with multiple target collections."""
        options = RelationOptions(
            collection_ids=["posts", "events", "products"],
            type=RelationType.POLYMORPHIC,
            polymorphic_type_field="commentable_type",
            display_fields=["title"],
        )

        assert options.collection_ids == ["posts", "events", "products"]
        assert options.type == RelationType.POLYMORPHIC
        assert options.polymorphic_type_field == "commentable_type"

    def test_nested_loading_depth(self):
        """Test max_depth validation for nested loading."""
        # Valid depths (0-5)
        for depth in range(6):
            options = RelationOptions(
                collection_id="users",
                max_depth=depth,
            )
            assert options.max_depth == depth

        # Invalid depth (> 5)
        with pytest.raises(ValidationError):
            RelationOptions(collection_id="users", max_depth=6)

        # Invalid depth (< 0)
        with pytest.raises(ValidationError):
            RelationOptions(collection_id="users", max_depth=-1)

    def test_cascade_delete_options(self):
        """Test all cascade delete options."""
        for cascade in [
            RelationCascade.CASCADE,
            RelationCascade.SET_NULL,
            RelationCascade.RESTRICT,
            RelationCascade.NO_ACTION,
        ]:
            options = RelationOptions(
                collection_id="users",
                cascade_delete=cascade,
            )
            assert options.cascade_delete == cascade


class TestFieldSchema:
    """Test FieldSchema with relation fields."""

    def test_basic_text_field(self):
        """Test basic text field schema."""
        field = FieldSchema(
            name="title",
            type=FieldType.TEXT,
        )

        assert field.name == "title"
        assert field.type == FieldType.TEXT
        assert not field.hidden
        assert not field.system

    def test_relation_field_one_to_many(self):
        """Test relation field with one-to-many configuration."""
        field = FieldSchema(
            name="comments",
            type=FieldType.RELATION,
            relation=RelationOptions(
                collection_id="comments",
                type=RelationType.ONE_TO_MANY,
                cascade_delete=RelationCascade.CASCADE,
            ),
        )

        assert field.name == "comments"
        assert field.type == FieldType.RELATION
        assert field.relation is not None
        assert field.relation.collection_id == "comments"
        assert field.relation.type == RelationType.ONE_TO_MANY

    def test_relation_field_many_to_many(self):
        """Test relation field with many-to-many configuration."""
        field = FieldSchema(
            name="tags",
            type=FieldType.RELATION,
            relation=RelationOptions(
                collection_id="tags",
                type=RelationType.MANY_TO_MANY,
                junction_table="posts_tags",
                junction_field="post_id",
                target_field="tag_id",
            ),
        )

        assert field.name == "tags"
        assert field.relation.type == RelationType.MANY_TO_MANY
        assert field.relation.junction_table == "posts_tags"

    def test_relation_field_polymorphic(self):
        """Test relation field with polymorphic configuration."""
        field = FieldSchema(
            name="commentable",
            type=FieldType.RELATION,
            relation=RelationOptions(
                collection_ids=["posts", "events"],
                type=RelationType.POLYMORPHIC,
                polymorphic_type_field="commentable_type",
            ),
        )

        assert field.name == "commentable"
        assert field.relation.type == RelationType.POLYMORPHIC
        assert field.relation.collection_ids == ["posts", "events"]

    def test_field_name_validation(self):
        """Test field name validation rules."""
        # Valid names
        valid_names = ["title", "user_name", "createdBy", "field123"]
        for name in valid_names:
            field = FieldSchema(name=name, type=FieldType.TEXT)
            assert field.name == name

        # Invalid names (reserved words)
        reserved = ["id", "created", "updated", "deleted", "select", "from"]
        for name in reserved:
            with pytest.raises(ValidationError) as exc_info:
                FieldSchema(name=name, type=FieldType.TEXT)
            assert "reserved" in str(exc_info.value).lower()

        # Invalid name pattern (starts with number)
        with pytest.raises(ValidationError):
            FieldSchema(name="123field", type=FieldType.TEXT)

        # Invalid name pattern (special characters)
        with pytest.raises(ValidationError):
            FieldSchema(name="field-name", type=FieldType.TEXT)

    def test_select_field_with_options(self):
        """Test select field with options."""
        field = FieldSchema(
            name="status",
            type=FieldType.SELECT,
            select=SelectOptions(
                values=["draft", "published", "archived"],
                max_select=1,
            ),
        )

        assert field.type == FieldType.SELECT
        assert field.select is not None
        assert field.select.values == ["draft", "published", "archived"]

    def test_file_field_with_options(self):
        """Test file field with options."""
        field = FieldSchema(
            name="avatar",
            type=FieldType.FILE,
            file=FileOptions(
                max_size=5242880,
                max_files=1,
                mime_types=["image/jpeg", "image/png"],
            ),
        )

        assert field.type == FieldType.FILE
        assert field.file is not None
        assert field.file.max_size == 5242880


class TestFieldValidation:
    """Test field validation configuration."""

    def test_basic_validation(self):
        """Test basic validation options."""
        validation = FieldValidation(
            required=True,
            unique=True,
            min_length=5,
            max_length=100,
        )

        assert validation.required is True
        assert validation.unique is True
        assert validation.min_length == 5
        assert validation.max_length == 100

    def test_numeric_validation(self):
        """Test numeric validation options."""
        validation = FieldValidation(
            min=0,
            max=100,
        )

        assert validation.min == 0
        assert validation.max == 100

    def test_pattern_validation(self):
        """Test regex pattern validation."""
        validation = FieldValidation(
            pattern=r"^[A-Z][a-z]+$",
        )

        assert validation.pattern == r"^[A-Z][a-z]+$"

    def test_select_values_validation(self):
        """Test allowed values for select fields."""
        validation = FieldValidation(
            values=["option1", "option2", "option3"],
        )

        assert validation.values == ["option1", "option2", "option3"]


class TestCompleteFieldSchemas:
    """Test complete field schema configurations."""

    def test_complete_relation_field(self):
        """Test a complete relation field with all options."""
        field = FieldSchema(
            name="author",
            type=FieldType.RELATION,
            label="Author",
            hint="Select the post author",
            validation=FieldValidation(required=True),
            relation=RelationOptions(
                collection_id="users",
                type=RelationType.MANY_TO_ONE,
                cascade_delete=RelationCascade.SET_NULL,
                display_fields=["name", "email"],
                max_depth=2,
            ),
        )

        assert field.name == "author"
        assert field.type == FieldType.RELATION
        assert field.label == "Author"
        assert field.hint == "Select the post author"
        assert field.validation.required is True
        assert field.relation.collection_id == "users"
        assert field.relation.type == RelationType.MANY_TO_ONE
        assert field.relation.cascade_delete == RelationCascade.SET_NULL
        assert field.relation.max_depth == 2

    def test_complete_many_to_many_field(self):
        """Test a complete many-to-many relation field."""
        field = FieldSchema(
            name="categories",
            type=FieldType.RELATION,
            label="Categories",
            hint="Select one or more categories",
            relation=RelationOptions(
                collection_id="categories",
                type=RelationType.MANY_TO_MANY,
                junction_table="post_categories",
                junction_field="post_id",
                target_field="category_id",
                cascade_delete=RelationCascade.CASCADE,
                display_fields=["name", "slug"],
                max_depth=1,
            ),
        )

        assert field.name == "categories"
        assert field.type == FieldType.RELATION
        assert field.relation.type == RelationType.MANY_TO_MANY
        assert field.relation.junction_table == "post_categories"
        assert field.relation.junction_field == "post_id"
        assert field.relation.target_field == "category_id"

    def test_complete_polymorphic_field(self):
        """Test a complete polymorphic relation field."""
        field = FieldSchema(
            name="attachable",
            type=FieldType.RELATION,
            label="Attach To",
            hint="Select what this attachment belongs to",
            relation=RelationOptions(
                collection_ids=["posts", "events", "products"],
                type=RelationType.POLYMORPHIC,
                polymorphic_type_field="attachable_type",
                cascade_delete=RelationCascade.CASCADE,
                display_fields=["title"],
                max_depth=1,
            ),
        )

        assert field.name == "attachable"
        assert field.type == FieldType.RELATION
        assert field.relation.type == RelationType.POLYMORPHIC
        assert field.relation.collection_ids == ["posts", "events", "products"]
        assert field.relation.polymorphic_type_field == "attachable_type"


class TestSchemaDefaults:
    """Test default values in schemas."""

    def test_field_validation_defaults(self):
        """Test FieldValidation defaults."""
        validation = FieldValidation()

        assert validation.required is False
        assert validation.unique is False
        assert validation.min is None
        assert validation.max is None

    def test_relation_options_defaults(self):
        """Test RelationOptions defaults."""
        options = RelationOptions(collection_id="users")

        assert options.type == RelationType.ONE_TO_MANY
        assert options.cascade_delete == RelationCascade.RESTRICT
        assert options.display_fields == ["id"]
        assert options.max_depth == 1
        assert options.junction_table is None
        assert options.polymorphic_type_field is None

    def test_field_schema_defaults(self):
        """Test FieldSchema defaults."""
        field = FieldSchema(name="test_field", type=FieldType.TEXT)

        assert field.label is None
        assert field.hint is None
        assert field.hidden is False
        assert field.system is False
        assert field.relation is None
        assert field.select is None
        assert field.file is None


class TestSchemaMigration:
    """Test schema migration for backward compatibility."""

    def test_migrate_cascade_delete_from_boolean_false(self):
        """Test migration of old boolean False cascade_delete to new enum."""
        options = RelationOptions(
            collection_id="users",
            cascade_delete=False  # Old format
        )

        assert options.cascade_delete == RelationCascade.RESTRICT

    def test_migrate_cascade_delete_from_boolean_true(self):
        """Test migration of old boolean True cascade_delete to new enum."""
        options = RelationOptions(
            collection_id="users",
            cascade_delete=True  # Old format
        )

        assert options.cascade_delete == RelationCascade.CASCADE

    def test_migrate_cascade_delete_from_none(self):
        """Test migration of None cascade_delete to default."""
        options = RelationOptions(
            collection_id="users",
            cascade_delete=None
        )

        assert options.cascade_delete == RelationCascade.RESTRICT

    def test_cascade_delete_string_passthrough(self):
        """Test that string enum values are passed through."""
        options = RelationOptions(
            collection_id="users",
            cascade_delete="set_null"  # New format
        )

        assert options.cascade_delete == RelationCascade.SET_NULL

    def test_old_schema_in_field_schema(self):
        """Test complete field with old boolean cascade_delete."""
        field = FieldSchema(
            name="author",
            type=FieldType.RELATION,
            relation=RelationOptions(
                collection_id="users",
                cascade_delete=False,  # Old format
            ),
        )

        assert field.relation.cascade_delete == RelationCascade.RESTRICT
