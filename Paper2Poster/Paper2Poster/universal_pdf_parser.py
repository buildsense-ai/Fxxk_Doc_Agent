#!/usr/bin/env python3
"""
通用PDF解析器 - 支持多种文档类型
包括学术论文、技术报告、商业文档、说明书等
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from enum import Enum

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parser_agent_openrouter import OpenRouterParserAgent

class DocumentType(Enum):
    """文档类型枚举"""
    ACADEMIC_PAPER = "academic_paper"
    TECHNICAL_REPORT = "technical_report"
    BUSINESS_DOCUMENT = "business_document"
    MANUAL = "manual"
    NEWS_ARTICLE = "news_article"
    BOOK_CHAPTER = "book_chapter"
    GENERAL = "general"

class UniversalPDFParser(OpenRouterParserAgent):
    """通用PDF解析器，支持多种文档类型"""
    
    def __init__(self, model_name: str = "gpt-4o", document_type: DocumentType = DocumentType.GENERAL):
        """
        初始化通用解析器
        
        Args:
            model_name: 使用的模型名称
            document_type: 文档类型
        """
        self.document_type = document_type
        super().__init__(model_name)
    
    def _get_prompt_template(self) -> str:
        """根据文档类型获取相应的提示模板"""
        
        base_instructions = """You are a document content divider and extractor specialist, expert in dividing and extracting content from various types of documents and reorganizing it into a structured JSON format.

Based on the given markdown document, generate a JSON output that captures the key information and structure of the document.

Step-by-Step Instructions:
1. Identify the main sections and logical structure of the document
2. Divide content into meaningful sections with approximately 300-800 words each
3. Create concise titles for each section (2-4 words)
4. Remove unwanted elements like headers, footers, page numbers, and irrelevant annotations
5. Preserve important formatting and structure information
6. Extract relevant metadata based on document type

"""
        
        # 根据文档类型定制指令和格式
        if self.document_type == DocumentType.ACADEMIC_PAPER:
            specific_instructions = """
7. Focus on: Abstract, Introduction, Methodology, Results, Conclusion
8. Extract: title, authors, affiliations, keywords
9. Maintain academic structure and terminology

Example Output:
{
    "meta": {
        "title": "Document title",
        "authors": "Author names",
        "affiliations": "Institution information",
        "document_type": "academic_paper"
    },
    "sections": [
        {"title": "Abstract", "content": "..."},
        {"title": "Introduction", "content": "..."}
    ]
}"""
            
        elif self.document_type == DocumentType.TECHNICAL_REPORT:
            specific_instructions = """
7. Focus on: Executive Summary, Technical Details, Implementation, Recommendations
8. Extract: title, organization, report date, version
9. Emphasize technical specifications and procedures

Example Output:
{
    "meta": {
        "title": "Report title",
        "organization": "Publishing organization",
        "date": "Publication date",
        "document_type": "technical_report"
    },
    "sections": [
        {"title": "Executive Summary", "content": "..."},
        {"title": "Technical Details", "content": "..."}
    ]
}"""
            
        elif self.document_type == DocumentType.BUSINESS_DOCUMENT:
            specific_instructions = """
7. Focus on: Executive Summary, Business Objectives, Analysis, Recommendations
8. Extract: title, company, department, date
9. Highlight business metrics and strategic information

Example Output:
{
    "meta": {
        "title": "Document title",
        "company": "Company name",
        "department": "Department/Division",
        "document_type": "business_document"
    },
    "sections": [
        {"title": "Executive Summary", "content": "..."},
        {"title": "Business Analysis", "content": "..."}
    ]
}"""
            
        elif self.document_type == DocumentType.MANUAL:
            specific_instructions = """
7. Focus on: Overview, Setup/Installation, Usage Instructions, Troubleshooting
8. Extract: title, product/service name, version, publisher
9. Maintain step-by-step procedures and safety information

Example Output:
{
    "meta": {
        "title": "Manual title",
        "product": "Product/Service name",
        "version": "Version information",
        "document_type": "manual"
    },
    "sections": [
        {"title": "Overview", "content": "..."},
        {"title": "Setup Guide", "content": "..."}
    ]
}"""
            
        elif self.document_type == DocumentType.NEWS_ARTICLE:
            specific_instructions = """
7. Focus on: Headline, Lead, Body paragraphs, Conclusion
8. Extract: title, author, publication, date
9. Maintain journalistic structure and key facts

Example Output:
{
    "meta": {
        "title": "Article headline",
        "author": "Journalist name",
        "publication": "News outlet",
        "document_type": "news_article"
    },
    "sections": [
        {"title": "Lead Story", "content": "..."},
        {"title": "Details", "content": "..."}
    ]
}"""
            
        elif self.document_type == DocumentType.BOOK_CHAPTER:
            specific_instructions = """
7. Focus on: Chapter introduction, main concepts, examples, summary
8. Extract: chapter title, book title, author, chapter number
9. Preserve narrative flow and conceptual structure

Example Output:
{
    "meta": {
        "title": "Chapter title",
        "book_title": "Book title",
        "author": "Author name",
        "document_type": "book_chapter"
    },
    "sections": [
        {"title": "Introduction", "content": "..."},
        {"title": "Main Concepts", "content": "..."}
    ]
}"""
            
        else:  # GENERAL
            specific_instructions = """
7. Adapt to the document's natural structure and purpose
8. Extract: title and any relevant metadata available
9. Create logical sections based on content flow

