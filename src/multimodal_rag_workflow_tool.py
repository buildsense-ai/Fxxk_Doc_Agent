#!/usr/bin/env python3
"""
多模态RAG工作流工具
整合PDF解析、文本embedding、图片RAG处理的完整流程
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# 导入现有工具
from src.pdf_parser_tool import PDFParserTool
from src.rag_tool_chroma import RAGTool
from src.image_rag_tool import ImageRAGTool
from src.base_tool import Tool

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultimodalRAGWorkflowTool(Tool):
    """多模态RAG工作流工具 - 完整的PDF处理到知识库构建流程"""
    
    def __init__(self):
        super().__init__(
            name="multimodal_rag_workflow",
            description="🔄 多模态RAG工作流 - 完整的PDF解析→文本embedding→图片RAG处理流程。支持批量处理，自动构建知识库。"
        )
        
        # 初始化各个工具组件
        self.pdf_parser = PDFParserTool()
        self.rag_tool = RAGTool()
        self.image_rag_tool = ImageRAGTool()
        
        # 工作流状态跟踪
        self.workflow_stats = {
            "processed_pdfs": 0,
            "extracted_texts": 0,
            "processed_images": 0,
            "total_errors": 0
        }
        
        logger.info("✅ 多模态RAG工作流工具初始化完成")
    
    def execute(self, **kwargs) -> str:
        """
        执行多模态RAG工作流
        
        Args:
            action: 操作类型 (process_pdf/batch_process/get_stats)
            pdf_path: PDF文件路径 (单个处理时)
            pdf_directory: PDF目录路径 (批量处理时)
            include_images: 是否处理图片 (默认True)
            auto_description: 是否自动生成图片描述 (默认True)
        """
        action = kwargs.get("action", "process_pdf")
        
        if action == "process_pdf":
            return self._process_single_pdf(**kwargs)
        elif action == "batch_process":
            return self._batch_process_pdfs(**kwargs)
        elif action == "get_stats":
            return self._get_workflow_stats()
        elif action == "clear_knowledge_base":
            return self._clear_knowledge_base()
        else:
            return json.dumps({
                "status": "error",
                "message": f"不支持的操作: {action}",
                "supported_actions": ["process_pdf", "batch_process", "get_stats", "clear_knowledge_base"]
            }, indent=2, ensure_ascii=False)
    
    def _process_single_pdf(self, **kwargs) -> str:
        """处理单个PDF文件的完整流程"""
        pdf_path = kwargs.get("pdf_path")
        include_images = kwargs.get("include_images", True)
        auto_description = kwargs.get("auto_description", True)
        
        if not pdf_path:
            return json.dumps({
                "status": "error",
                "message": "请提供PDF文件路径 (pdf_path参数)"
            }, indent=2, ensure_ascii=False)
        
        if not os.path.exists(pdf_path):
            return json.dumps({
                "status": "error",
                "message": f"PDF文件不存在: {pdf_path}"
            }, indent=2, ensure_ascii=False)
        
        workflow_result = {
            "status": "success",
            "pdf_path": pdf_path,
            "timestamp": datetime.now().isoformat(),
            "steps": []
        }
        
        try:
            # 步骤1: PDF解析
            logger.info(f"🔄 开始处理PDF: {pdf_path}")
            parse_result = self._parse_pdf_step(pdf_path)
            workflow_result["steps"].append(parse_result)
            
            if parse_result["status"] != "success":
                workflow_result["status"] = "partial_failure"
                return json.dumps(workflow_result, indent=2, ensure_ascii=False)
            
            # 步骤2: 文本embedding处理
            if parse_result.get("content_file"):
                embedding_result = self._process_text_embedding_step(parse_result)
                workflow_result["steps"].append(embedding_result)
            
            # 步骤3: 图片RAG处理
            if include_images and parse_result.get("images_info"):
                image_result = self._process_images_step(
                    parse_result, 
                    auto_description=auto_description
                )
                workflow_result["steps"].append(image_result)
            
            # 更新统计信息
            self.workflow_stats["processed_pdfs"] += 1
            
            workflow_result["summary"] = {
                "total_steps": len(workflow_result["steps"]),
                "successful_steps": sum(1 for step in workflow_result["steps"] if step["status"] == "success"),
                "output_directory": parse_result.get("output_directory")
            }
            
            logger.info(f"✅ PDF处理完成: {pdf_path}")
            return json.dumps(workflow_result, indent=2, ensure_ascii=False)
            
        except Exception as e:
            self.workflow_stats["total_errors"] += 1
            workflow_result["status"] = "error"
            workflow_result["error"] = str(e)
            logger.error(f"❌ PDF处理失败: {e}")
            return json.dumps(workflow_result, indent=2, ensure_ascii=False)
    
    def _parse_pdf_step(self, pdf_path: str) -> Dict[str, Any]:
        """步骤1: PDF解析"""
        step_result = {
            "step": "pdf_parsing",
            "status": "processing",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # 调用PDF解析工具
            parse_result_str = self.pdf_parser.execute(
                pdf_path=pdf_path,
                action="parse"
            )
            
            parse_result = json.loads(parse_result_str)
            
            if parse_result.get("status") == "success":
                step_result.update({
                    "status": "success",
                    "output_directory": parse_result.get("output_directory"),
                    "content_file": parse_result.get("content_file"),
                    "images_file": parse_result.get("images_file"),
                    "statistics": parse_result.get("statistics"),
                    "message": "PDF解析成功"
                })
                
                # 加载图片信息
                if parse_result.get("images_file") and os.path.exists(parse_result["images_file"]):
                    with open(parse_result["images_file"], 'r', encoding='utf-8') as f:
                        step_result["images_info"] = json.load(f)
                
            else:
                step_result.update({
                    "status": "error",
                    "message": parse_result.get("message", "PDF解析失败")
                })
            
            return step_result
            
        except Exception as e:
            step_result.update({
                "status": "error",
                "message": f"PDF解析异常: {str(e)}"
            })
            return step_result
    
    def _process_text_embedding_step(self, parse_result: Dict[str, Any]) -> Dict[str, Any]:
        """步骤2: 文本embedding处理"""
        step_result = {
            "step": "text_embedding",
            "status": "processing",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            content_file = parse_result.get("content_file")
            if not content_file or not os.path.exists(content_file):
                step_result.update({
                    "status": "skipped",
                    "message": "内容文件不存在，跳过文本embedding"
                })
                return step_result
            
            # 读取解析后的内容
            with open(content_file, 'r', encoding='utf-8') as f:
                content_data = json.load(f)
            
            # 提取文本内容
            text_content = self._extract_text_from_parsed_content(content_data)
            
            if not text_content.strip():
                step_result.update({
                    "status": "skipped",
                    "message": "文本内容为空，跳过embedding处理"
                })
                return step_result
            
            # 创建临时文本文件用于RAG处理
            temp_txt_path = content_file.replace('.json', '_text.txt')
            with open(temp_txt_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            # 调用RAG工具进行embedding
            rag_result_str = self.rag_tool.execute(
                action="upload",
                file_path=temp_txt_path,
                filename=f"parsed_{os.path.basename(parse_result.get('pdf_path', 'unknown'))}"
            )
            
            # 清理临时文件
            if os.path.exists(temp_txt_path):
                os.remove(temp_txt_path)
            
            step_result["status"] = "success"
            step_result["message"] = "文本embedding处理完成"
            step_result["rag_result"] = rag_result_str[:200] + "..." if len(rag_result_str) > 200 else rag_result_str
            step_result["text_length"] = str(len(text_content))
            
            self.workflow_stats["extracted_texts"] += 1
            return step_result
            
        except Exception as e:
            step_result.update({
                "status": "error",
                "message": f"文本embedding处理失败: {str(e)}"
            })
            return step_result
    
    def _process_images_step(self, parse_result: Dict[str, Any], auto_description: bool = True) -> Dict[str, Any]:
        """步骤3: 图片RAG处理"""
        step_result = {
            "step": "image_rag_processing",
            "status": "processing",
            "timestamp": datetime.now().isoformat(),
            "processed_images": 0,
            "failed_images": 0
        }
        
        try:
            images_info = parse_result.get("images_info", {})
            output_directory = parse_result.get("output_directory")
            
            if not images_info or not output_directory:
                step_result.update({
                    "status": "skipped",
                    "message": "没有找到图片信息或输出目录"
                })
                return step_result
            
            processed_count = 0
            failed_count = 0
            
            # 处理每张图片
            for image_id, image_data in images_info.items():
                try:
                    # 构建图片文件路径
                    image_filename = image_data.get("filename", f"{image_id}.png")
                    image_path = os.path.join(output_directory, image_filename)
                    
                    if not os.path.exists(image_path):
                        logger.warning(f"图片文件不存在: {image_path}")
                        failed_count += 1
                        continue
                    
                    # 生成图片描述
                    if auto_description:
                        description = self._generate_image_description(image_data, image_path)
                    else:
                        description = image_data.get("description", f"来自PDF的图片: {image_filename}")
                    
                    # 上传到图片RAG系统
                    upload_result = self.image_rag_tool.execute(
                        action="upload",
                        image_path=image_path,
                        description=description
                    )
                    
                    if "✅" in upload_result:
                        processed_count += 1
                        logger.info(f"✅ 图片上传成功: {image_filename}")
                    else:
                        failed_count += 1
                        logger.warning(f"⚠️ 图片上传失败: {image_filename}")
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"❌ 图片处理异常: {e}")
            
            step_result.update({
                "status": "success" if processed_count > 0 else "partial_failure",
                "message": f"图片RAG处理完成: {processed_count}张成功, {failed_count}张失败",
                "processed_images": processed_count,
                "failed_images": failed_count
            })
            
            self.workflow_stats["processed_images"] += processed_count
            return step_result
            
        except Exception as e:
            step_result.update({
                "status": "error",
                "message": f"图片RAG处理失败: {str(e)}"
            })
            return step_result
    
    def _extract_text_from_parsed_content(self, content_data: Dict) -> str:
        """从解析后的内容中提取文本"""
        text_parts = []
        
        # 如果有chapters结构
        if "chapters" in content_data:
            for chapter in content_data["chapters"]:
                if "title" in chapter:
                    text_parts.append(f"# {chapter['title']}")
                if "content" in chapter:
                    text_parts.append(chapter["content"])
                if "key_points" in chapter:
                    for point in chapter["key_points"]:
                        text_parts.append(f"- {point}")
        
        # 如果有sections结构
        elif "sections" in content_data:
            for section in content_data["sections"]:
                if "title" in section:
                    text_parts.append(f"## {section['title']}")
                if "content" in section:
                    text_parts.append(section["content"])
        
        # 如果直接有content字段
        elif "content" in content_data:
            text_parts.append(content_data["content"])
        
        # 如果有其他文本字段
        else:
            for key, value in content_data.items():
                if isinstance(value, str) and len(value) > 10:
                    text_parts.append(f"{key}: {value}")
        
        return "\n\n".join(text_parts)
    
    def _generate_image_description(self, image_data: Dict, image_path: str) -> str:
        """生成图片描述"""
        # 优先使用已有描述
        if "description" in image_data and image_data["description"]:
            return image_data["description"]
        
        # 根据图片文件名和位置信息生成描述
        filename = os.path.basename(image_path)
        description_parts = [f"来自PDF文档的图片: {filename}"]
        
        # 添加位置信息
        if "page" in image_data:
            description_parts.append(f"位于第{image_data['page']}页")
        
        if "bbox" in image_data:
            description_parts.append("包含图形或图表内容")
        
        # 添加尺寸信息
        if "width" in image_data and "height" in image_data:
            description_parts.append(f"尺寸: {image_data['width']}x{image_data['height']}")
        
        return ", ".join(description_parts)
    
    def _batch_process_pdfs(self, **kwargs) -> str:
        """批量处理PDF文件"""
        pdf_directory = kwargs.get("pdf_directory")
        include_images = kwargs.get("include_images", True)
        
        if not pdf_directory:
            return json.dumps({
                "status": "error",
                "message": "请提供PDF目录路径 (pdf_directory参数)"
            }, indent=2, ensure_ascii=False)
        
        if not os.path.exists(pdf_directory):
            return json.dumps({
                "status": "error",
                "message": f"目录不存在: {pdf_directory}"
            }, indent=2, ensure_ascii=False)
        
        # 查找所有PDF文件
        pdf_files = []
        for root, dirs, files in os.walk(pdf_directory):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
        
        if not pdf_files:
            return json.dumps({
                "status": "warning",
                "message": f"在目录 {pdf_directory} 中未找到PDF文件"
            }, indent=2, ensure_ascii=False)
        
        batch_result = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "total_files": len(pdf_files),
            "processed_files": 0,
            "failed_files": 0,
            "results": []
        }
        
        # 处理每个PDF文件
        for pdf_path in pdf_files:
            try:
                logger.info(f"📄 批量处理: {pdf_path}")
                result_str = self._process_single_pdf(
                    pdf_path=pdf_path,
                    include_images=include_images
                )
                result = json.loads(result_str)
                
                if result.get("status") == "success":
                    batch_result["processed_files"] += 1
                else:
                    batch_result["failed_files"] += 1
                
                batch_result["results"].append({
                    "pdf_path": pdf_path,
                    "status": result.get("status"),
                    "summary": result.get("summary")
                })
                
            except Exception as e:
                batch_result["failed_files"] += 1
                batch_result["results"].append({
                    "pdf_path": pdf_path,
                    "status": "error",
                    "error": str(e)
                })
                logger.error(f"❌ 批量处理失败: {pdf_path} - {e}")
        
        return json.dumps(batch_result, indent=2, ensure_ascii=False)
    
    def _get_workflow_stats(self) -> str:
        """获取工作流统计信息"""
        return json.dumps({
            "status": "success",
            "workflow_statistics": self.workflow_stats,
            "timestamp": datetime.now().isoformat()
        }, indent=2, ensure_ascii=False)
    
    def _clear_knowledge_base(self) -> str:
        """清空知识库"""
        try:
            # 清空文本RAG
            rag_result = self.rag_tool.execute(action="clear")
            
            # 重置统计信息
            self.workflow_stats = {
                "processed_pdfs": 0,
                "extracted_texts": 0,
                "processed_images": 0,
                "total_errors": 0
            }
            
            return json.dumps({
                "status": "success",
                "message": "知识库已清空",
                "details": rag_result
            }, indent=2, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"清空知识库失败: {str(e)}"
            }, indent=2, ensure_ascii=False)
    
    def get_usage_guide(self) -> str:
        """获取使用指南"""
        return """
