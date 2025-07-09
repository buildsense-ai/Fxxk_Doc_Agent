"""
Retrieval service that combines embedding, vector, and database services for hybrid search.
"""

import time
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class RetrievalService:
    """Service that orchestrates hybrid retrieval using multiple services."""
    
    def __init__(self, 
                 embedding_service,
                 vector_service,
                 db_session,
                 text_weight: float = 0.7,
                 image_weight: float = 0.3):
        """Initialize retrieval service with required services."""
        self.embedding_service = embedding_service
        self.vector_service = vector_service
        self.db_session = db_session
        self.text_weight = text_weight
        self.image_weight = image_weight
    
    def search_images(self, 
                     query: str, 
                     top_k: int = 10, 
                     search_type: str = "hybrid") -> Dict[str, Any]:
        """
        Search for images using different strategies.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            search_type: Type of search ("text", "image", "hybrid")
            
        Returns:
            Search results with metadata
        """
        start_time = time.time()
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.encode_text(query, use_clip=True)
            
            # Perform search based on type
            if search_type == "text":
                results = self._text_only_search(query_embedding, top_k)
            elif search_type == "image":
                results = self._image_only_search(query_embedding, top_k)
            else:  # hybrid
                results = self._hybrid_search(query_embedding, top_k)
            
            # Enrich results with database metadata
            enriched_results = self._enrich_results(results)
            
            search_time = time.time() - start_time
            
            return {
                "results": enriched_results,
                "total_found": len(enriched_results),
                "query": query,
                "search_time": search_time,
                "search_type": search_type
            }
            
        except Exception as e:
            logger.error(f"Error in search_images: {e}")
            raise
    
    def _text_only_search(self, query_embedding, top_k: int) -> List[Dict[str, Any]]:
        """Search using text embeddings only."""
        return self.vector_service.search_by_vector(
            query_embedding, 
            vector_field="text", 
            top_k=top_k
        )
    
    def _image_only_search(self, query_embedding, top_k: int) -> List[Dict[str, Any]]:
        """Search using image embeddings only."""
        return self.vector_service.search_by_vector(
            query_embedding, 
            vector_field="image", 
            top_k=top_k
        )
    
    def _hybrid_search(self, query_embedding, top_k: int) -> List[Dict[str, Any]]:
        """Perform hybrid search with re-ranking."""
        return self.vector_service.hybrid_search(
            query_embedding,
            text_weight=self.text_weight,
            image_weight=self.image_weight,
            top_k=top_k * 2  # Get more candidates for re-ranking
        )[:top_k]  # Return top results after re-ranking
    
    def _enrich_results(self, vector_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich vector search results with database metadata."""
        from app.models.database import Image
        
        enriched_results = []
        
        for result in vector_results:
            image_id = result["image_id"]
            
            # Query database for metadata
            try:
                image_record = self.db_session.query(Image).filter(
                    Image.image_id == image_id
                ).first()
                
                if image_record:
                    enriched_result = {
                        "image_id": image_id,
                        "filename": image_record.filename,
                        "file_url": image_record.file_url,
                        "description": image_record.description,
                        "score": result.get("hybrid_score", result.get("score", 0.0)),
                        "text_similarity": result.get("text_score"),
                        "image_similarity": result.get("image_score"),
                        "created_at": image_record.created_at.isoformat() if image_record.created_at else None
                    }
                    enriched_results.append(enriched_result)
                
            except Exception as e:
                logger.error(f"Error enriching result for image_id {image_id}: {e}")
                continue
        
        return enriched_results
    
    def add_image_to_index(self, 
                          image_id: str, 
                          image_data: bytes, 
                          description: Optional[str] = None) -> bool:
        """
        Add image and its embeddings to the search index.
        
        Args:
            image_id: Unique image identifier
            image_data: Image file bytes
            description: Optional text description
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate image embedding
            image_embedding = self.embedding_service.encode_image(image_data)
            
            # Generate text embedding (use description or empty string)
            text_to_embed = description or ""
            text_embedding = self.embedding_service.encode_text(text_to_embed, use_clip=False)
            
            # Insert into vector database
            self.vector_service.insert_embeddings(
                image_ids=[image_id],
                image_embeddings=[image_embedding],
                text_embeddings=[text_embedding]
            )
            
            logger.info(f"Successfully added image {image_id} to search index")
            return True
            
        except Exception as e:
            logger.error(f"Error adding image to index: {e}")
            return False
    
    def remove_image_from_index(self, image_id: str) -> bool:
        """Remove image from search index."""
        try:
            return self.vector_service.delete_by_image_id(image_id)
        except Exception as e:
            logger.error(f"Error removing image from index: {e}")
            return False 