"""
Object storage service using MinIO for storing uploaded images.
"""

import os
import uuid
from typing import Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class StorageService:
    """Service for object storage operations using MinIO."""
    
    def __init__(self, 
                 endpoint: str = "localhost:9000",
                 access_key: str = "minioadmin",
                 secret_key: str = "minioadmin",
                 bucket_name: str = "image-storage",
                 secure: bool = False):
        """Initialize storage service."""
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.secure = secure
        self.client = None
        
    def _connect(self):
        """Connect to MinIO server."""
        if self.client is None:
            try:
                from minio import Minio
                self.client = Minio(
                    self.endpoint,
                    access_key=self.access_key,
                    secret_key=self.secret_key,
                    secure=self.secure
                )
                # Ensure bucket exists
                if not self.client.bucket_exists(self.bucket_name):
                    self.client.make_bucket(self.bucket_name)
                    logger.info(f"Created bucket: {self.bucket_name}")
                
                logger.info(f"Connected to MinIO at {self.endpoint}")
            except ImportError:
                logger.error("minio library not installed")
                raise
            except Exception as e:
                logger.error(f"Error connecting to MinIO: {e}")
                raise
    
    def upload_file(self, file_data: bytes, filename: str, content_type: str = "image/jpeg") -> Tuple[str, str]:
        """
        Upload file to MinIO.
        
        Args:
            file_data: File bytes
            filename: Original filename
            content_type: MIME type
            
        Returns:
            Tuple of (object_name, file_url)
        """
        self._connect()
        
        try:
            # Generate unique object name
            file_extension = os.path.splitext(filename)[1]
            object_name = f"{datetime.now().strftime('%Y/%m/%d')}/{uuid.uuid4()}{file_extension}"
            
            # Upload file
            from io import BytesIO
            self.client.put_object(
                self.bucket_name,
                object_name,
                BytesIO(file_data),
                length=len(file_data),
                content_type=content_type
            )
            
            # Generate file URL
            file_url = f"http://{self.endpoint}/{self.bucket_name}/{object_name}"
            
            logger.info(f"Uploaded file: {object_name}")
            return object_name, file_url
            
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            raise
    
    def delete_file(self, object_name: str) -> bool:
        """Delete file from MinIO."""
        self._connect()
        
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"Deleted file: {object_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    def get_file_url(self, object_name: str) -> str:
        """Get file URL."""
        return f"http://{self.endpoint}/{self.bucket_name}/{object_name}" 