Example Output:
{
    "meta": {
        "title": "Document title",
        "document_type": "general",
        "subject": "Main topic/theme"
    },
    "sections": [
        {"title": "Introduction", "content": "..."},
        {"title": "Main Content", "content": "..."}
    ]
}"""
        
        return base_instructions + specific_instructions + "\n\nGive your output in JSON format\nInput:\n{{ markdown_document }}\nOutput:"
    
    def _validate_and_optimize_content(self, content_json: Dict) -> Dict:
        """验证和优化内容 - 通用版本"""
        # 检查必要字段
        if 'sections' not in content_json:
            raise ValueError("Missing 'sections' field in response")
        
        # 验证每个section的格式
        for section in content_json['sections']:
            if not isinstance(section, dict) or 'title' not in section or 'content' not in section:
                raise ValueError("Invalid section format")
        
        # 确保有meta信息
        if 'meta' not in content_json:
            content_json['meta'] = {"document_type": self.document_type.value}
        else:
            content_json['meta']['document_type'] = self.document_type.value
        
        # 如果section过多，进行智能选择
        if len(content_json['sections']) > 12:
            print(f"Section数量过多({len(content_json['sections'])}个)，进行智能选择...")
            # 保留开头2个，中间随机选择8个，结尾2个
            import random
            selected_sections = (
                content_json['sections'][:2] + 
                random.sample(content_json['sections'][2:-2], min(8, len(content_json['sections'])-4)) + 
                content_json['sections'][-2:]
            )
            content_json['sections'] = selected_sections
            print(f"选择后剩余{len(content_json['sections'])}个sections")
        
        return content_json

def auto_detect_document_type(pdf_path: str) -> DocumentType:
    """自动检测文档类型（简单启发式方法）"""
    filename = os.path.basename(pdf_path).lower()
    
    # 基于文件名的启发式判断
    if any(keyword in filename for keyword in ['paper', 'journal', 'conference', 'arxiv']):
        return DocumentType.ACADEMIC_PAPER
    elif any(keyword in filename for keyword in ['report', 'technical', 'spec', 'specification']):
        return DocumentType.TECHNICAL_REPORT
    elif any(keyword in filename for keyword in ['business', 'proposal', 'plan', 'strategy']):
        return DocumentType.BUSINESS_DOCUMENT
    elif any(keyword in filename for keyword in ['manual', 'guide', 'instruction', 'handbook']):
        return DocumentType.MANUAL
    elif any(keyword in filename for keyword in ['news', 'article', 'press']):
        return DocumentType.NEWS_ARTICLE
    elif any(keyword in filename for keyword in ['chapter', 'book']):
        return DocumentType.BOOK_CHAPTER
    else:
        return DocumentType.GENERAL

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="通用PDF解析器 - 支持多种文档类型")
    parser.add_argument("pdf_path", help="PDF文件路径")
    parser.add_argument("--output_dir", default="universal_output", help="输出目录")
    parser.add_argument("--model", default="gpt-4o-mini", help="使用的模型名称")
    parser.add_argument("--doc_type", 
                        choices=[dt.value for dt in DocumentType],
                        help="文档类型 (如果不指定则自动检测)")
    parser.add_argument("--auto_detect", action="store_true", help="自动检测文档类型")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    # 检查PDF文件是否存在
    if not os.path.exists(args.pdf_path):
        print(f"错误: PDF文件不存在: {args.pdf_path}")
        return
    
    # 确定文档类型
    if args.doc_type:
        doc_type = DocumentType(args.doc_type)
        print(f"📋 使用指定文档类型: {doc_type.value}")
    elif args.auto_detect:
        doc_type = auto_detect_document_type(args.pdf_path)
        print(f"🔍 自动检测文档类型: {doc_type.value}")
    else:
        doc_type = DocumentType.GENERAL
        print(f"📄 使用通用文档类型: {doc_type.value}")
    
    # 检查环境变量
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ 未设置OPENAI_API_KEY环境变量")
        return
    
    try:
        # 创建通用解析器
        print(f"初始化通用解析器，使用模型: {args.model}")
        universal_parser = UniversalPDFParser(model_name=args.model, document_type=doc_type)
        
        # 执行解析
        content_json, images, tables = universal_parser.parse_raw(args.pdf_path, args.output_dir)
        
        # 获取统计信息
        stats = universal_parser.get_parsing_stats(content_json, images, tables)
        
        # 输出结果
        print("\n" + "="*50)
        print("解析完成！")
        print("="*50)
        
        print(f"📄 解析统计:")
        print(f"  - 文档类型: {doc_type.value}")
        print(f"  - 使用模型: {stats['model_used']}")
        print(f"  - Sections数量: {stats['sections_count']}")
        print(f"  - 总文本长度: {stats['total_text_length']:,} 字符")
        print(f"  - 平均section长度: {stats['avg_section_length']:.0f} 字符")
        print(f"  - 图片数量: {stats['images_count']}")
        print(f"  - 表格数量: {stats['tables_count']}")
        
        print(f"\n📁 输出文件:")
        print(f"  - 结构化内容: {args.output_dir}/parsed_content.json")
        print(f"  - 图片信息: {args.output_dir}/images.json")
        print(f"  - 表格信息: {args.output_dir}/tables.json")
        print(f"  - 汇总信息: {args.output_dir}/summary.json")
        
        if args.verbose and content_json.get("meta"):
            print(f"\n📝 文档信息:")
            meta = content_json["meta"]
            for key, value in meta.items():
                if value:
                    print(f"  - {key}: {value}")
        
        print(f"\n✅ 解析成功完成！")
        
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        import traceback
        if args.verbose:
            traceback.print_exc()

if __name__ == "__main__":
    main() 