"""Vector database service using ChromaDB."""

import numpy as np
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class VectorService:
    """Service for vector database operations using ChromaDB."""
    
    def __init__(self, host: str = "localhost", port: int = 8000, collection_name: str = "image_embeddings"):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        
    def _connect(self):
        """Connect to ChromaDB using PersistentClient."""
        if self.client is None:
            try:
                import chromadb
                import os
                
                # 尝试多个可能的路径，优先使用image_rag_system/chroma
                possible_paths = [
                    "image_rag_system/chroma",  # 从项目根目录（优先）
                    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "chroma"),  # 相对于此文件  
                    "./chroma",  # 当前目录（最后）
                ]
                
                chroma_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        chroma_path = path
                        break
                
                if not chroma_path:
                    # 如果都不存在，使用第一个路径（会创建新的）
                    chroma_path = possible_paths[0]
                
                # Use PersistentClient for direct file access (more reliable)
                self.client = chromadb.PersistentClient(path=chroma_path)
                
                logger.info(f"Connected to ChromaDB using PersistentClient (path: {chroma_path})")
                
            except ImportError:
                logger.error("chromadb library not installed")
                raise
            except Exception as e:
                logger.error(f"Error connecting to ChromaDB: {e}")
                raise
    
    def create_collection(self, image_embedding_dim: int = 512, text_embedding_dim: int = 384):
        """Create or get collection for storing embeddings."""
        self._connect()
        
        if self.client is None:
            raise RuntimeError("ChromaDB client not initialized")
        
        try:
            # 检查集合是否存在
            try:
                existing_collection = self.client.get_collection(name=self.collection_name)
                # 如果集合存在，直接使用它
                self.collection = existing_collection
                logger.info(f"✅ 使用现有集合 {self.collection_name}")
                return
            except:
                pass  # 集合不存在，继续创建
            
            # 创建新集合
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info(f"✅ 集合 {self.collection_name} 创建成功 (文本维度: {text_embedding_dim})")
            
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            raise
    
    def insert_embeddings(self, 
                         image_ids: List[str],
                         image_embeddings: List[np.ndarray],
                         text_embeddings: List[np.ndarray]) -> bool:
        """Insert image and text embeddings into the collection."""
        self._connect()
        
        if self.collection is None:
            self.create_collection()
        
        if self.collection is None:
            logger.error("Collection not initialized")
            return False
        
        try:
            # Prepare documents and embeddings
            documents = []
            embeddings = []
            ids = []
            metadatas = []
            
            for i, image_id in enumerate(image_ids):
                # Add image embedding
                img_id = f"{image_id}_image"
                ids.append(img_id)
                embeddings.append(image_embeddings[i].tolist())
                documents.append(f"Image {image_id}")
                metadatas.append({
                    "image_id": image_id,
                    "type": "image"
                })
                
                # Add text embedding
                text_id = f"{image_id}_text"
                ids.append(text_id)
                embeddings.append(text_embeddings[i].tolist())
                documents.append(f"Text for {image_id}")
                metadatas.append({
                    "image_id": image_id,
                    "type": "text"
                })
            
            # Insert into collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Inserted {len(image_ids)} embeddings into collection")
            return True
            
        except Exception as e:
            logger.error(f"Error inserting embeddings: {e}")
            return False
    
    def search_by_vector(self, 
                        query_vector: np.ndarray,
                        vector_field: str = "text",
                        top_k: int = 10) -> List[Dict[str, Any]]:
        """Search for similar vectors in the collection."""
        self._connect()
        
        if self.collection is None:
            self.create_collection()
        
        if self.collection is None:
            logger.error("Collection not initialized")
            return []
        
        try:
            # Query the collection
            results = self.collection.query(
                query_embeddings=[query_vector.tolist()],
                n_results=top_k,
                where={"type": vector_field},
                include=["metadatas", "distances"]
            )
            
            # Process results
            search_results = []
            if results and results.get('ids') and len(results['ids']) > 0:
                for i, doc_id in enumerate(results['ids'][0]):
                    metadata = results['metadatas'][0][i] if results.get('metadatas') else {}
                    distance = results['distances'][0][i] if results.get('distances') else 1.0
                    
                    search_results.append({
                        "image_id": metadata.get("image_id"),
                        "score": 1.0 - distance,  # Convert distance to similarity
                        "distance": distance
                    })
            
            logger.info(f"Found {len(search_results)} similar vectors")
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            return []
    
    def hybrid_search(self,
                     query_vector: np.ndarray,
                     text_weight: float = 0.7,
                     image_weight: float = 0.3,
                     top_k: int = 20) -> List[Dict[str, Any]]:
        """Perform hybrid search using both text and image embeddings."""
        try:
            # Search in text embeddings
            text_results = self.search_by_vector(
                query_vector, 
                vector_field="text", 
                top_k=top_k
            )
            
            # Search in image embeddings
            image_results = self.search_by_vector(
                query_vector, 
                vector_field="image", 
                top_k=top_k
            )
            
            # Combine results and calculate hybrid scores
            combined_results = {}
            
            # Process text results
            for result in text_results:
                image_id = result["image_id"]
                combined_results[image_id] = {
                    "image_id": image_id,
                    "text_score": result["score"],
                    "image_score": 0.0,
                    "hybrid_score": text_weight * result["score"]
                }
            
            # Process image results
            for result in image_results:
                image_id = result["image_id"]
                if image_id in combined_results:
                    combined_results[image_id]["image_score"] = result["score"]
                    combined_results[image_id]["hybrid_score"] = (
                        text_weight * combined_results[image_id]["text_score"] +
                        image_weight * result["score"]
                    )
                else:
                    combined_results[image_id] = {
                        "image_id": image_id,
                        "text_score": 0.0,
                        "image_score": result["score"],
                        "hybrid_score": image_weight * result["score"]
                    }
            
            # Sort by hybrid score
            final_results = sorted(
                combined_results.values(), 
                key=lambda x: x["hybrid_score"], 
                reverse=True
            )
            
            logger.info(f"Hybrid search returned {len(final_results)} results")
            return final_results
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return []
    
    def delete_by_image_id(self, image_id: str) -> bool:
        """Delete embeddings by image ID."""
        self._connect()
        
        if self.collection is None:
            self.create_collection()
        
        try:
            # Delete both image and text embeddings
            ids_to_delete = [f"{image_id}_image", f"{image_id}_text"]
            
            self.collection.delete(ids=ids_to_delete)
            
            logger.info(f"Deleted embeddings for image_id: {image_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting embeddings: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        self._connect()
        
        if self.collection is None:
            self.create_collection()
        
        try:
            count = self.collection.count()
            return {
                "name": self.collection_name,
                "num_entities": count,
                "database": "ChromaDB"
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {} 