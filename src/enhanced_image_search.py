#!/usr/bin/env python3
"""
改进的图片搜索展示功能
解决重复图片名称和展示问题
"""
import json
import os
from typing import List, Dict, Any
from urllib.parse import urlparse

class EnhancedImageSearchResult:
    """增强的图片搜索结果处理"""
    
    def __init__(self, rag_tool):
        self.rag_tool = rag_tool
        
    def search_images_with_enhanced_display(self, query: str, top_k: int = 5) -> str:
        """
        搜索图片并提供增强的展示
        
        Args:
            query: 搜索关键词
            top_k: 返回结果数量
            
        Returns:
            str: 格式化的搜索结果
        """
        # 执行原始搜索
        search_result = self.rag_tool.execute(
            action="search_images",
            query=query,
            top_k=top_k
        )
        
        # 解析搜索结果
        result_data = json.loads(search_result)
        
        if result_data.get("status") != "success":
            return f"❌ 搜索失败: {result_data.get('message', 'unknown error')}"
        
        results = result_data.get("results", [])
        
        if not results:
            return f"📭 未找到与'{query}'相关的图片"
        
        # 处理和去重结果
        enhanced_results = self._process_and_deduplicate_results(results)
        
        # 生成增强的展示文本
        return self._generate_enhanced_display(query, enhanced_results)
    
    def _process_and_deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        处理和去重搜索结果
        
        Args:
            results: 原始搜索结果
            
        Returns:
            List[Dict[str, Any]]: 处理后的结果
        """
        enhanced_results = []
        seen_images = set()  # 用于去重
        
        for i, result in enumerate(results):
            metadata = result.get("metadata", {})
            
            # 创建唯一标识符
            unique_id = f"{metadata.get('source_file', 'unknown')}_{metadata.get('image_id', 'unknown')}"
            
            # 跳过重复图片
            if unique_id in seen_images:
                continue
            seen_images.add(unique_id)
            
            # 生成增强的图片标题
            enhanced_title = self._generate_enhanced_title(metadata, i + 1)
            
            # 生成增强的描述
            enhanced_description = self._generate_enhanced_description(result)
            
            # 构建增强结果
            enhanced_result = {
                "index": len(enhanced_results) + 1,
                "enhanced_title": enhanced_title,
                "enhanced_description": enhanced_description,
                "minio_url": metadata.get("minio_url", ""),
                "original_result": result,
                "distance": result.get("distance", 0.0),
                "similarity": 1 / (1 + result.get("distance", 0.0))
            }
            
            enhanced_results.append(enhanced_result)
        
        return enhanced_results
    
    def _generate_enhanced_title(self, metadata: Dict[str, Any], index: int) -> str:
        """
        生成增强的图片标题
        
        Args:
            metadata: 图片元数据
            index: 图片序号
            
        Returns:
            str: 增强的标题
        """
        # 获取基本信息
        original_caption = metadata.get("original_caption", "")
        caption = metadata.get("caption", "")
        source_file = metadata.get("source_file", "unknown")
        image_id = metadata.get("image_id", "unknown")
        
        # 提取文件名中的关键信息
        file_name = os.path.basename(source_file)
        file_info = self._extract_file_info(file_name)
        
        # 优先使用有意义的标题
        if original_caption and original_caption != "unknown" and not original_caption.startswith("图片"):
            title = original_caption
        elif caption and not caption.startswith("图片"):
            title = caption
        else:
            # 生成基于文件信息的标题
            title = f"{file_info}第{image_id}张图片"
        
        return title
    
    def _extract_file_info(self, filename: str) -> str:
        """
        从文件名中提取有意义的信息
        
        Args:
            filename: 文件名
            
        Returns:
            str: 提取的信息
        """
        # 去掉时间戳和扩展名
        name = os.path.splitext(filename)[0]
        
        # 提取关键词
        if "刘氏宗祠" in name:
            return "刘氏宗祠"
        elif "古庙" in name:
            return "古庙"
        elif "设计方案" in name:
            return "设计方案"
        elif "修缮" in name:
            return "修缮方案"
        else:
            return "文档"
    
    def _generate_enhanced_description(self, result: Dict[str, Any]) -> str:
        """
        生成增强的图片描述
        
        Args:
            result: 搜索结果
            
        Returns:
            str: 增强的描述
        """
        metadata = result.get("metadata", {})
        
        # 获取VLM描述
        vlm_description = metadata.get("vlm_description", "")
        context = metadata.get("context", "")
        
        # 构建描述
        description_parts = []
        
        if vlm_description and not vlm_description.startswith("图片标题:"):
            # 如果有详细的VLM描述，使用它
            description_parts.append(vlm_description)
        elif context:
            # 如果有上下文，使用上下文
            description_parts.append(f"上下文: {context}")
        
        # 添加基本信息
        width = metadata.get("width", 0)
        height = metadata.get("height", 0)
        if width and height:
            description_parts.append(f"图片尺寸: {width}x{height}")
        
        # 添加相似度信息
        distance = result.get("distance", 0.0)
        similarity = 1 / (1 + distance)
        description_parts.append(f"相关性: {similarity:.2%}")
        
        return " | ".join(description_parts) if description_parts else "无详细描述"
    
    def _generate_enhanced_display(self, query: str, results: List[Dict[str, Any]]) -> str:
        """
        生成增强的展示文本
        
        Args:
            query: 搜索关键词
            results: 处理后的结果
            
        Returns:
            str: 格式化的展示文本
        """
        if not results:
            return f"📭 未找到与'{query}'相关的图片"
        
        # 生成标题
        display_text = f"🔍 已为您检索到以下{len(results)}张{query}相关图片：\n\n"
        
        # 生成每个图片的展示
        for result in results:
            index = result["index"]
            title = result["enhanced_title"]
            description = result["enhanced_description"]
            minio_url = result["minio_url"]
            
            display_text += f"{index}. [{title}]({minio_url})\n"
            display_text += f"   - {description}\n\n"
        
        # 添加推荐信息
        if len(results) > 1:
            # 找到相关性最高的图片
            best_result = max(results, key=lambda x: x["similarity"])
            display_text += f"💡 特别推荐第{best_result['index']}张图片，相关性最高（{best_result['similarity']:.2%}）\n"
        
        return display_text

# 使用示例
def demo_enhanced_search():
    """演示增强搜索功能"""
    import sys
    sys.path.append('src')
    from rag_tool_chroma import RAGTool
    
    # 初始化工具
    rag_tool = RAGTool()
    enhanced_search = EnhancedImageSearchResult(rag_tool)
    
    # 搜索刘氏宗祠图片
    result = enhanced_search.search_images_with_enhanced_display("刘氏宗祠", top_k=5)
    
    print("🎯 增强搜索结果:")
    print("=" * 60)
    print(result)

if __name__ == "__main__":
    demo_enhanced_search() 