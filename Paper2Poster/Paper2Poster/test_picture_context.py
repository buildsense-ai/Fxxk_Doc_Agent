import os
import sys
from pathlib import Path
from docling.document_converter import DocumentConverter
from docling_core.types.doc.document import PictureItem, TableItem, TextItem

def explore_picture_context(pdf_path: str):
    """探索图片周围的文字内容"""
    print(f"正在分析PDF: {pdf_path}")
    
    # 初始化转换器
    doc_converter = DocumentConverter()
    
    # 转换PDF
    result = doc_converter.convert(pdf_path)
    
    # 获取所有文档元素
    all_elements = []
    for element, level in result.document.iterate_items():
        all_elements.append((element, level))
    
    print(f"文档总共有 {len(all_elements)} 个元素")
    
    # 找到所有图片
    picture_indices = []
    for i, (element, level) in enumerate(all_elements):
        if isinstance(element, PictureItem):
            picture_indices.append(i)
            print(f"\n找到图片 {len(picture_indices)} 在索引 {i}")
            
            # 探索PictureItem的属性
            print(f"图片属性:")
            for attr in dir(element):
                if not attr.startswith('_'):
                    try:
                        value = getattr(element, attr)
                        if callable(value):
                            print(f"  方法: {attr}()")
                        else:
                            print(f"  属性: {attr} = {value}")
                    except Exception as e:
                        print(f"  属性: {attr} = <无法访问: {e}>")
            
            # 查看图片周围的元素
            context_range = 5  # 前后各5个元素
            start_idx = max(0, i - context_range)
            end_idx = min(len(all_elements), i + context_range + 1)
            
            print(f"\n图片周围的元素 (索引 {start_idx} 到 {end_idx-1}):")
            for j in range(start_idx, end_idx):
                elem, lvl = all_elements[j]
                elem_type = type(elem).__name__
                
                if j == i:
                    print(f"  >>> 图片 {j}: {elem_type} (当前图片)")
                else:
                    # 尝试获取文本内容
                    text_content = ""
                    if hasattr(elem, 'text') and elem.text:
                        text_content = elem.text[:100] + "..." if len(elem.text) > 100 else elem.text
                    elif hasattr(elem, 'content') and elem.content:
                        text_content = elem.content[:100] + "..." if len(elem.content) > 100 else elem.content
                    elif isinstance(elem, TextItem):
                        text_content = str(elem)[:100]
                    
                    print(f"      {j}: {elem_type} - {text_content}")
    
    print(f"\n总共找到 {len(picture_indices)} 张图片")

if __name__ == "__main__":
    # 测试用PDF路径
    pdf_path = "aaa.pdf"
    
    if os.path.exists(pdf_path):
        explore_picture_context(pdf_path)
    else:
        print(f"PDF文件不存在: {pdf_path}")
        print("请确认文件路径正确") 