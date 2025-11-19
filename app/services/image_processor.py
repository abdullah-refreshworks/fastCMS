"""
Image processing service for resizing, thumbnails, and optimization.

Uses Pillow (PIL) for image manipulation.
Supports JPEG, PNG, GIF, WEBP formats.
"""

from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Literal, Optional, Tuple

from PIL import Image, ImageOps

from app.core.config import settings


class ImageProcessor:
    """Image processing utilities."""

    # Supported image formats
    SUPPORTED_FORMATS = {"image/jpeg", "image/png", "image/gif", "image/webp"}

    # Format extensions mapping
    FORMAT_EXTENSIONS = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
    }

    # PIL format names
    PIL_FORMATS = {
        "image/jpeg": "JPEG",
        "image/png": "PNG",
        "image/gif": "GIF",
        "image/webp": "WEBP",
    }

    @classmethod
    def is_image(cls, content_type: str) -> bool:
        """
        Check if content type is a supported image format.

        Args:
            content_type: MIME type

        Returns:
            True if supported image format
        """
        return content_type.lower() in cls.SUPPORTED_FORMATS

    @classmethod
    def get_extension(cls, content_type: str) -> str:
        """Get file extension for content type."""
        return cls.FORMAT_EXTENSIONS.get(content_type.lower(), ".bin")

    @classmethod
    def get_pil_format(cls, content_type: str) -> str:
        """Get PIL format name for content type."""
        return cls.PIL_FORMATS.get(content_type.lower(), "JPEG")

    @staticmethod
    async def resize_image(
        image_data: bytes,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None,
        quality: int = 85,
        output_format: Optional[str] = None,
    ) -> Tuple[bytes, int, int]:
        """
        Resize an image while maintaining aspect ratio.

        Args:
            image_data: Original image bytes
            max_width: Maximum width (None = no limit)
            max_height: Maximum height (None = no limit)
            quality: JPEG quality (1-100)
            output_format: Output format (JPEG, PNG, etc.)

        Returns:
            Tuple of (resized_image_bytes, width, height)

        Raises:
            ValueError: If image cannot be processed
        """
        try:
            # Open image
            with Image.open(BytesIO(image_data)) as img:
                # Convert RGBA to RGB for JPEG
                if output_format == "JPEG" and img.mode in ("RGBA", "LA", "P"):
                    # Create white background
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    bg.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                    img = bg

                original_width, original_height = img.size

                # Calculate new size
                if max_width or max_height:
                    # Use thumbnail which maintains aspect ratio
                    size = (
                        max_width or original_width,
                        max_height or original_height,
                    )
                    img.thumbnail(size, Image.Resampling.LANCZOS)

                # Get new dimensions
                new_width, new_height = img.size

                # Save to bytes
                output = BytesIO()
                save_format = output_format or img.format or "JPEG"

                if save_format == "JPEG":
                    img.save(
                        output,
                        format=save_format,
                        quality=quality,
                        optimize=True,
                    )
                elif save_format == "PNG":
                    img.save(
                        output,
                        format=save_format,
                        optimize=True,
                    )
                elif save_format == "WEBP":
                    img.save(
                        output,
                        format=save_format,
                        quality=quality,
                        method=6,  # Best compression
                    )
                else:
                    img.save(output, format=save_format)

                return output.getvalue(), new_width, new_height

        except Exception as e:
            raise ValueError(f"Failed to resize image: {str(e)}") from e

    @staticmethod
    async def create_thumbnail(
        image_data: bytes,
        width: int,
        height: Optional[int] = None,
        quality: int = 85,
        output_format: Optional[str] = None,
    ) -> Tuple[bytes, int, int]:
        """
        Create a thumbnail from an image.

        Args:
            image_data: Original image bytes
            width: Thumbnail width
            height: Thumbnail height (None = auto from aspect ratio)
            quality: JPEG quality (1-100)
            output_format: Output format (JPEG, PNG, etc.)

        Returns:
            Tuple of (thumbnail_bytes, width, height)

        Raises:
            ValueError: If image cannot be processed
        """
        try:
            with Image.open(BytesIO(image_data)) as img:
                # Convert RGBA to RGB for JPEG
                if output_format == "JPEG" and img.mode in ("RGBA", "LA", "P"):
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    bg.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                    img = bg

                # Calculate height if not provided
                if height is None:
                    aspect_ratio = img.height / img.width
                    height = int(width * aspect_ratio)

                # Use ImageOps.fit for center-crop thumbnail
                img_thumb = ImageOps.fit(
                    img,
                    (width, height),
                    method=Image.Resampling.LANCZOS,
                )

                # Save to bytes
                output = BytesIO()
                save_format = output_format or img.format or "JPEG"

                if save_format == "JPEG":
                    img_thumb.save(
                        output,
                        format=save_format,
                        quality=quality,
                        optimize=True,
                    )
                elif save_format == "PNG":
                    img_thumb.save(
                        output,
                        format=save_format,
                        optimize=True,
                    )
                elif save_format == "WEBP":
                    img_thumb.save(
                        output,
                        format=save_format,
                        quality=quality,
                        method=6,
                    )
                else:
                    img_thumb.save(output, format=save_format)

                return output.getvalue(), img_thumb.width, img_thumb.height

        except Exception as e:
            raise ValueError(f"Failed to create thumbnail: {str(e)}") from e

    @staticmethod
    async def create_thumbnails(
        image_data: bytes,
        sizes: list[int],
        quality: int = 85,
        output_format: Optional[str] = None,
    ) -> dict[int, Tuple[bytes, int, int]]:
        """
        Create multiple thumbnail sizes from an image.

        Args:
            image_data: Original image bytes
            sizes: List of thumbnail widths
            quality: JPEG quality (1-100)
            output_format: Output format (JPEG, PNG, etc.)

        Returns:
            Dictionary mapping size to (thumbnail_bytes, width, height)

        Raises:
            ValueError: If image cannot be processed
        """
        thumbnails = {}

        for size in sizes:
            try:
                thumb_data, width, height = await ImageProcessor.create_thumbnail(
                    image_data, size, quality=quality, output_format=output_format
                )
                thumbnails[size] = (thumb_data, width, height)
            except Exception as e:
                # Skip this size if it fails
                print(f"Warning: Failed to create {size}px thumbnail: {str(e)}")
                continue

        return thumbnails

    @staticmethod
    async def get_image_info(image_data: bytes) -> dict:
        """
        Get image metadata without processing.

        Args:
            image_data: Image bytes

        Returns:
            Dictionary with image info (format, mode, size, etc.)

        Raises:
            ValueError: If not a valid image
        """
        try:
            with Image.open(BytesIO(image_data)) as img:
                return {
                    "format": img.format,
                    "mode": img.mode,
                    "width": img.width,
                    "height": img.height,
                    "size": len(image_data),
                    "is_animated": getattr(img, "is_animated", False),
                    "n_frames": getattr(img, "n_frames", 1),
                }
        except Exception as e:
            raise ValueError(f"Invalid image data: {str(e)}") from e

    @staticmethod
    async def optimize_image(
        image_data: bytes,
        max_size: Optional[int] = None,
        quality: int = 85,
        output_format: Optional[str] = None,
    ) -> bytes:
        """
        Optimize image file size without significant quality loss.

        Args:
            image_data: Original image bytes
            max_size: Maximum file size in bytes (None = no limit)
            quality: Starting JPEG quality (1-100)
            output_format: Output format (JPEG, PNG, etc.)

        Returns:
            Optimized image bytes

        Raises:
            ValueError: If image cannot be processed
        """
        try:
            with Image.open(BytesIO(image_data)) as img:
                # Convert RGBA to RGB for JPEG
                if output_format == "JPEG" and img.mode in ("RGBA", "LA", "P"):
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    bg.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                    img = bg

                save_format = output_format or img.format or "JPEG"

                # If no max_size, just optimize once
                if max_size is None:
                    output = BytesIO()
                    if save_format == "JPEG":
                        img.save(output, format=save_format, quality=quality, optimize=True)
                    elif save_format == "PNG":
                        img.save(output, format=save_format, optimize=True)
                    elif save_format == "WEBP":
                        img.save(output, format=save_format, quality=quality, method=6)
                    else:
                        img.save(output, format=save_format)
                    return output.getvalue()

                # Try to meet max_size by reducing quality
                current_quality = quality
                while current_quality >= 20:  # Don't go below 20% quality
                    output = BytesIO()

                    if save_format == "JPEG":
                        img.save(
                            output,
                            format=save_format,
                            quality=current_quality,
                            optimize=True,
                        )
                    elif save_format == "WEBP":
                        img.save(
                            output,
                            format=save_format,
                            quality=current_quality,
                            method=6,
                        )
                    else:
                        img.save(output, format=save_format, optimize=True)

                    result = output.getvalue()

                    if len(result) <= max_size:
                        return result

                    current_quality -= 5

                # If still too large, return best effort
                return result

        except Exception as e:
            raise ValueError(f"Failed to optimize image: {str(e)}") from e

    @staticmethod
    async def convert_format(
        image_data: bytes,
        target_format: Literal["JPEG", "PNG", "WEBP", "GIF"],
        quality: int = 85,
    ) -> bytes:
        """
        Convert image to a different format.

        Args:
            image_data: Original image bytes
            target_format: Target format (JPEG, PNG, WEBP, GIF)
            quality: Quality for lossy formats (1-100)

        Returns:
            Converted image bytes

        Raises:
            ValueError: If image cannot be processed
        """
        try:
            with Image.open(BytesIO(image_data)) as img:
                # Handle transparency for JPEG
                if target_format == "JPEG" and img.mode in ("RGBA", "LA", "P"):
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    bg.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                    img = bg

                output = BytesIO()

                if target_format == "JPEG":
                    img.save(output, format=target_format, quality=quality, optimize=True)
                elif target_format == "PNG":
                    img.save(output, format=target_format, optimize=True)
                elif target_format == "WEBP":
                    img.save(output, format=target_format, quality=quality, method=6)
                elif target_format == "GIF":
                    img.save(output, format=target_format, optimize=True)
                else:
                    img.save(output, format=target_format)

                return output.getvalue()

        except Exception as e:
            raise ValueError(f"Failed to convert image format: {str(e)}") from e
