#!/usr/bin/env python3
"""
独立解析智能体接口
用于测试Paper2Poster的解析功能
"""

import argparse
import json
import os
import random
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from camel.models import ModelFactory
from camel.agents import ChatAgent
from tenacity import retry, stop_after_attempt
from docling_core.types.doc import ImageRefMode, PictureItem, TableItem
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from jinja2 import Template
import PIL
import torch

# 尝试导入marker（可选）
try:
    from marker.models import create_model_dict
    from utils.src.model_utils import parse_pdf
    MARKER_AVAILABLE = True
except ImportError:
    MARKER_AVAILABLE = False
    print("Warning: Marker not available, will only use Docling for parsing")

# 尝试导入CAMEL工具函数
try:
    from utils.wei_utils import get_agent_config, account_token
    from utils.src.utils import get_json_from_response
    CAMEL_UTILS_AVAILABLE = True
except ImportError:
    CAMEL_UTILS_AVAILABLE = False
    print("Warning: CAMEL utils not available, using simplified token counting")

load_dotenv()

# 配置常量
IMAGE_RESOLUTION_SCALE = 5.0

# 初始化Docling转换器
pipeline_options = PdfPipelineOptions()
pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
pipeline_options.generate_page_images = True
pipeline_options.generate_picture_images = True

doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

