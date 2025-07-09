#!/usr/bin/env python3
"""
测试Docling是否能正常工作
"""

import os
from pathlib import Path
from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption

def test_docling():
    """测试Docling配置"""
    print("🔧 测试Docling配置...")
    
    # 设置本地模型路径
    models_cache_dir = Path("models_cache")
    if models_cache_dir.exists():
        artifacts_path = str(models_cache_dir.absolute())
        print(f"✅ 找到本地模型路径: {artifacts_path}")
    else:
        artifacts_path = None
        print("⚠️  未找到本地模型路径，将使用在线下载")

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
    
    print(f"📋 管道选项配置完成")
    
    # 创建文档转换器
    try:
        doc_converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        print("✅ 文档转换器创建成功")
        
        # 测试PDF文件
        pdf_path = "设计方案.pdf"
        if not os.path.exists(pdf_path):
            print(f"❌ 找不到PDF文件: {pdf_path}")
            return
            
        print(f"📄 开始转换PDF: {pdf_path}")
        
        # 执行转换
        result = doc_converter.convert(pdf_path)
        
        print(f"✅ PDF转换成功!")
        print(f"📊 页数: {len(result.document.pages)}")
        
        # 导出markdown
        markdown_content = result.document.export_to_markdown()
        print(f"📝 Markdown长度: {len(markdown_content)} 字符")
        
        # 保存结果
        output_file = "test_output.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"💾 结果已保存到: {output_file}")
        
        # 显示前500个字符
        print(f"\n📖 内容预览:")
        print("=" * 50)
        print(markdown_content[:500])
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_docling() 