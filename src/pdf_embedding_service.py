#!/usr/bin/env python3
"""
PDF Embedding Service - PDF解析内容的向量化存储服务
处理parsed_content.json和images.json，将文本和图片进行embedding并存储到统一集合
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import uuid

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("⚠️ ChromaDB不可用，请安装: pip install chromadb")

class PDFEmbeddingService:
    """PDF内容向量化服务 - 统一存储文本和图片"""
    
    def __init__(self, 
                 chroma_db_path: str = "pdf_embedding_storage",
                 collection_name: str = "pdf_unified_embeddings"):
        """
        初始化PDF embedding服务
        
        Args:
            chroma_db_path: ChromaDB存储路径
            collection_name: 统一embedding集合名称
        """
        self.chroma_db_path = chroma_db_path
        self.collection_name = collection_name
        
        # 初始化ChromaDB
        self._init_chroma_db()
        
    def _init_chroma_db(self):
        """初始化ChromaDB客户端和集合"""
        if not CHROMADB_AVAILABLE:
            raise RuntimeError("ChromaDB不可用，无法初始化embedding服务")
            
        try:
            # 创建存储目录
            os.makedirs(self.chroma_db_path, exist_ok=True)
            
            # 初始化ChromaDB客户端
            self.chroma_client = chromadb.PersistentClient(
                path=self.chroma_db_path,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # 获取或创建统一集合
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "PDF文本和图片内容统一向量化存储"}
            )
            
            print(f"✅ ChromaDB初始化成功: {self.chroma_db_path}")
            print(f"📊 使用统一集合: {self.collection_name}")
            
        except Exception as e:
            print(f"❌ ChromaDB初始化失败: {e}")
            raise
    
    def embed_parsed_pdf(self, 
                        parsed_content_path: str, 
                        images_json_path: str,
                        parser_output_dir: str) -> Dict:
        """
        对解析后的PDF内容进行embedding
        
        Args:
            parsed_content_path: parsed_content.json文件路径
            images_json_path: images.json文件路径  
            parser_output_dir: 解析器输出目录
            
        Returns:
            Dict: embedding结果统计
        """
        stats = {
            "text_embeddings": 0,
            "image_embeddings": 0,
            "total_embeddings": 0,
            "errors": []
        }
        
        try:
            # 获取源文件信息
            source_file, title = self._get_source_info(parsed_content_path)
            
            # 准备批量数据
            documents = []
            metadatas = []
            ids = []
            
            # 1. 处理文本内容
            if os.path.exists(parsed_content_path):
                text_docs, text_metas, text_ids = self._prepare_text_embeddings(
                    parsed_content_path, source_file, title, parser_output_dir
                )
                documents.extend(text_docs)
                metadatas.extend(text_metas)
                ids.extend(text_ids)
                stats["text_embeddings"] = len(text_docs)
                
                if text_docs:
                    print(f"✅ 准备文本embedding: {len(text_docs)}个section")
            else:
                stats["errors"].append(f"文本文件不存在: {parsed_content_path}")
            
            # 2. 处理图片内容
            if os.path.exists(images_json_path):
                image_docs, image_metas, image_ids = self._prepare_image_embeddings(
                    images_json_path, source_file, title, parser_output_dir
                )
                documents.extend(image_docs)
                metadatas.extend(image_metas)
                ids.extend(image_ids)
                stats["image_embeddings"] = len(image_docs)
                
                if image_docs:
                    print(f"✅ 准备图片embedding: {len(image_docs)}个图片")
            else:
                stats["errors"].append(f"图片文件不存在: {images_json_path}")
            
            # 3. 批量添加到ChromaDB
            if documents:
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                stats["total_embeddings"] = len(documents)
                print(f"✅ 批量embedding完成: {len(documents)}个项目")
            else:
                stats["errors"].append("没有找到可嵌入的内容")
                
        except Exception as e:
            error_msg = f"PDF embedding失败: {e}"
            stats["errors"].append(error_msg)
            print(f"❌ {error_msg}")
            
        return stats
    
    def _get_source_info(self, parsed_content_path: str) -> Tuple[str, str]:
        """获取源文件信息"""
        source_file = "unknown"
        title = "unknown"
        
        try:
            if os.path.exists(parsed_content_path):
                with open(parsed_content_path, 'r', encoding='utf-8') as f:
                    content_data = json.load(f)
                    metadata_info = content_data.get("metadata", {})
                    source_file = metadata_info.get("source_file", "unknown")
                    title = metadata_info.get("title", "unknown")
                    
                    # 修复文件名编码问题
                    source_file = self._fix_filename_encoding(source_file)
                    title = self._fix_filename_encoding(title)
                    
        except Exception as e:
            print(f"⚠️ 获取源文件信息失败: {e}")
            
        return source_file, title
    
    def _fix_filename_encoding(self, filename: str) -> str:
        """修复文件名编码问题"""
        if not filename or filename == "unknown":
            return filename
            
        try:
            # 尝试修复URL编码的中文字符
            import urllib.parse
            # 先尝试URL解码
            try:
                decoded = urllib.parse.unquote(filename, encoding='utf-8')
                if decoded != filename:
                    filename = decoded
            except:
                pass
            
            # 处理常见的编码问题
            # 如果包含特殊编码字符，尝试重新编码
            if 'å' in filename or 'ç' in filename or 'è' in filename:
                try:
                    # 尝试从latin-1解码为utf-8
                    fixed = filename.encode('latin-1').decode('utf-8')
                    filename = fixed
                except:
                    # 如果失败，尝试其他方法
                    try:
                        # 尝试从gbk解码
                        fixed = filename.encode('latin-1').decode('gbk')
                        filename = fixed
                    except:
                        pass
            
            # 提取文件名（去掉路径）
            filename = os.path.basename(filename)
            
            # 如果文件名仍然包含乱码，尝试从文件路径中提取
            if any(char in filename for char in ['å', 'ç', 'è', 'ã', 'â']):
                # 尝试使用时间戳作为标识
                import re
                timestamp_match = re.search(r'(\d{13})', filename)
                if timestamp_match:
                    timestamp = timestamp_match.group(1)
                    # 尝试找到PDF扩展名
                    if '.pdf' in filename.lower():
                        filename = f"文档_{timestamp}.pdf"
                    else:
                        filename = f"文档_{timestamp}"
                else:
                    # 如果没有时间戳，使用通用名称
                    if '.pdf' in filename.lower():
                        filename = "PDF文档.pdf"
                    else:
                        filename = "PDF文档"
            
        except Exception as e:
            print(f"⚠️ 修复文件名编码失败: {e}")
            # 如果所有方法都失败，使用通用名称
            filename = "PDF文档"
            
        return filename
    
    def _prepare_text_embeddings(self, parsed_content_path: str, source_file: str, 
                                title: str, parser_output_dir: str) -> Tuple[List[str], List[Dict], List[str]]:
        """准备文本内容的embedding数据"""
        documents = []
        metadatas = []
        ids = []
        
        try:
            # 读取解析内容
            with open(parsed_content_path, 'r', encoding='utf-8') as f:
                content_data = json.load(f)
            
            # 处理每个section
            sections = content_data.get("sections", [])
            
            for i, section in enumerate(sections):
                content = section.get("content", "").strip()
                if not content:
                    continue
                    
                # 生成唯一ID
                section_id = self._generate_id(source_file, "text", i, content)
                
                # 构建元数据
                section_metadata = {
                    "source_file": source_file,
                    "document_title": title,
                    "content_type": "text",  # 关键字段：区分文本和图片
                    "section_index": i,
                    "source_page": section.get("source_page", i),
                    "content_length": len(content),
                    "embedding_time": datetime.now().isoformat(),
                    "parser_output_path": parser_output_dir
                }
                
                documents.append(content)
                metadatas.append(section_metadata)
                ids.append(section_id)
                
        except Exception as e:
            print(f"❌ 文本embedding准备失败: {e}")
            
        return documents, metadatas, ids
    
    def _prepare_image_embeddings(self, images_json_path: str, source_file: str,
                                 title: str, parser_output_dir: str) -> Tuple[List[str], List[Dict], List[str]]:
        """准备图片内容的embedding数据"""
        documents = []
        metadatas = []
        ids = []
        
        try:
            # 读取图片信息
            with open(images_json_path, 'r', encoding='utf-8') as f:
                images_data = json.load(f)
            
            for image_id, image_info in images_data.items():
                # 构建图片描述文档（用于文本搜索）
                caption = image_info.get("caption", f"图片 {image_id}")
                context = image_info.get("context", "")
                image_path = image_info.get("image_path", "")
                
                # 组合图片的文本描述
                image_description = f"{caption}"
                if context:
                    image_description += f"\n上下文: {context}"
                
                # 生成唯一ID
                img_id = self._generate_id(source_file, "image", image_id, image_path)
                
                # 构建元数据
                image_metadata = {
                    "source_file": source_file,
                    "document_title": title,
                    "content_type": "image",  # 关键字段：区分文本和图片
                    "image_id": image_id,
                    "image_path": image_path,
                    "caption": caption,
                    "context": context,
                    "width": image_info.get("width", 0),
                    "height": image_info.get("height", 0),
                    "figure_size": image_info.get("figure_size", 0),
                    "figure_aspect": image_info.get("figure_aspect", 1.0),
                    "embedding_time": datetime.now().isoformat(),
                    "parser_output_path": parser_output_dir
                }
                
                documents.append(image_description)
                metadatas.append(image_metadata)
                ids.append(img_id)
                
        except Exception as e:
            print(f"❌ 图片embedding准备失败: {e}")
            
        return documents, metadatas, ids
    
    def _generate_id(self, source_file: str, content_type: str, index_or_id: any, content: str) -> str:
        """生成内容的唯一ID"""
        # 使用源文件路径、内容类型、索引和内容hash生成唯一ID
        content_hash = hashlib.md5(str(content).encode('utf-8')).hexdigest()[:8]
        file_name = os.path.basename(source_file)
        return f"{content_type}_{file_name}_{index_or_id}_{content_hash}"
    
    def search(self, query: str, 
               content_type: Optional[str] = None,
               top_k: int = 5, 
               source_file_filter: Optional[str] = None) -> List[Dict]:
        """
        统一搜索接口
        
        Args:
            query: 搜索查询
            content_type: 内容类型过滤 ("text", "image", None表示搜索全部)
            top_k: 返回结果数量
            source_file_filter: 源文件过滤器
            
        Returns:
            List[Dict]: 搜索结果
        """
        try:
            # 构建查询条件
            where_condition = {}
            
            if content_type:
                where_condition["content_type"] = content_type
                
            if source_file_filter:
                where_condition["source_file"] = source_file_filter
            
            # 执行搜索
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_condition if where_condition else None
            )
            
            # 格式化结果
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    result = {
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if results["distances"] else None,
                        "id": results["ids"][0][i],
                        "content_type": results["metadatas"][0][i].get("content_type", "unknown")
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return []
    
    def get_collection_stats(self) -> Dict:
        """获取集合统计信息"""
        try:
            total_count = self.collection.count()
            
            # 获取按内容类型分组的统计
            stats = {
                "total_embeddings": total_count,
                "collection_name": self.collection_name
            }
            
            # 尝试获取分类统计（如果集合不为空）
            if total_count > 0:
                try:
                    # 获取所有元数据来统计类型分布
                    all_results = self.collection.get()
                    
                    text_count = 0
                    image_count = 0
                    
                    for metadata in all_results["metadatas"]:
                        content_type = metadata.get("content_type", "unknown")
                        if content_type == "text":
                            text_count += 1
                        elif content_type == "image":
                            image_count += 1
                    
                    stats["text_embeddings"] = text_count
                    stats["image_embeddings"] = image_count
                    
                except Exception as e:
                    print(f"⚠️ 获取详细统计失败: {e}")
                    stats["text_embeddings"] = "unknown"
                    stats["image_embeddings"] = "unknown"
            else:
                stats["text_embeddings"] = 0
                stats["image_embeddings"] = 0
            
            return stats
            
        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
            return {"error": str(e)} 