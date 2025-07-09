#!/usr/bin/env python3
"""
简化版PDF解析器 - 只使用Docling进行PDF解析，不需要LLM API
"""

import argparse
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple
from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc.document import PictureItem, TableItem
import PIL.Image as Image

def parse_pdf_simple(pdf_path: str, output_dir: str = "simple_output") -> Tuple[str, Dict, Dict]:
    """
    简单PDF解析 - 只使用Docling
    
    Args:
        pdf_path: PDF文件路径
        output_dir: 输出目录
        
    Returns:
        Tuple[str, Dict, Dict]: (markdown_content, images, tables)
    """
    print(f"📄 开始解析PDF: {pdf_path}")
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 设置本地模型路径
    models_cache_dir = Path("models_cache")
    if models_cache_dir.exists():
        artifacts_path = str(models_cache_dir.absolute())
        print(f"✅ 使用本地模型: {artifacts_path}")
    else:
        artifacts_path = None
        print("⚠️ 未找到本地模型，将使用在线下载")

    # 配置管道选项
    pipeline_options = PdfPipelineOptions(
        ocr_options=EasyOcrOptions(),
        artifacts_path=artifacts_path,
        do_table_structure=False,  # 暂时禁用表格结构分析
        do_ocr=True,
        generate_page_images=True,
        generate_picture_images=True,
        images_scale=2.0
    )
    
    # 创建文档转换器
    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    
    print("🔄 使用Docling解析PDF...")
    
    # 执行转换
    raw_result = doc_converter.convert(pdf_path)
    
    # 导出原始markdown
    raw_markdown = raw_result.document.export_to_markdown()
    
    # 清理markdown内容
    markdown_clean_pattern = re.compile(r"<!--[\s\S]*?-->")
    clean_markdown = markdown_clean_pattern.sub("", raw_markdown)
    
    print(f"📝 解析完成，文本长度: {len(clean_markdown)} 字符")
    
    # 提取图片和表格
    images, tables = extract_media(raw_result, output_dir)
    
    # 保存结果
    save_results(clean_markdown, images, tables, output_dir, pdf_path)
    
    return clean_markdown, images, tables

def extract_media(raw_result, output_dir: str) -> Tuple[Dict, Dict]:
    """提取图片和表格"""
    images = {}
    tables = {}
    
    print("🖼️ 提取图片和表格...")
    
    # 提取表格
    table_counter = 0
    for element, _level in raw_result.document.iterate_items():
        if isinstance(element, TableItem):
            table_counter += 1
            caption = element.caption_text(raw_result.document)
            
            if len(caption) > 0:
                table_img_path = os.path.join(output_dir, f"table-{table_counter}.png")
                
                try:
                    table_image = element.get_image(raw_result.document)
                    if table_image is not None:
                        with open(table_img_path, "wb") as fp:
                            table_image.save(fp, "PNG")
                        
                        table_img = Image.open(table_img_path)
                        tables[str(table_counter)] = {
                            'caption': caption,
                            'table_path': table_img_path,
                            'width': table_img.width,
                            'height': table_img.height,
                        }
                except Exception as e:
                    print(f"⚠️ 保存表格 {table_counter} 时出错: {e}")
    
    # 提取图片
    picture_counter = 0
    for element, _level in raw_result.document.iterate_items():
        if isinstance(element, PictureItem):
            picture_counter += 1
            caption = element.caption_text(raw_result.document)
            
            if len(caption) > 0:
                image_img_path = os.path.join(output_dir, f"picture-{picture_counter}.png")
                
                try:
                    picture_image = element.get_image(raw_result.document)
                    if picture_image is not None:
                        with open(image_img_path, "wb") as fp:
                            picture_image.save(fp, "PNG")
                        
                        image_img = Image.open(image_img_path)
                        images[str(picture_counter)] = {
                            'caption': caption,
                            'image_path': image_img_path,
                            'width': image_img.width,
                            'height': image_img.height,
                        }
                except Exception as e:
                    print(f"⚠️ 保存图片 {picture_counter} 时出错: {e}")
    
    print(f"📊 提取了 {len(tables)} 个表格和 {len(images)} 个图片")
    return images, tables

