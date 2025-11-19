"""
Base storage interface for file operations.

Supports multiple storage backends:
- Local filesystem (default)
- AWS S3
- Azure Blob Storage
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from io import BytesIO
from typing import BinaryIO, Optional


@dataclass
class StorageFile:
    """Represents a stored file with metadata."""

    key: str  # File identifier/path
    size: int  # File size in bytes
    content_type: str  # MIME type
    url: Optional[str] = None  # Public URL if available
    etag: Optional[str] = None  # Entity tag for versioning


class BaseStorage(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    async def upload(
        self,
        file: BinaryIO,
        key: str,
        content_type: str,
        metadata: Optional[dict] = None,
    ) -> StorageFile:
        """
        Upload a file to storage.

        Args:
            file: File-like object to upload
            key: Unique identifier for the file
            content_type: MIME type of the file
            metadata: Optional metadata dictionary

        Returns:
            StorageFile with upload details

        Raises:
            StorageError: If upload fails
        """
        pass

    @abstractmethod
    async def download(self, key: str) -> bytes:
        """
        Download a file from storage.

        Args:
            key: File identifier

        Returns:
            File contents as bytes

        Raises:
            FileNotFoundError: If file doesn't exist
            StorageError: If download fails
        """
        pass

    @abstractmethod
    async def download_stream(self, key: str) -> BytesIO:
        """
        Download a file as a stream.

        Args:
            key: File identifier

        Returns:
            BytesIO stream

        Raises:
            FileNotFoundError: If file doesn't exist
            StorageError: If download fails
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """
        Delete a file from storage.

        Args:
            key: File identifier

        Raises:
            FileNotFoundError: If file doesn't exist
            StorageError: If deletion fails
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if a file exists in storage.

        Args:
            key: File identifier

        Returns:
            True if file exists, False otherwise
        """
        pass

    @abstractmethod
    async def get_metadata(self, key: str) -> StorageFile:
        """
        Get file metadata without downloading.

        Args:
            key: File identifier

        Returns:
            StorageFile with metadata

        Raises:
            FileNotFoundError: If file doesn't exist
            StorageError: If operation fails
        """
        pass

    @abstractmethod
    def get_public_url(self, key: str, expires_in: Optional[int] = None) -> str:
        """
        Get a public URL for the file.

        Args:
            key: File identifier
            expires_in: Optional expiration time in seconds

        Returns:
            Public URL (may be signed/temporary)
        """
        pass

    @abstractmethod
    async def list_files(self, prefix: str = "", limit: int = 1000) -> list[StorageFile]:
        """
        List files with optional prefix filter.

        Args:
            prefix: Optional prefix to filter files
            limit: Maximum number of files to return

        Returns:
            List of StorageFile objects
        """
        pass

    @abstractmethod
    async def copy(self, source_key: str, dest_key: str) -> StorageFile:
        """
        Copy a file within storage.

        Args:
            source_key: Source file identifier
            dest_key: Destination file identifier

        Returns:
            StorageFile for the copied file

        Raises:
            FileNotFoundError: If source doesn't exist
            StorageError: If copy fails
        """
        pass

    @abstractmethod
    async def get_size(self, key: str) -> int:
        """
        Get file size without downloading.

        Args:
            key: File identifier

        Returns:
            File size in bytes

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        pass


class StorageError(Exception):
    """Base exception for storage operations."""

    pass


class FileNotFoundError(StorageError):
    """Raised when a file is not found in storage."""

    pass


class UploadError(StorageError):
    """Raised when file upload fails."""

    pass


class DownloadError(StorageError):
    """Raised when file download fails."""

    pass
