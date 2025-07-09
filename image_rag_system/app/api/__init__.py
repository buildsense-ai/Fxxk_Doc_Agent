"""
API endpoints for the Image RAG system.
"""

from .upload import router as upload_router
from .search import router as search_router

__all__ = ["upload_router", "search_router"] 