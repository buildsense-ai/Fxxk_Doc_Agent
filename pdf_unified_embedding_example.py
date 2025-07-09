#!/usr/bin/env python3
"""
统一PDF Embedding系统使用示例
展示如何使用统一的embedding系统处理PDF解析结果
"""

import os
import json
from src.pdf_embedding_service import PDFEmbeddingService
from src.pdf_embedding_tool import PDFEmbeddingTool

def main():
    """统一PDF embedding系统完整示例"""
    
    print("🚀 统一PDF Embedding系统演示")
    print("=" * 50)
    
    # 1. 直接使用服务类
    print("\n📊 1. 使用PDFEmbeddingService")
    print("-" * 30)
    
    # 初始化服务
    service = PDFEmbeddingService()
    
    # 示例解析器输出目录
    parser_output_dir = "parser_output/20250708_165249_zu74gk"
    
    if os.path.exists(parser_output_dir):
        # 执行embedding
        print(f"📁 处理目录: {parser_output_dir}")
        
        parsed_content_path = os.path.join(parser_output_dir, "parsed_content.json")
        images_json_path = os.path.join(parser_output_dir, "images.json")
        
        stats = service.embed_parsed_pdf(
            parsed_content_path=parsed_content_path,
            images_json_path=images_json_path,
            parser_output_dir=parser_output_dir
        )
        
        print(f"✅ Embedding完成: {stats}")
        
        # 统一搜索演示
        print("\n🔍 2. 统一搜索演示")
        print("-" * 30)
        
        # 搜索所有内容
        print("🔍 搜索全部内容:")
        all_results = service.search("建筑设计", content_type=None, top_k=3)
        print(f"   找到 {len(all_results)} 个结果")
        for i, result in enumerate(all_results):
            print(f"   {i+1}. [{result['content_type']}] {result['content'][:50]}...")
        
        # 仅搜索文本
        print("\n🔍 仅搜索文本内容:")
        text_results = service.search("项目背景", content_type="text", top_k=3)
        print(f"   找到 {len(text_results)} 个文本结果")
        for i, result in enumerate(text_results):
            print(f"   {i+1}. {result['content'][:50]}...")
        
        # 仅搜索图片
        print("\n🔍 仅搜索图片内容:")
        image_results = service.search("平面图", content_type="image", top_k=3)
        print(f"   找到 {len(image_results)} 个图片结果")
        for i, result in enumerate(image_results):
            print(f"   {i+1}. {result['metadata']['caption']} - {result['content'][:50]}...")
        
        # 获取统计信息
        print("\n📈 3. 统计信息")
        print("-" * 30)
        stats = service.get_collection_stats()
        print(f"📊 总embedding数量: {stats['total_embeddings']}")
        print(f"📝 文本embedding: {stats['text_embeddings']}")
        print(f"🖼️ 图片embedding: {stats['image_embeddings']}")
        print(f"📦 集合名称: {stats['collection_name']}")
        
    else:
        print(f"❌ 目录不存在: {parser_output_dir}")
    
    # 2. 使用工具类
    print("\n🔧 4. 使用PDFEmbeddingTool")
    print("-" * 30)
    
    tool = PDFEmbeddingTool()
    
    # 工具embedding
    if os.path.exists(parser_output_dir):
        print("📊 执行embedding:")
        result = tool.execute(
            action="embed",
            parser_output_dir=parser_output_dir
        )
        print(f"   结果: {json.loads(result)['message']}")
    
    # 工具搜索
    print("\n🔍 执行搜索:")
    search_result = tool.execute(
        action="search",
        query="建筑设计",
        content_type="all",
        top_k=3
    )
    search_data = json.loads(search_result)
    print(f"   {search_data['message']}")
    print(f"   总结果: {search_data['total_results']}")
    print(f"   文本结果: {search_data['text_results']}")
    print(f"   图片结果: {search_data['image_results']}")
    
    # 工具统计
    print("\n📈 获取统计:")
    stats_result = tool.execute(action="stats")
    stats_data = json.loads(stats_result)
    print(f"   {stats_data['message']}")
    print(f"   统计: {stats_data['statistics']}")
    
    print("\n✅ 演示完成！")
    print("\n💡 统一存储优势:")
    print("   - 单一集合存储文本和图片")
    print("   - 通过content_type元数据区分")
    print("   - 统一搜索接口，支持类型过滤")
    print("   - 完整的元数据追踪")

def show_usage_examples():
    """显示使用示例"""
    print("\n📚 使用示例:")
    print("=" * 50)
    
    print("\n1. 基本embedding:")
    print("   service.embed_parsed_pdf(parsed_content_path, images_json_path, parser_output_dir)")
    
    print("\n2. 统一搜索:")
    print("   # 搜索全部内容")
    print("   service.search('建筑设计', content_type=None)")
    print("   ")
    print("   # 仅搜索文本")
    print("   service.search('项目背景', content_type='text')")
    print("   ")
    print("   # 仅搜索图片")
    print("   service.search('平面图', content_type='image')")
    
    print("\n3. 工具调用:")
    print("   # Embedding")
    print("   tool.execute(action='embed', parser_output_dir='...')")
    print("   ")
    print("   # 搜索")
    print("   tool.execute(action='search', query='...', content_type='all')")
    print("   ")
    print("   # 统计")
    print("   tool.execute(action='stats')")

if __name__ == "__main__":
    try:
        main()
        show_usage_examples()
    except Exception as e:
        print(f"❌ 运行出错: {e}")
        import traceback
        traceback.print_exc() 