def save_results(markdown_content: str, images: Dict, tables: Dict, output_dir: str, pdf_path: str):
    """保存解析结果"""
    
    # 保存原始markdown
    markdown_path = os.path.join(output_dir, "raw_content.md")
    with open(markdown_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    print(f"📄 原始内容已保存到: {markdown_path}")
    
    # 保存图片信息
    images_path = os.path.join(output_dir, "images.json")
    with open(images_path, 'w', encoding='utf-8') as f:
        json.dump(images, f, indent=4, ensure_ascii=False)
    
    # 保存表格信息
    tables_path = os.path.join(output_dir, "tables.json")
    with open(tables_path, 'w', encoding='utf-8') as f:
        json.dump(tables, f, indent=4, ensure_ascii=False)
    
    # 创建结构化内容（简单版本）
    structured_content = create_simple_structure(markdown_content)
    
    # 保存结构化内容
    content_path = os.path.join(output_dir, "structured_content.json")
    with open(content_path, 'w', encoding='utf-8') as f:
        json.dump(structured_content, f, indent=4, ensure_ascii=False)
    print(f"📋 结构化内容已保存到: {content_path}")
    
    # 保存汇总信息
    summary = {
        "source_pdf": pdf_path,
        "total_characters": len(markdown_content),
        "total_images": len(images),
        "total_tables": len(tables),
        "sections_count": len(structured_content.get("sections", [])),
        "processing_method": "Docling Only (No LLM)"
    }
    
    summary_path = os.path.join(output_dir, "summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=4, ensure_ascii=False)
    print(f"📊 汇总信息已保存到: {summary_path}")

def create_simple_structure(markdown_content: str) -> Dict:
    """创建简单的结构化内容（不使用LLM）"""
    
    # 按标题分割内容
    lines = markdown_content.split('\n')
    sections = []
    current_section = {"title": "Document Content", "content": ""}
    
    for line in lines:
        # 检测标题
        if line.startswith('# ') or line.startswith('## ') or line.startswith('### '):
            # 保存当前section
            if current_section["content"].strip():
                sections.append(current_section)
            
            # 开始新section
            title = line.lstrip('#').strip()
            current_section = {"title": title, "content": ""}
        else:
            current_section["content"] += line + "\n"
    
    # 添加最后一个section
    if current_section["content"].strip():
        sections.append(current_section)
    
    # 如果没有找到标题，就把所有内容作为一个section
    if not sections:
        sections = [{"title": "Full Document", "content": markdown_content}]
    
    # 尝试提取元信息
    meta_info = extract_meta_info(markdown_content)
    
    return {
        "meta": meta_info,
        "sections": sections
    }

def extract_meta_info(content: str) -> Dict:
    """简单提取文档元信息"""
    lines = content.split('\n')[:50]  # 只检查前50行
    
    title = ""
    authors = ""
    
    for line in lines:
        line = line.strip()
        if line and not title:
            # 第一个非空行可能是标题
            if not line.startswith('#') and len(line) > 10:
                title = line
        
        # 查找作者信息
        if any(keyword in line.lower() for keyword in ['author', '作者', 'by ']):
            authors = line
            break
    
    return {
        "title": title,
        "authors": authors,
        "extraction_method": "Simple Pattern Matching"
    }

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="简化版PDF解析器（仅使用Docling）")
    parser.add_argument("pdf_path", help="PDF文件路径")
    parser.add_argument("--output_dir", default="simple_output", help="输出目录")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    # 检查PDF文件是否存在
    if not os.path.exists(args.pdf_path):
        print(f"❌ PDF文件不存在: {args.pdf_path}")
        return
    
    try:
        # 执行解析
        markdown_content, images, tables = parse_pdf_simple(args.pdf_path, args.output_dir)
        
        # 输出结果
        print("\n" + "="*50)
        print("✅ 解析完成！")
        print("="*50)
        
        print(f"📊 解析统计:")
        print(f"  - 文本长度: {len(markdown_content):,} 字符")
        print(f"  - 图片数量: {len(images)}")
        print(f"  - 表格数量: {len(tables)}")
        
        print(f"\n📁 输出文件:")
        print(f"  - 原始内容: {args.output_dir}/raw_content.md")
        print(f"  - 结构化内容: {args.output_dir}/structured_content.json")
        print(f"  - 图片信息: {args.output_dir}/images.json")
        print(f"  - 表格信息: {args.output_dir}/tables.json")
        print(f"  - 汇总信息: {args.output_dir}/summary.json")
        
        if args.verbose:
            print(f"\n📖 内容预览 (前500字符):")
            print("-" * 50)
            print(markdown_content[:500])
            print("-" * 50)
        
        print(f"\n✅ 简化解析成功完成！")
        
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        import traceback
        if args.verbose:
            traceback.print_exc()

if __name__ == "__main__":
    main() 