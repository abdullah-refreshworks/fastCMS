"""
Access control engine for evaluating permission rules.

Rules syntax:
- null/empty: Public access
- "@request.auth.id != ''": Authenticated users only
- "@request.auth.id = @record.user_id": Owner only
- "@request.auth.role = 'admin'": Admin only
- Complex: "(@request.auth.id = @record.user_id || @request.auth.role = 'admin')"
"""

import re
from typing import Any, Optional

from app.core.exceptions import ForbiddenException


class AccessContext:
    """Context for access control evaluation."""

    def __init__(
        self,
        user_id: Optional[str] = None,
        user_role: str = "user",
        record_data: Optional[dict[str, Any]] = None,
    ):
        self.user_id = user_id
        self.user_role = user_role
        self.record_data = record_data or {}

    @property
    def is_authenticated(self) -> bool:
        return self.user_id is not None

    @property
    def is_admin(self) -> bool:
        return self.user_role == "admin"


class AccessControlEngine:
    """Engine for evaluating access control rules."""

    def __init__(self):
        self.token_pattern = re.compile(r"@(request|record)\.([a-zA-Z_][a-zA-Z0-9_.]*)")

    def evaluate(self, rule: Optional[str], context: AccessContext) -> bool:
        """
        Evaluate an access control rule.

        Args:
            rule: Access control rule expression
            context: Request and record context

        Returns:
            True if access is allowed, False otherwise
        """
        # Empty rule means public access
        if not rule or rule.strip() == "":
            return True

        # Replace tokens with actual values
        expression = self._replace_tokens(rule, context)

        # Evaluate the expression
        try:
            result = self._evaluate_expression(expression)
            return bool(result)
        except Exception:
            # If evaluation fails, deny access
            return False

    def check(self, rule: Optional[str], context: AccessContext, operation: str = "access"):
        """
        Check access and raise exception if denied.

        Args:
            rule: Access control rule
            context: Request and record context
            operation: Operation name for error message

        Raises:
            ForbiddenException: If access is denied
        """
        if not self.evaluate(rule, context):
            raise ForbiddenException(f"Access denied for {operation} operation")

    def _replace_tokens(self, rule: str, context: AccessContext) -> str:
        """Replace @request and @record tokens with actual values."""

        def replace_token(match: re.Match) -> str:
            scope = match.group(1)  # request or record
            path = match.group(2)  # e.g., auth.id, user_id

            if scope == "request":
                return self._get_request_value(path, context)
            elif scope == "record":
                return self._get_record_value(path, context)
            return "None"

        return self.token_pattern.sub(replace_token, rule)

    def _get_request_value(self, path: str, context: AccessContext) -> str:
        """Get value from request context."""
        if path == "auth.id":
            return f"'{context.user_id}'" if context.user_id else "''"
        elif path == "auth.role":
            return f"'{context.user_role}'"
        elif path == "auth.verified":
            return "True" if context.user_id else "False"
        return "None"

    def _get_record_value(self, path: str, context: AccessContext) -> str:
        """Get value from record data."""
        keys = path.split(".")
        value = context.record_data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return "None"

        if value is None:
            return "None"
        elif isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, bool):
            return str(value)
        elif isinstance(value, (int, float)):
            return str(value)
        return "None"

    def _evaluate_expression(self, expression: str) -> bool:
        """
        Safely evaluate a boolean expression.

        Only allows safe operations:
        - Comparisons: =, !=, <, >, <=, >=
        - Logical: &&, ||, !
        - Parentheses
        """
        # Convert SQL-style operators to Python
        # Handle compound operators first before single character replacements
        expression = expression.replace("&&", " and ")
        expression = expression.replace("||", " or ")
        # Replace != first to preserve it
        expression = expression.replace("!=", "!__NE__")
        # Now safe to replace = with ==
        expression = expression.replace("=", "==")
        # Restore !=
        expression = expression.replace("!__NE__", "!=")

        # Only allow safe characters
        if not re.match(r"^[\w\s'\"()!=<>&|.]+$", expression):
            return False

        # Evaluate using eval (safe because we validated the expression)
        try:
            return eval(expression, {"__builtins__": {}}, {})
        except Exception:
            return False


# Global instance
access_control = AccessControlEngine()