class ParserAgent:
    """独立的解析智能体类"""
    
    def __init__(self, model_name: str = "4o"):
        """
        初始化解析智能体
        
        Args:
            model_name: 使用的模型名称，默认为"4o"
        """
        self.model_name = model_name
        self.actor_config = self._get_agent_config(model_name)
        self.actor_model = self._create_model()
        self.actor_agent = self._create_agent()
        
    def _get_agent_config(self, model_name: str) -> Dict:
        """获取智能体配置"""
        if CAMEL_UTILS_AVAILABLE:
            return get_agent_config(model_name)
        else:
            # 简化配置
            return {
                "model_type": "gpt-4o",
                "model_config": {},
                "model_platform": "openai"
            }
    
    def _create_model(self):
        """创建模型实例"""
        try:
            if self.model_name.startswith('vllm_qwen'):
                return ModelFactory.create(
                    model_platform=self.actor_config['model_platform'],
                    model_type=self.actor_config['model_type'],
                    model_config_dict=self.actor_config['model_config'],
                    url=self.actor_config['url'],
                )
            else:
                return ModelFactory.create(
                    model_platform=self.actor_config['model_platform'],
                    model_type=self.actor_config['model_type'],
                    model_config_dict=self.actor_config['model_config'],
                )
        except Exception as e:
            print(f"Error creating model: {e}")
            return None
    
    def _create_agent(self) -> ChatAgent:
        """创建聊天智能体"""
        actor_sys_msg = 'You are the author of the paper, and you will create a poster for the paper.'
        
        return ChatAgent(
            system_message=actor_sys_msg,
            model=self.actor_model,
            message_window_size=10,
            token_limit=self.actor_config.get('token_limit', None)
        )
    
    def _account_token(self, response) -> Tuple[int, int]:
        """计算token使用量"""
        if CAMEL_UTILS_AVAILABLE:
            return account_token(response)
        else:
            # 简化版本，返回估计值
            return len(str(response)), len(str(response))
    
    def _get_json_from_response(self, content: str) -> Dict:
        """从响应中提取JSON"""
        if CAMEL_UTILS_AVAILABLE:
            return get_json_from_response(content)
        else:
            # 简化版本
            try:
                # 尝试直接解析JSON
                return json.loads(content)
            except:
                # 尝试提取JSON代码块
                import re
                json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
                else:
                    # 尝试提取{}包围的内容
                    brace_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if brace_match:
                        return json.loads(brace_match.group(0))
                    else:
                        raise ValueError("Could not extract JSON from response")

    @retry(stop=stop_after_attempt(5))
    def parse_raw(self, pdf_path: str, output_dir: str = "parser_output") -> Tuple[Dict, Dict, Dict]:
        """
        解析PDF文件
        
        Args:
            pdf_path: PDF文件路径
            output_dir: 输出目录
            
        Returns:
            Tuple[Dict, Dict, Dict]: (content_json, images, tables)
        """
        print(f"开始解析PDF: {pdf_path}")
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 第一步：使用Docling解析PDF
        print("使用Docling解析PDF...")
        raw_result = doc_converter.convert(pdf_path)
        raw_markdown = raw_result.document.export_to_markdown()
        
        # 清理markdown内容
        markdown_clean_pattern = re.compile(r"<!--[\s\S]*?-->")
        text_content = markdown_clean_pattern.sub("", raw_markdown)
        
        # 检查解析结果
        if len(text_content) < 500:
            print("Docling解析结果过短，尝试使用Marker...")
            if MARKER_AVAILABLE:
                parser_model = create_model_dict(device='cuda', dtype=torch.float16)
                text_content, rendered = parse_pdf(pdf_path, model_lst=parser_model, save_file=False)
            else:
                print("Warning: Marker不可用，继续使用Docling结果")
        
        print(f"解析得到文本长度: {len(text_content)} 字符")
        
        # 第二步：使用LLM重新组织内容
        print("使用LLM重新组织内容...")
        content_json = self._reorganize_content_with_llm(text_content)
        
        # 第三步：提取图片和表格
        print("提取图片和表格...")
        images, tables = self._extract_images_and_tables(raw_result, output_dir)
        
        # 保存结果
        self._save_results(content_json, images, tables, output_dir)
        
        return content_json, images, tables
    
    def _reorganize_content_with_llm(self, text_content: str) -> Dict:
        """使用LLM重新组织内容"""
        # 加载提示模板
        template_content = self._get_prompt_template()
        template = Template(template_content)
        
        # 生成提示
        prompt = template.render(markdown_document=text_content)
        
        # 调用LLM
        while True:
            self.actor_agent.reset()
            response = self.actor_agent.step(prompt)
            input_token, output_token = self._account_token(response)
            
            print(f"LLM调用完成 - 输入tokens: {input_token}, 输出tokens: {output_token}")
            
            try:
                content_json = self._get_json_from_response(response.msgs[0].content)
                
                if len(content_json) > 0:
                    # 验证和优化结果
                    content_json = self._validate_and_optimize_content(content_json)
                    return content_json
                else:
                    print("LLM返回空结果，重试...")
                    
            except Exception as e:
                print(f"解析LLM响应失败: {e}")
                print("重试...")
                
                # 如果内容太长，截断重试
                if self.model_name.startswith('vllm_qwen'):
                    text_content = text_content[:80000]
                    prompt = template.render(markdown_document=text_content)
    
    def _get_prompt_template(self) -> str:
        """获取提示模板"""
        return """You are a document content divider and extractor specialist, expert in dividing and extracting content from various types of documents and reorganizing it into a two-level json format for later poster generation.

Based on given markdown document, generate a JSON output for later poster generation, make sure the output is concise and focused.

Step-by-Step Instructions:
1. Identify Sections and Subsections in document and identify sections and subsections based on the heading levels and logical structure.

2. Divide Content: Reorganize the content into sections and subsections, ensuring that each subsection contains approximately 500 words.

3. Refine Titles: Create titles for each section with at most 3 words.

4. Remove Unwanted Elements: Eliminate any unwanted elements such as headers, footers, text surrounded by `~~` indicating deletion.

5. Refine Text: For content, you should keep as much raw text as possible. Do not include citations.

6. Length: you should control the length of each section, according to their importance according to your understanding of the paper. For important sections, their content should be long.

7. Make sure there is a poster title section at the beginning, and it should contain information like paper title, author, organization etc.

8. The "meta" key contains the meta information of the poster, where the title should be the raw title of the paper and is not summarized.

9. There **must** be a section for the poster title.

Example Output:
{
    "meta": {
        "poster_title": "raw title of the paper",
        "authors": "authors of the paper",
        "affiliations": "affiliations of the authors"
    },
    "sections": [
        {
            "title": "Poster Title & Author",
            "content": "content of poster title and author"
        },
        {
            "title": "title of section1",
            "content": "content of section 1"
        },
        {
            "title": "title of section2",
            "content": "content of section 2"
        }
    ]
}

Give your output in JSON format
Input:
{{ markdown_document }}
Output:"""
    
    def _validate_and_optimize_content(self, content_json: Dict) -> Dict:
        """验证和优化内容"""
        # 检查必要字段
        if 'sections' not in content_json:
            raise ValueError("Missing 'sections' field in response")
        
        # 验证每个section的格式
        has_title = False
        for section in content_json['sections']:
            if not isinstance(section, dict) or 'title' not in section or 'content' not in section:
                raise ValueError("Invalid section format")
            if 'title' in section['title'].lower():
                has_title = True
        
        if not has_title:
            raise ValueError("Missing title section")
        
        # 如果section过多，进行智能选择
        if len(content_json['sections']) > 9:
            print(f"Section数量过多({len(content_json['sections'])}个)，进行智能选择...")
            selected_sections = (
                content_json['sections'][:2] + 
                random.sample(content_json['sections'][2:-2], 5) + 
                content_json['sections'][-2:]
            )
            content_json['sections'] = selected_sections
            print(f"选择后剩余{len(content_json['sections'])}个sections")
        
        return content_json
    
    def _extract_images_and_tables(self, raw_result, output_dir: str) -> Tuple[Dict, Dict]:
        """提取图片和表格"""
        images = {}
        tables = {}
        
        # 提取表格
        table_counter = 0
        for element, _level in raw_result.document.iterate_items():
            if isinstance(element, TableItem):
                table_counter += 1
                caption = element.caption_text(raw_result.document)
                
                if len(caption) > 0:
                    table_img_path = os.path.join(output_dir, f"table-{table_counter}.png")
                    
                    # 保存表格图片
                    with open(table_img_path, "wb") as fp:
                        element.get_image(raw_result.document).save(fp, "PNG")
                    
                    # 获取图片信息
                    table_img = PIL.Image.open(table_img_path)
                    tables[str(table_counter)] = {
                        'caption': caption,
                        'table_path': table_img_path,
                        'width': table_img.width,
                        'height': table_img.height,
                        'figure_size': table_img.width * table_img.height,
                        'figure_aspect': table_img.width / table_img.height,
                    }
        
        # 提取图片
        picture_counter = 0
        for element, _level in raw_result.document.iterate_items():
            if isinstance(element, PictureItem):
                picture_counter += 1
                caption = element.caption_text(raw_result.document)
                
                if len(caption) > 0:
                    image_img_path = os.path.join(output_dir, f"picture-{picture_counter}.png")
                    
                    # 保存图片
                    with open(image_img_path, "wb") as fp:
                        element.get_image(raw_result.document).save(fp, "PNG")
                    
                    # 获取图片信息
                    image_img = PIL.Image.open(image_img_path)
                    images[str(picture_counter)] = {
                        'caption': caption,
                        'image_path': image_img_path,
                        'width': image_img.width,
                        'height': image_img.height,
                        'figure_size': image_img.width * image_img.height,
                        'figure_aspect': image_img.width / image_img.height,
                    }
        
        print(f"提取了 {len(tables)} 个表格和 {len(images)} 个图片")
        return images, tables
    
    def _save_results(self, content_json: Dict, images: Dict, tables: Dict, output_dir: str):
        """保存解析结果"""
        # 保存结构化内容
        content_path = os.path.join(output_dir, "parsed_content.json")
        with open(content_path, 'w', encoding='utf-8') as f:
            json.dump(content_json, f, indent=4, ensure_ascii=False)
        print(f"结构化内容已保存到: {content_path}")
        
        # 保存图片信息
        images_path = os.path.join(output_dir, "images.json")
        with open(images_path, 'w', encoding='utf-8') as f:
            json.dump(images, f, indent=4, ensure_ascii=False)
        print(f"图片信息已保存到: {images_path}")
        
        # 保存表格信息
        tables_path = os.path.join(output_dir, "tables.json")
        with open(tables_path, 'w', encoding='utf-8') as f:
            json.dump(tables, f, indent=4, ensure_ascii=False)
        print(f"表格信息已保存到: {tables_path}")
        
        # 保存汇总信息
        summary = {
            "total_sections": len(content_json.get("sections", [])),
            "total_images": len(images),
            "total_tables": len(tables),
            "meta_info": content_json.get("meta", {}),
            "section_titles": [section.get("title", "") for section in content_json.get("sections", [])]
        }
        
        summary_path = os.path.join(output_dir, "summary.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=4, ensure_ascii=False)
        print(f"汇总信息已保存到: {summary_path}")
    
    def get_parsing_stats(self, content_json: Dict, images: Dict, tables: Dict) -> Dict:
        """获取解析统计信息"""
        total_text_length = sum(len(section.get("content", "")) for section in content_json.get("sections", []))
        
        stats = {
            "sections_count": len(content_json.get("sections", [])),
            "total_text_length": total_text_length,
            "avg_section_length": total_text_length / max(len(content_json.get("sections", [])), 1),
            "images_count": len(images),
            "tables_count": len(tables),
            "total_figures": len(images) + len(tables),
            "has_meta": "meta" in content_json,
            "has_title_section": any("title" in section.get("title", "").lower() for section in content_json.get("sections", []))
        }
        
        return stats


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="独立解析智能体测试接口")
    parser.add_argument("pdf_path", help="PDF文件路径")
    parser.add_argument("--output_dir", default="parser_output", help="输出目录")
    parser.add_argument("--model", default="4o", help="使用的模型名称")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    # 检查PDF文件是否存在
    if not os.path.exists(args.pdf_path):
        print(f"错误: PDF文件不存在: {args.pdf_path}")
        return
    
    try:
        # 创建解析智能体
        print(f"初始化解析智能体，使用模型: {args.model}")
        parser_agent = ParserAgent(model_name=args.model)
        
        # 执行解析
        content_json, images, tables = parser_agent.parse_raw(args.pdf_path, args.output_dir)
        
        # 获取统计信息
        stats = parser_agent.get_parsing_stats(content_json, images, tables)
        
        # 输出结果
        print("\n" + "="*50)
        print("解析完成！")
        print("="*50)
        
        print(f"📄 解析统计:")
        print(f"  - Sections数量: {stats['sections_count']}")
        print(f"  - 总文本长度: {stats['total_text_length']:,} 字符")
        print(f"  - 平均section长度: {stats['avg_section_length']:.0f} 字符")
        print(f"  - 图片数量: {stats['images_count']}")
        print(f"  - 表格数量: {stats['tables_count']}")
        print(f"  - 总图表数量: {stats['total_figures']}")
        
        print(f"\n📁 输出文件:")
        print(f"  - 结构化内容: {args.output_dir}/parsed_content.json")
        print(f"  - 图片信息: {args.output_dir}/images.json")
        print(f"  - 表格信息: {args.output_dir}/tables.json")
        print(f"  - 汇总信息: {args.output_dir}/summary.json")
        
        if args.verbose:
            print(f"\n📋 Section标题:")
            for i, title in enumerate(stats['section_titles'], 1):
                print(f"  {i}. {title}")
            
            if content_json.get("meta"):
                print(f"\n📝 论文信息:")
                meta = content_json["meta"]
                print(f"  - 标题: {meta.get('poster_title', 'N/A')}")
                print(f"  - 作者: {meta.get('authors', 'N/A')}")
                print(f"  - 机构: {meta.get('affiliations', 'N/A')}")
        
        print(f"\n✅ 解析成功完成！")
        
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        import traceback
        if args.verbose:
            traceback.print_exc()


if __name__ == "__main__":
    main() 