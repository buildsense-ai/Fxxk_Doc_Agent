"""
Helper utility functions for the Image RAG system.
"""

import os
import uuid
import hashlib
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def validate_image_file(filename: str, file_data: bytes, max_size: int = 10 * 1024 * 1024) -> bool:
    """
    Validate uploaded image file.
    
    Args:
        filename: Original filename
        file_data: File bytes
        max_size: Maximum file size in bytes
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Check file size
        if len(file_data) > max_size:
            logger.warning(f"File too large: {len(file_data)} bytes")
            return False
        
        # Check file extension
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
        file_ext = os.path.splitext(filename.lower())[1]
        if file_ext not in allowed_extensions:
            logger.warning(f"Invalid file extension: {file_ext}")
            return False
        
        # Try to open as image
        try:
            from PIL import Image
            import io
            image = Image.open(io.BytesIO(file_data))
            image.verify()
            return True
        except Exception as e:
            logger.warning(f"Invalid image file: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error validating image file: {e}")
        return False


def generate_image_id() -> str:
    """Generate unique image ID."""
    return str(uuid.uuid4())


def get_file_extension(filename: str) -> str:
    """Get file extension from filename."""
    return os.path.splitext(filename.lower())[1]


def calculate_file_hash(file_data: bytes) -> str:
    """Calculate SHA-256 hash of file data."""
    return hashlib.sha256(file_data).hexdigest()


def resize_image_if_needed(file_data: bytes, max_width: int = 1920, max_height: int = 1080) -> bytes:
    """
    Resize image if it's too large.
    
    Args:
        file_data: Image bytes
        max_width: Maximum width
        max_height: Maximum height
        
    Returns:
        Resized image bytes
    """
    try:
        from PIL import Image
        import io
        
        image = Image.open(io.BytesIO(file_data))
        
        # Check if resize is needed
        if image.width <= max_width and image.height <= max_height:
            return file_data
        
        # Calculate new dimensions
        ratio = min(max_width / image.width, max_height / image.height)
        new_width = int(image.width * ratio)
        new_height = int(image.height * ratio)
        
        # Resize image
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Save to bytes
        output = io.BytesIO()
        resized_image.save(output, format=image.format or 'JPEG', quality=85)
        
        logger.info(f"Image resized from {image.width}x{image.height} to {new_width}x{new_height}")
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Error resizing image: {e}")
        return file_data  # Return original if resize fails 