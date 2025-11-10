"""Read-only mode for maintenance/backups"""
from typing import Optional
import asyncio

_readonly_mode: bool = False
_readonly_reason: Optional[str] = None


def is_readonly() -> bool:
    """Check if system is in read-only mode"""
    return _readonly_mode


def get_readonly_reason() -> Optional[str]:
    """Get reason for read-only mode"""
    return _readonly_reason


def enable_readonly(reason: str = "Maintenance") -> None:
    """Enable read-only mode"""
    global _readonly_mode, _readonly_reason
    _readonly_mode = True
    _readonly_reason = reason


def disable_readonly() -> None:
    """Disable read-only mode"""
    global _readonly_mode, _readonly_reason
    _readonly_mode = False
    _readonly_reason = None


class ReadOnlyContext:
    """Context manager for temporary read-only mode"""

    def __init__(self, reason: str = "Backup"):
        self.reason = reason
        self.was_readonly = False

    def __enter__(self):
        self.was_readonly = is_readonly()
        if not self.was_readonly:
            enable_readonly(self.reason)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.was_readonly:
            disable_readonly()

    async def __aenter__(self):
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return self.__exit__(exc_type, exc_val, exc_tb)
