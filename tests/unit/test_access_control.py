"""
Unit tests for access control engine.
"""

import pytest

from app.core.access_control import AccessContext, AccessControlEngine


class TestAccessControlEngine:
    """Test access control engine."""

    def setup_method(self):
        """Setup test instance."""
        self.engine = AccessControlEngine()

    def test_empty_rule_allows_all(self):
        """Empty rule should allow all access."""
        context = AccessContext()
        assert self.engine.evaluate("", context) is True
        assert self.engine.evaluate(None, context) is True

    def test_authenticated_user_rule(self):
        """Test authenticated user rule."""
        # Not authenticated
        context = AccessContext()
        result = self.engine.evaluate("@request.auth.id != ''", context)
        assert result is False

        # Authenticated
        context = AccessContext(user_id="user123")
        result = self.engine.evaluate("@request.auth.id != ''", context)
        assert result is True

    def test_admin_role_rule(self):
        """Test admin role rule."""
        # Regular user
        context = AccessContext(user_id="user123", user_role="user")
        result = self.engine.evaluate("@request.auth.role = 'admin'", context)
        assert result is False

        # Admin user
        context = AccessContext(user_id="admin123", user_role="admin")
        result = self.engine.evaluate("@request.auth.role = 'admin'", context)
        assert result is True

    def test_owner_only_rule(self):
        """Test owner-only rule."""
        # Not owner
        context = AccessContext(
            user_id="user123",
            record_data={"user_id": "user456"}
        )
        result = self.engine.evaluate("@request.auth.id = @record.user_id", context)
        assert result is False

        # Owner
        context = AccessContext(
            user_id="user123",
            record_data={"user_id": "user123"}
        )
        result = self.engine.evaluate("@request.auth.id = @record.user_id", context)
        assert result is True

    def test_owner_or_admin_rule(self):
        """Test owner or admin rule."""
        rule = "@request.auth.id = @record.user_id || @request.auth.role = 'admin'"

        # Not owner, not admin
        context = AccessContext(
            user_id="user123",
            user_role="user",
            record_data={"user_id": "user456"}
        )
        result = self.engine.evaluate(rule, context)
        assert result is False

        # Owner
        context = AccessContext(
            user_id="user123",
            user_role="user",
            record_data={"user_id": "user123"}
        )
        result = self.engine.evaluate(rule, context)
        assert result is True

        # Admin (not owner)
        context = AccessContext(
            user_id="admin123",
            user_role="admin",
            record_data={"user_id": "user456"}
        )
        result = self.engine.evaluate(rule, context)
        assert result is True

    def test_complex_rule_with_and(self):
        """Test complex rule with AND operator."""
        rule = "@request.auth.id != '' && @request.auth.role = 'admin'"

        # Not authenticated
        context = AccessContext()
        result = self.engine.evaluate(rule, context)
        assert result is False

        # Authenticated but not admin
        context = AccessContext(user_id="user123", user_role="user")
        result = self.engine.evaluate(rule, context)
        assert result is False

        # Authenticated and admin
        context = AccessContext(user_id="admin123", user_role="admin")
        result = self.engine.evaluate(rule, context)
        assert result is True

    def test_check_method_raises_on_deny(self):
        """Test check method raises exception when access denied."""
        from app.core.exceptions import ForbiddenException

        context = AccessContext()

        # Should raise
        with pytest.raises(ForbiddenException):
            self.engine.check("@request.auth.id != ''", context)

        # Should not raise
        context = AccessContext(user_id="user123")
        self.engine.check("@request.auth.id != ''", context)

    def test_record_field_access(self):
        """Test accessing record fields."""
        context = AccessContext(
            record_data={
                "published": True,
                "status": "active",
                "count": 42
            }
        )

        # Boolean field
        result = self.engine.evaluate("@record.published = True", context)
        assert result is True

        # String field
        result = self.engine.evaluate("@record.status = 'active'", context)
        assert result is True

        # Number field
        result = self.engine.evaluate("@record.count = 42", context)
        assert result is True

    def test_invalid_expression_denies(self):
        """Invalid expressions should deny access."""
        context = AccessContext(user_id="user123")

        # Invalid syntax should deny
        result = self.engine.evaluate("invalid..syntax", context)
        assert result is False

    def test_access_context_properties(self):
        """Test AccessContext helper properties."""
        # Not authenticated
        context = AccessContext()
        assert context.is_authenticated is False
        assert context.is_admin is False

        # Authenticated user
        context = AccessContext(user_id="user123", user_role="user")
        assert context.is_authenticated is True
        assert context.is_admin is False

        # Admin user
        context = AccessContext(user_id="admin123", user_role="admin")
        assert context.is_authenticated is True
        assert context.is_admin is True
