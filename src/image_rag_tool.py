"""
图片RAG工具 - 集成image_rag_system功能
支持图片上传和基于文本描述的图片检索
"""
import os
import sys
import json
import base64
import requests
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

# 添加image_rag_system到路径
image_rag_path = Path(__file__).parent.parent / "image_rag_system"
sys.path.insert(0, str(image_rag_path))

try:
    from app.services.embedding_service_advanced import AdvancedEmbeddingService
    from app.services.embedding_service_simple import EmbeddingService as SimpleEmbeddingService
    from app.services.gemini_service import GeminiDescriptionService
    from app.services.vector_service import VectorService
    from app.services.database_service import DatabaseService
    from app.services.minio_service import MinIOService
    from app.models.schemas import ImageUploadRequest, SearchRequest
except ImportError as e:
    print(f"⚠️ 图片RAG系统导入失败: {e}")

from src.base_tool import Tool
from src.openrouter_client import OpenRouterClient
from src.pdf_embedding_service import PDFEmbeddingService # Re-use the unified service

class ImageRAGTool(Tool):
    """图片RAG工具 - 图片上传和基于文本描述的图片检索 (已重构)"""
    
    def __init__(self):
        super().__init__(
            name="image_rag_tool",
            description="🖼️ 图片RAG系统 - 上传图片，自动生成描述并将其嵌入统一知识库。参数：action('upload'), image_path('路径'), description('可选的用户描述')"
        )
        
        # 使用统一的服务
        self.openrouter_client = None
        self.embedding_service = None
        self._initialize_services()
    
    def _initialize_services(self):
        """初始化统一的服务"""
        try:
            self.openrouter_client = OpenRouterClient()
            print("✅ 图片RAG: OpenRouter客户端初始化成功。")
        except Exception as e:
            print(f"⚠️ 图片RAG: OpenRouter客户端初始化失败: {e}")

        try:
            self.embedding_service = PDFEmbeddingService() # Using the unified embedding service
            print("✅ 图片RAG: 统一嵌入服务初始化成功。")
        except Exception as e:
            print(f"⚠️ 图片RAG: 统一嵌入服务初始化失败: {e}")
                
    def execute(self, **kwargs) -> str:
        """执行图片RAG操作"""
        action = kwargs.get('action', '').lower()
        
        if action == 'upload':
            return self._upload_image(**kwargs)
        # Search functionality is now handled by the unified rag_tool_chroma
        elif action in ['search', 'list', 'stats', 'process_images_json']:
             return f"❌ 操作 '{action}' 已被弃用。请使用 'rag_tool_chroma' 进行搜索和列表查询。"
        else:
            return f"❌ 不支持的操作: {action}。仅支持 'upload' 操作。"
    
    def _upload_image(self, **kwargs) -> str:
        """上传图片，生成AI描述，并将其嵌入到统一的知识库"""
        image_path = kwargs.get('image_path')
        user_description = kwargs.get('description', '')
        
        if not image_path or not os.path.exists(image_path):
            return json.dumps({"status": "error", "message": "图片路径不存在或未提供"})
        
        if not self.openrouter_client or not self.embedding_service:
            return json.dumps({"status": "error", "message": "服务未正确初始化"})

        try:
            print(f"🚀 开始处理上传的图片: {image_path}")
            
            # 1. 使用Gemini生成图片描述
            prompt = "请详细描述这张图片的内容，包括场景、物体、人物、风格和任何可见的文本。"
            ai_description = self.openrouter_client.get_image_description_gemini(image_path, prompt=prompt)
            
            if "Error:" in ai_description:
                raise Exception(f"AI描述生成失败: {ai_description}")

            final_description = f"用户描述: {user_description}\n\nAI描述: {ai_description}" if user_description else ai_description
            print(f"📝 生成的描述: {final_description[:150]}...")

            # 2. 准备元数据并嵌入
            metadata = {
                "source_document": Path(image_path).name,
                "document_type": "Image", # Use simplified type for all images
                "upload_timestamp": datetime.now().isoformat(),
                "user_provided_description": bool(user_description)
            }
            
            print(f"💡 正在嵌入描述到 '{self.embedding_service.collection_name}' 集合...")
            embedding_result = self.embedding_service.embed_and_store_text(
                text_chunks=[final_description],
                metadatas=[metadata]
            )

            result = {
                "status": "success",
                "message": "图片处理和嵌入成功。",
                "image_source": image_path,
                "embedding_info": {
                    "chunks_embedded": embedding_result.get("chunks_count", 0),
                    "vector_db_collection": embedding_result.get("collection_name", "N/A")
                }
            }
            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"❌ 图片上传和嵌入流程失败: {e}")
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)

    # All other methods like _search_images, _list_images etc. are now deprecated
    # and their functionality should be handled by rag_tool_chroma.
    def _search_images(self, **kwargs) -> str:
        return "This method is deprecated. Use rag_tool_chroma."
    def _list_images(self, **kwargs) -> str:
        return "This method is deprecated. Use rag_tool_chroma."
    def _get_stats(self, **kwargs) -> str:
        return "This method is deprecated. Use rag_tool_chroma."
    def _process_images_json(self, **kwargs) -> str:
        return "This method is deprecated. Use rag_tool_chroma." 