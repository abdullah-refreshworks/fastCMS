"""
Local filesystem storage implementation.

This is the default storage backend that stores files on the local filesystem.
No additional dependencies required - works out of the box.
"""

import os
import shutil
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Optional

import aiofiles
import aiofiles.os

from .base import BaseStorage, DownloadError, StorageError, StorageFile, UploadError


class LocalStorage(BaseStorage):
    """Local filesystem storage implementation."""

    def __init__(self, base_path: str, base_url: str = ""):
        """
        Initialize local storage.

        Args:
            base_path: Root directory for file storage
            base_url: Base URL for generating file URLs
        """
        self.base_path = Path(base_path)
        self.base_url = base_url.rstrip("/")

        # Create base directory if it doesn't exist
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, key: str) -> Path:
        """Get full filesystem path for a key."""
        # Sanitize key to prevent directory traversal
        key = key.replace("..", "").lstrip("/")
        return self.base_path / key

    async def upload(
        self,
        file: BinaryIO,
        key: str,
        content_type: str,
        metadata: Optional[dict] = None,
    ) -> StorageFile:
        """Upload file to local storage."""
        try:
            full_path = self._get_full_path(key)

            # Create parent directories
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Read file content
            file.seek(0)
            content = file.read()
            size = len(content)

            # Write file asynchronously
            async with aiofiles.open(full_path, "wb") as f:
                await f.write(content)

            # Store metadata as extended attributes or separate file if needed
            if metadata:
                metadata_path = full_path.with_suffix(full_path.suffix + ".meta")
                async with aiofiles.open(metadata_path, "w") as f:
                    import json

                    await f.write(json.dumps(metadata))

            return StorageFile(
                key=key,
                size=size,
                content_type=content_type,
                url=self.get_public_url(key),
            )

        except Exception as e:
            raise UploadError(f"Failed to upload file: {str(e)}") from e

    async def download(self, key: str) -> bytes:
        """Download file from local storage."""
        try:
            full_path = self._get_full_path(key)

            if not await aiofiles.os.path.exists(full_path):
                raise FileNotFoundError(f"File not found: {key}")

            async with aiofiles.open(full_path, "rb") as f:
                return await f.read()

        except FileNotFoundError:
            raise
        except Exception as e:
            raise DownloadError(f"Failed to download file: {str(e)}") from e

    async def download_stream(self, key: str) -> BytesIO:
        """Download file as a stream."""
        content = await self.download(key)
        return BytesIO(content)

    async def delete(self, key: str) -> None:
        """Delete file from local storage."""
        try:
            full_path = self._get_full_path(key)

            if not await aiofiles.os.path.exists(full_path):
                raise FileNotFoundError(f"File not found: {key}")

            await aiofiles.os.remove(full_path)

            # Remove metadata file if exists
            metadata_path = full_path.with_suffix(full_path.suffix + ".meta")
            if await aiofiles.os.path.exists(metadata_path):
                await aiofiles.os.remove(metadata_path)

        except FileNotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to delete file: {str(e)}") from e

    async def exists(self, key: str) -> bool:
        """Check if file exists."""
        full_path = self._get_full_path(key)
        return await aiofiles.os.path.exists(full_path)

    async def get_metadata(self, key: str) -> StorageFile:
        """Get file metadata."""
        try:
            full_path = self._get_full_path(key)

            if not await aiofiles.os.path.exists(full_path):
                raise FileNotFoundError(f"File not found: {key}")

            stat = await aiofiles.os.stat(full_path)

            # Try to determine content type
            import mimetypes

            content_type, _ = mimetypes.guess_type(str(full_path))
            content_type = content_type or "application/octet-stream"

            return StorageFile(
                key=key,
                size=stat.st_size,
                content_type=content_type,
                url=self.get_public_url(key),
            )

        except FileNotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to get metadata: {str(e)}") from e

    def get_public_url(self, key: str, expires_in: Optional[int] = None) -> str:
        """Get public URL for file."""
        # For local storage, generate a simple URL
        # In production, this should go through the API endpoint
        if self.base_url:
            return f"{self.base_url}/api/v1/files/{key}"
        return f"/api/v1/files/{key}"

    async def list_files(self, prefix: str = "", limit: int = 1000) -> list[StorageFile]:
        """List files with optional prefix."""
        try:
            search_path = self._get_full_path(prefix) if prefix else self.base_path
            files = []

            if not await aiofiles.os.path.exists(search_path):
                return []

            # Walk directory tree
            for root, _, filenames in os.walk(search_path):
                for filename in filenames:
                    # Skip metadata files
                    if filename.endswith(".meta"):
                        continue

                    full_path = Path(root) / filename
                    relative_path = full_path.relative_to(self.base_path)
                    key = str(relative_path)

                    try:
                        stat = await aiofiles.os.stat(full_path)
                        import mimetypes

                        content_type, _ = mimetypes.guess_type(str(full_path))
                        content_type = content_type or "application/octet-stream"

                        files.append(
                            StorageFile(
                                key=key,
                                size=stat.st_size,
                                content_type=content_type,
                                url=self.get_public_url(key),
                            )
                        )

                        if len(files) >= limit:
                            return files

                    except Exception:
                        # Skip files with errors
                        continue

            return files

        except Exception as e:
            raise StorageError(f"Failed to list files: {str(e)}") from e

    async def copy(self, source_key: str, dest_key: str) -> StorageFile:
        """Copy file within storage."""
        try:
            source_path = self._get_full_path(source_key)
            dest_path = self._get_full_path(dest_key)

            if not await aiofiles.os.path.exists(source_path):
                raise FileNotFoundError(f"Source file not found: {source_key}")

            # Create destination parent directories
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(source_path, dest_path)

            # Copy metadata if exists
            source_meta = source_path.with_suffix(source_path.suffix + ".meta")
            if await aiofiles.os.path.exists(source_meta):
                dest_meta = dest_path.with_suffix(dest_path.suffix + ".meta")
                shutil.copy2(source_meta, dest_meta)

            return await self.get_metadata(dest_key)

        except FileNotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to copy file: {str(e)}") from e

    async def get_size(self, key: str) -> int:
        """Get file size."""
        try:
            full_path = self._get_full_path(key)

            if not await aiofiles.os.path.exists(full_path):
                raise FileNotFoundError(f"File not found: {key}")

            stat = await aiofiles.os.stat(full_path)
            return stat.st_size

        except FileNotFoundError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to get file size: {str(e)}") from e