🔄 多模态RAG工作流工具使用指南

🚀 核心功能：
1. PDF解析 → 文本embedding → 图片RAG处理的完整流程
2. 支持单个文件和批量处理
3. 自动构建多模态知识库

📋 基本用法：
1. 处理单个PDF:
   multimodal_rag_workflow(action="process_pdf", pdf_path="path/to/file.pdf")

2. 批量处理PDF目录:
   multimodal_rag_workflow(action="batch_process", pdf_directory="path/to/pdfs/")

3. 获取统计信息:
   multimodal_rag_workflow(action="get_stats")

4. 清空知识库:
   multimodal_rag_workflow(action="clear_knowledge_base")

🔧 参数说明：
- pdf_path: PDF文件路径
- pdf_directory: PDF目录路径（批量处理）
- include_images: 是否处理图片（默认True）
- auto_description: 是否自动生成图片描述（默认True）

📊 处理流程：
1. 📄 PDF解析（文本、图片、表格）
2. 🧠 文本内容embedding到向量数据库
3. 🖼️ 图片上传到图片RAG系统
4. 📈 统计和结果报告

💡 使用建议：
- 确保PDF文件质量良好
- 批量处理时建议分批进行
- 定期查看统计信息
- 可与长文档生成工具配合使用

⚡ 工作流优势：
✅ 一键完成多模态知识库构建
✅ 自动处理文本和图片RAG
✅ 详细的处理状态跟踪
✅ 支持大批量PDF处理
✅ 为长文档生成提供知识支持
        """


# 工具实例化和导出
if __name__ == "__main__":
    tool = MultimodalRAGWorkflowTool()
    print(tool.get_usage_guide()) 