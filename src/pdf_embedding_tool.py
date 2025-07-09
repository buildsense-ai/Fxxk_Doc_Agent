#!/usr/bin/env python3
"""
PDF Embedding Tool - PDF内容向量化工具
将解析后的PDF内容进行embedding并提供统一的搜索功能
"""

import json
import os
from typing import Dict, Optional
from src.base_tool import Tool
from src.pdf_embedding_service import PDFEmbeddingService

class PDFEmbeddingTool(Tool):
    """PDF内容向量化工具 - 统一处理文本和图片"""
    
    def __init__(self):
        super().__init__(
            name="pdf_embedding",
            description="📊 PDF内容向量化工具 - 将解析后的PDF内容进行embedding存储，支持文本和图片的统一语义搜索"
        )
        self.embedding_service = None
        self._init_service()
    
    def _init_service(self):
        """初始化embedding服务"""
        try:
            self.embedding_service = PDFEmbeddingService()
            print("✅ PDF embedding服务初始化成功")
        except Exception as e:
            print(f"❌ PDF embedding服务初始化失败: {e}")
            self.embedding_service = None
    
    def execute(self, **kwargs) -> str:
        """
        执行PDF embedding操作
        
        Args:
            action: 操作类型 (embed/search/stats)
            parser_output_dir: 解析器输出目录（用于embed操作）
            query: 搜索查询（用于search操作）
            content_type: 内容类型过滤 ("text", "image", "all"或None，用于search操作)
            top_k: 返回结果数量（默认5）
            source_file_filter: 源文件过滤器（可选）
            
        Returns:
            str: JSON格式的操作结果
        """
        if not self.embedding_service:
            return json.dumps({
                "status": "error",
                "message": "PDF embedding服务不可用"
            }, indent=2, ensure_ascii=False)
        
        action = kwargs.get("action", "embed")
        
        if action == "embed":
            return self._embed_pdf_content(**kwargs)
        elif action == "search":
            return self._search_content(**kwargs)
        elif action == "stats":
            return self._get_stats(**kwargs)
        else:
            return json.dumps({
                "status": "error",
                "message": f"不支持的操作: {action}。支持的操作: embed, search, stats"
            }, indent=2, ensure_ascii=False)
    
    def _embed_pdf_content(self, **kwargs) -> str:
        """对PDF解析内容进行embedding"""
        parser_output_dir = kwargs.get("parser_output_dir")
        
        if not parser_output_dir:
            return json.dumps({
                "status": "error",
                "message": "请提供解析器输出目录 (parser_output_dir参数)"
            }, indent=2, ensure_ascii=False)
        
        if not os.path.exists(parser_output_dir):
            return json.dumps({
                "status": "error",
                "message": f"解析器输出目录不存在: {parser_output_dir}"
            }, indent=2, ensure_ascii=False)
        
        # 构建文件路径
        parsed_content_path = os.path.join(parser_output_dir, "parsed_content.json")
        images_json_path = os.path.join(parser_output_dir, "images.json")
        
        try:
            # 执行embedding
            stats = self.embedding_service.embed_parsed_pdf(
                parsed_content_path=parsed_content_path,
                images_json_path=images_json_path,
                parser_output_dir=parser_output_dir
            )
            
            result = {
                "status": "success",
                "message": "PDF内容embedding完成",
                "statistics": stats,
                "input_directory": parser_output_dir
            }
            
            return json.dumps(result, indent=2, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"PDF embedding失败: {str(e)}"
            }, indent=2, ensure_ascii=False)
    
    def _search_content(self, **kwargs) -> str:
        """统一搜索内容"""
        query = kwargs.get("query")
        if not query:
            return json.dumps({
                "status": "error",
                "message": "请提供搜索查询 (query参数)"
            }, indent=2, ensure_ascii=False)
        
        # 处理content_type参数
        content_type = kwargs.get("content_type", "all")
        if content_type == "all":
            content_type = None  # None表示搜索全部类型
        elif content_type not in ["text", "image", None]:
            return json.dumps({
                "status": "error",
                "message": f"不支持的content_type: {content_type}。支持: text, image, all"
            }, indent=2, ensure_ascii=False)
        
        top_k = kwargs.get("top_k", 5)
        source_file_filter = kwargs.get("source_file_filter")
        
        try:
            results = self.embedding_service.search(
                query=query,
                content_type=content_type,
                top_k=top_k,
                source_file_filter=source_file_filter
            )
            
            # 统计结果类型
            text_count = sum(1 for r in results if r.get("content_type") == "text")
            image_count = sum(1 for r in results if r.get("content_type") == "image")
            
            search_type_desc = {
                "text": "仅文本",
                "image": "仅图片", 
                None: "文本和图片"
            }.get(content_type, "未知")
            
            return json.dumps({
                "status": "success",
                "message": f"搜索完成 - {search_type_desc}",
                "query": query,
                "search_scope": search_type_desc,
                "total_results": len(results),
                "text_results": text_count,
                "image_results": image_count,
                "results": results
            }, indent=2, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"搜索失败: {str(e)}"
            }, indent=2, ensure_ascii=False)
    
    def _get_stats(self, **kwargs) -> str:
        """获取embedding统计信息"""
        try:
            stats = self.embedding_service.get_collection_stats()
            
            return json.dumps({
                "status": "success",
                "message": "统计信息获取成功",
                "statistics": stats
            }, indent=2, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"获取统计信息失败: {str(e)}"
            }, indent=2, ensure_ascii=False)
    
    def get_usage_guide(self) -> str:
        """获取使用指南"""
        return """
📊 PDF Embedding工具使用指南

🔧 基本用法:
1. 嵌入PDF内容: pdf_embedding(action="embed", parser_output_dir="parser_output/xxx")
2. 统一搜索: pdf_embedding(action="search", query="搜索内容", content_type="all", top_k=5)
3. 获取统计: pdf_embedding(action="stats")

📋 参数说明:
- action: 操作类型 (embed/search/stats)
- parser_output_dir: PDF解析器输出目录（embed操作必需）
- query: 搜索查询内容（search操作必需）
- content_type: 内容类型过滤（search操作可选）
  * "text": 仅搜索文本内容
  * "image": 仅搜索图片内容  
  * "all": 搜索文本和图片（默认）
- top_k: 返回结果数量（可选，默认5）
- source_file_filter: 按源文件过滤搜索结果（可选）

🎯 工作流程:
1. 首先使用pdf_parser解析PDF文件
2. 然后使用pdf_embedding(action="embed")对解析结果进行向量化
3. 最后使用search进行统一的语义搜索

💡 统一存储优势:
- 单一集合存储：文本和图片存储在同一个ChromaDB集合中
- 元数据区分：通过content_type字段区分文本和图片
- 统一搜索：一个接口可以搜索文本、图片或全部内容
- 完整元数据：每个embedding都包含完整的溯源信息

🔍 搜索示例:
- 搜索全部: pdf_embedding(action="search", query="建筑设计", content_type="all")
- 仅搜文本: pdf_embedding(action="search", query="项目背景", content_type="text")
- 仅搜图片: pdf_embedding(action="search", query="平面图", content_type="image")
""" 