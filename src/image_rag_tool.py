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

class ImageRAGTool(Tool):
    """图片RAG工具 - 图片上传和基于文本描述的图片检索"""
    
    def __init__(self):
        super().__init__(
            name="image_rag_tool",
            description="🖼️ 图片RAG系统 - 上传图片和用户描述，支持基于文本描述的图片检索。参数：action(upload/search), image_path(图片路径), description(用户提供的图片描述), query(搜索查询)"
        )
        
        # 初始化服务
        self.embedding_service = None
        self.vector_service = None
        self.gemini_service = None
        self.database_service = None
        self.minio_service = None
        self.is_advanced_embedding = False
        
        self._initialize_services()
    
    def _initialize_services(self):
        """初始化图片RAG服务"""
        try:
            # 1. 初始化嵌入服务
            try:
                self.embedding_service = AdvancedEmbeddingService()
                if self.embedding_service.is_available():
                    self.is_advanced_embedding = True
                    print("✅ 图片RAG: 使用高质量嵌入服务 (BGE-M3)")
                else:
                    self.embedding_service = SimpleEmbeddingService()
                    self.is_advanced_embedding = False
                    print("✅ 图片RAG: 使用简化嵌入服务")
            except Exception as e:
                print(f"⚠️ 图片RAG: 嵌入服务初始化失败: {e}")
                return
            
            # 2. 初始化Gemini服务
            try:
                self.gemini_service = GeminiDescriptionService()
                if self.gemini_service.is_available():
                    print("✅ 图片RAG: Gemini描述服务可用")
                else:
                    print("⚠️ 图片RAG: Gemini服务不可用")
            except Exception as e:
                print(f"⚠️ 图片RAG: Gemini服务初始化失败: {e}")
            
            # 3. 初始化向量服务
            try:
                self.vector_service = VectorService()
                print("✅ 图片RAG: ChromaDB服务初始化成功")
            except Exception as e:
                print(f"⚠️ 图片RAG: ChromaDB服务初始化失败: {e}")
            
            # 4. 初始化数据库服务
            try:
                self.database_service = DatabaseService()
                print("✅ 图片RAG: MySQL数据库服务初始化成功")
            except Exception as e:
                print(f"⚠️ 图片RAG: 数据库服务初始化失败: {e}")
            
            # 5. 初始化MinIO服务
            try:
                self.minio_service = MinIOService()
                if self.minio_service.is_available():
                    print("✅ 图片RAG: MinIO对象存储服务初始化成功")
                else:
                    print("⚠️ 图片RAG: MinIO服务不可用")
            except Exception as e:
                print(f"⚠️ 图片RAG: MinIO服务初始化失败: {e}")
                
        except Exception as e:
            print(f"❌ 图片RAG工具初始化失败: {e}")
    
    def execute(self, **kwargs) -> str:
        """执行图片RAG操作"""
        action = kwargs.get('action', '').lower()
        
        if action == 'upload':
            return self._upload_image(**kwargs)
        elif action == 'search':
            return self._search_images(**kwargs)
        elif action == 'list':
            return self._list_images(**kwargs)
        elif action == 'stats':
            return self._get_stats(**kwargs)
        elif action == 'process_images_json':
            return self._process_images_json(**kwargs)
        else:
            return f"❌ 不支持的操作: {action}。支持的操作: upload, search, list, stats, process_images_json"
    
    def _upload_image(self, **kwargs) -> str:
        """上传图片并生成描述"""
        image_path = kwargs.get('image_path')
        description = kwargs.get('description', '')
        source_file = kwargs.get('source_file')
        
        if not image_path or not os.path.exists(image_path):
            return "❌ 图片路径不存在或未提供"
        
        try:
            # 读取图片文件
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # 生成图片ID
            import uuid
            image_id = str(uuid.uuid4())
            
            # 使用Gemini生成图片描述（暂时注释掉）
            # if self.gemini_service and self.gemini_service.is_available():
            #     try:
            #         ai_description = self.gemini_service.generate_description(image_data)
            #         if not description:
            #             description = ai_description
            #         else:
            #             description = f"{description}\n\nAI描述: {ai_description}"
            #     except Exception as e:
            #         print(f"⚠️ Gemini描述生成失败: {e}")
            
            # 检查用户是否提供了描述
            if not description:
                return "❌ 请提供图片描述，用于后续的RAG检索"
            
            # 存储图片到MinIO
            storage_url = None
            object_name = None
            bucket_name = None
            
            if self.minio_service and self.minio_service.is_available():
                try:
                    upload_result = self.minio_service.upload_image(
                        image_data=image_data,
                        filename=os.path.basename(image_path),
                        image_id=image_id
                    )
                    if upload_result:
                        storage_url = upload_result.get('file_url')
                        object_name = upload_result.get('object_name')
                        bucket_name = upload_result.get('bucket_name')
                        print(f"✅ MinIO上传成功: {storage_url}")
                    else:
                        print("⚠️ MinIO上传返回空结果")
                except Exception as e:
                    print(f"⚠️ MinIO存储失败: {e}")
            else:
                print("⚠️ MinIO服务不可用")
            
            # 保存到数据库（包含MinIO信息）
            if self.database_service:
                try:
                    self.database_service.create_image_record(
                        image_id=image_id,
                        filename=os.path.basename(image_path),
                        original_filename=os.path.basename(image_path),
                        user_description=description,
                        file_size=len(image_data),
                        minio_url=storage_url,
                        object_name=object_name,
                        bucket_name=bucket_name,
                        source_file=source_file
                    )
                    print(f"✅ 数据库记录保存成功，包含MinIO URL: {storage_url}")
                except Exception as e:
                    print(f"⚠️ 数据库保存失败: {e}")
            else:
                print("⚠️ 数据库服务不可用")
            
            # 构建返回信息
            result_info = f"✅ 图片上传成功！\n"
            result_info += f"🆔 图片ID: {image_id}\n"
            result_info += f"📄 文件名: {os.path.basename(image_path)}\n"
            result_info += f"📝 描述: {description[:100]}{'...' if len(description) > 100 else ''}\n"
            
            if storage_url:
                result_info += f"🔗 访问URL: {storage_url}\n"
            else:
                result_info += f"⚠️ 存储URL: 未生成\n"
            
            result_info += f"💾 文件大小: {len(image_data)} 字节\n"
            result_info += f"📊 存储位置: MinIO ({self.minio_service.bucket_name if self.minio_service else 'N/A'})\n"
            result_info += f"🗄️ 数据库: MySQL (已保存记录)"
            
            # 向量化存储
            if self.embedding_service and self.vector_service:
                try:
                    # 获取文本嵌入
                    if self.is_advanced_embedding:
                        embedding = self.embedding_service.embed_documents([description])[0]
                    else:
                        embedding = self.embedding_service.encode_text(description)
                    
                    # 存储到向量数据库
                    self.vector_service.insert_embeddings(
                        image_ids=[image_id],
                        image_embeddings=[embedding],  # 使用文本嵌入作为图片嵌入
                        text_embeddings=[embedding]
                    )
                except Exception as e:
                    print(f"⚠️ 向量化存储失败: {e}")
            
            return result_info
            
        except Exception as e:
            return f"❌ 图片上传失败: {e}"
    
    def _search_images(self, **kwargs) -> str:
        """基于文本描述搜索图片"""
        query = kwargs.get('query', '')
        top_k = kwargs.get('top_k', 10)
        min_score = kwargs.get('min_score', 0.0)
        
        if not query:
            return "❌ 搜索查询不能为空"
        
        if not self.embedding_service or not self.vector_service:
            return "❌ 嵌入服务或向量服务未初始化"
        
        try:
            # 获取查询嵌入
            if self.is_advanced_embedding:
                query_embedding = self.embedding_service.embed_query(query)
            else:
                query_embedding = self.embedding_service.encode_text(query)
            
            # 搜索相似文档
            results = self.vector_service.search_by_vector(
                query_vector=query_embedding,
                vector_field="text",
                top_k=top_k
            )
            
            if not results:
                return f"🔍 未找到与'{query}'相关的图片"
            
            # 格式化结果
            result_text = f"🔍 找到 {len(results)} 张相关图片:\n\n"
            for i, result in enumerate(results, 1):
                image_id = result.get('image_id', 'N/A')
                score = result.get('score', 0)
                
                # 从数据库获取图片信息
                if self.database_service:
                    image_info = self.database_service.get_image_by_id(image_id)
                    if image_info:
                        filename = image_info.get('filename', '未知文件')
                        description = image_info.get('user_description', '')[:100]
                        
                        # 直接从数据库获取MinIO URL
                        image_url = image_info.get('minio_url')
                        if not image_url:
                            # 如果数据库中没有URL，尝试从MinIO服务获取
                            if self.minio_service and self.minio_service.is_available():
                                file_ext = filename.split('.')[-1] if '.' in filename else 'jpg'
                                image_url = self.minio_service.get_image_url(image_id, file_ext)
                    else:
                        filename = '未知文件'
                        description = '描述不可用'
                        image_url = None
                else:
                    filename = '未知文件'
                    description = '描述不可用'
                    image_url = None
                
                result_text += f"{i}. 📄 {filename}\n"
                result_text += f"   描述: {description}{'...' if len(description) == 100 else ''}\n"
                result_text += f"   相似度: {score:.3f}\n"
                result_text += f"   图片ID: {image_id}\n"
                if image_url:
                    result_text += f"   🔗 图片URL: {image_url}\n"
                result_text += "\n"
            
            return result_text
            
        except Exception as e:
            return f"❌ 图片搜索失败: {e}"
    
    def _list_images(self, **kwargs) -> str:
        """列出所有图片"""
        limit = kwargs.get('limit', 20)
        offset = kwargs.get('offset', 0)
        
        if not self.database_service:
            return "❌ 数据库服务未初始化"
        
        try:
            images = self.database_service.get_images_list(limit=limit, offset=offset)
            
            if not images:
                return "📚 暂无图片记录"
            
            result_text = f"📚 图片库 (显示 {len(images)} 张):\n\n"
            for i, image in enumerate(images, 1):
                # 处理Image对象和字典，健壮处理时间和空字段
                if hasattr(image, 'filename'):
                    filename = getattr(image, 'filename', '未知文件') or '未知文件'
                    description = getattr(image, 'user_description', None) or getattr(image, 'combined_description', None) or ''
                    created_at = getattr(image, 'created_at', None)
                    if created_at:
                        try:
                            created_at_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
                        except Exception:
                            created_at_str = str(created_at)
                    else:
                        created_at_str = 'N/A'
                    image_id = getattr(image, 'image_id', 'N/A')
                else:
                    filename = image.get('filename', '未知文件') or '未知文件'
                    description = image.get('user_description', '') or image.get('description', '')
                    created_at = image.get('created_at', 'N/A')
                    if hasattr(created_at, 'strftime'):
                        try:
                            created_at_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
                        except Exception:
                            created_at_str = str(created_at)
                    else:
                        created_at_str = str(created_at)
                    image_id = image.get('image_id', 'N/A')
                
                result_text += f"{i}. 📄 {filename}\n"
                result_text += f"   描述: {description[:50]}{'...' if len(description) > 50 else ''}\n"
                result_text += f"   上传时间: {created_at_str}\n"
                result_text += f"   图片ID: {image_id}\n\n"
            
            return result_text
            
        except Exception as e:
            return f"❌ 获取图片列表失败: {e}"
    
    def _get_stats(self, **kwargs) -> str:
        """获取图片库统计信息"""
        if not self.database_service:
            return "❌ 数据库服务未初始化"
        
        try:
            stats = self.database_service.get_statistics()
            
            result_text = "📊 图片RAG系统统计信息:\n\n"
            result_text += f"📚 总图片数量: {stats.get('total_images', 0)}\n"
            result_text += f"📅 今日上传: {stats.get('today_uploads', 0)}\n"
            result_text += f"📈 本周上传: {stats.get('week_uploads', 0)}\n"
            result_text += f"💾 总存储大小: {stats.get('total_size_mb', 0):.2f} MB\n"
            
            return result_text
            
        except Exception as e:
            return f"❌ 获取统计信息失败: {e}"
    
    def _process_images_json(self, **kwargs) -> str:
        """
        处理PDF解析工具生成的images.json文件
        """
        folder_path = kwargs.get('folder_path')
        project_name = kwargs.get('project_name', '')
        
        if not folder_path or not os.path.exists(folder_path):
            return f"❌ 文件夹不存在: {folder_path}"
        
        images_json_path = os.path.join(folder_path, "images.json")
        if not os.path.exists(images_json_path):
            return f"❌ images.json not found in {folder_path}"
            
        # 尝试从同级目录的parsed_content.json中获取来源文件
        source_file = f"parsed_from:{folder_path}" # 默认值
        try:
            content_json_path = os.path.join(folder_path, "parsed_content.json")
            if os.path.exists(content_json_path):
                with open(content_json_path, 'r', encoding='utf-8') as f:
                    parsed_data = json.load(f)
                    source_file = parsed_data.get("meta", {}).get("source_file", source_file)
        except Exception as e:
            print(f"⚠️ 读取来源文件元数据失败: {e}")

        processed_count = 0
        failed_count = 0
        
        with open(images_json_path, 'r', encoding='utf-8') as f:
            images_data = json.load(f)
        
        for image_info in images_data.get("images", []):
            try:
                # 获取图片路径
                image_path = image_info.get('image_path')
                if not image_path or not os.path.exists(image_path):
                    print(f"⚠️ 图片文件不存在，跳过: {image_path}")
                    failed_count += 1
                    continue
                
                # 获取图片描述
                description = image_info.get("context", "No description provided.")
                
                # 调用内部的_upload_image方法进行处理
                upload_result = self._upload_image(
                    image_path=image_path,
                    description=description,
                    source_file=source_file  # 传递来源文件
                )
                
                if "✅" in upload_result:
                    processed_count += 1
                else:
                    failed_count += 1
                    print(f"⚠️ 图片处理失败: {image_path}\n{upload_result}")
            
            except Exception as e:
                failed_count += 1
                print(f"❌ 处理图片条目时发生严重错误: {e}", exc_info=True)

        return f"✅ images.json处理完成。成功处理: {processed_count}张图片, 失败: {failed_count}张。" 