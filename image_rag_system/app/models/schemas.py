"""
Pydantic schemas for API request/response validation.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

# Using basic Python classes for schemas to avoid import errors
# In production, replace with proper Pydantic models after installing dependencies

class ImageUploadRequest:
    """Schema for image upload request."""
    
    def __init__(self, description: Optional[str] = None, generate_ai_description: bool = True):
        self.description = description  # 用户描述
        self.generate_ai_description = generate_ai_description  # 是否生成AI描述


class ImageUploadResponse:
    """Schema for image upload response."""
    
    def __init__(self, image_id: str, filename: str, file_url: str, message: str, 
                 user_description: Optional[str] = None, ai_description: Optional[str] = None,
                 ai_generation_info: Optional[Dict[str, Any]] = None):
        self.image_id = image_id
        self.filename = filename
        self.file_url = file_url
        self.message = message
        self.user_description = user_description  # 用户描述
        self.ai_description = ai_description      # AI生成的描述
        self.ai_generation_info = ai_generation_info  # AI生成的元信息


class SearchRequest:
    """Schema for search request."""
    
    def __init__(self, query: str, top_k: int = 10, search_type: str = "hybrid"):
        self.query = query
        self.top_k = top_k
        self.search_type = search_type  # "text", "image", "hybrid"


class ImageResult:
    """Schema for individual search result."""
    
    def __init__(self, 
                 image_id: str,
                 filename: str,
                 file_url: str,
                 description: Optional[str],  # 保留向后兼容
                 score: float,
                 text_similarity: Optional[float] = None,
                 image_similarity: Optional[float] = None,
                 user_description: Optional[str] = None,    # 用户描述
                 ai_description: Optional[str] = None,      # AI描述
                 matched_description_type: Optional[str] = None):  # 匹配的描述类型
        self.image_id = image_id
        self.filename = filename
        self.file_url = file_url
        self.description = description  # 向后兼容，通常是合并后的描述
        self.score = score
        self.text_similarity = text_similarity
        self.image_similarity = image_similarity
        self.user_description = user_description
        self.ai_description = ai_description
        self.matched_description_type = matched_description_type  # "user", "ai", "both"


class SearchResponse:
    """Schema for search response."""
    
    def __init__(self, results: List[ImageResult], total_found: int, query: str, search_time: float):
        self.results = results
        self.total_found = total_found
        self.query = query
        self.search_time = search_time


# TODO: Replace with proper Pydantic models when dependencies are installed
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ImageUploadRequest(BaseModel):
    description: Optional[str] = None

class ImageUploadResponse(BaseModel):
    image_id: str
    filename: str
    file_url: str
    message: str

class SearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=10, ge=1, le=100)
    search_type: str = Field(default="hybrid", regex="^(text|image|hybrid)$")

class ImageResult(BaseModel):
    image_id: str
    filename: str
    file_url: str
    description: Optional[str]
    score: float
    text_similarity: Optional[float] = None
    image_similarity: Optional[float] = None

class SearchResponse(BaseModel):
    results: List[ImageResult]
    total_found: int
    query: str
    search_time: float
""" 