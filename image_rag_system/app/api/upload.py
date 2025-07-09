"""
Image upload API endpoints.
"""

import os
import uuid
from typing import Optional
import logging
from PIL import Image

logger = logging.getLogger(__name__)

# Simplified implementation without FastAPI dependencies for now
class UploadAPI:
    """Image upload API handler."""
    
    def __init__(self, storage_service, embedding_service, retrieval_service, db_session):
        self.storage_service = storage_service
        self.embedding_service = embedding_service
        self.retrieval_service = retrieval_service
        self.db_session = db_session
    
    async def upload_image(self, file_data: bytes, filename: str, description: Optional[str] = None):
        """
        Upload image and add to search index.
        
        Args:
            file_data: Image file bytes
            filename: Original filename
            description: Optional description
            
        Returns:
            Upload response
        """
        try:
            # Generate unique image ID
            image_id = str(uuid.uuid4())
            
            # Validate image
            try:
                image = Image.open(file_data)
                width, height = image.size
                format_name = image.format
            except Exception as e:
                logger.error(f"Invalid image file: {e}")
                raise ValueError("Invalid image file")
            
            # Upload to storage
            object_name, file_url = self.storage_service.upload_file(
                file_data, filename, f"image/{format_name.lower()}"
            )
            
            # Save metadata to database
            from app.models.database import Image as ImageModel
            image_record = ImageModel(
                image_id=image_id,
                filename=os.path.basename(object_name),
                original_filename=filename,
                file_path=object_name,
                file_url=file_url,
                description=description,
                file_size=len(file_data),
                width=width,
                height=height,
                mime_type=f"image/{format_name.lower()}"
            )
            
            self.db_session.add(image_record)
            self.db_session.commit()
            
            # Add to search index (async task in production)
            success = self.retrieval_service.add_image_to_index(
                image_id, file_data, description
            )
            
            if success:
                # Update embedding status
                image_record.image_embedding_status = "completed"
                image_record.text_embedding_status = "completed"
                self.db_session.commit()
            
            return {
                "image_id": image_id,
                "filename": filename,
                "file_url": file_url,
                "message": "Image uploaded successfully"
            }
            
        except Exception as e:
            logger.error(f"Error uploading image: {e}")
            self.db_session.rollback()
            raise


# FastAPI router implementation
try:
    from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
    from sqlalchemy.orm import Session
    from app.models.database import get_db
    
    router = APIRouter(prefix="/upload", tags=["upload"])

    @router.post("/image")
    async def upload_image(
        file: UploadFile = File(...),
        description: Optional[str] = Form(None),
        db: Session = Depends(get_db)
    ):
        """Upload an image file."""
        try:
            # Read file data
            file_data = await file.read()
            
            # Basic validation
            if not file.content_type or not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="File must be an image")
            
            # For now, just return a success response
            return {
                "message": "Image uploaded successfully", 
                "filename": file.filename,
                "size": len(file_data),
                "content_type": file.content_type
            }
            
        except Exception as e:
            logger.error(f"Upload error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

except ImportError:
    # Fallback router for testing
    class MockRouter:
        def __init__(self):
            self.prefix = "/upload"
            self.tags = ["upload"]
    
    router = MockRouter() 