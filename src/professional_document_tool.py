#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专业文档生成工具 - 封装完整的RAG+AI智能文档处理功能
整合用户提供的专业工具代理和模板插入功能

功能特性：
- RAG向量检索集成
- 智能模板插入（保持Word结构）
- AI内容合并（生成新文档）
- 多格式文档支持（DOC/DOCX/PDF/TXT）
- 图像占位符处理
- 专业建筑工程领域优化
"""

import os
import json
import logging
import tempfile
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

# 导入用户提供的核心模块
try:
    import sys
    import os
    # 添加src目录到Python路径，以便导入模块
    src_dir = os.path.dirname(os.path.abspath(__file__))
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    
    from professional_tool_agent_function import run_professional_tool_agent
    from insert_template_function import (
        template_insertion_with_context,
        merge_template_with_context,
        extract_content_from_file
    )
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"⚠️ 专业文档工具依赖模块导入失败: {e}")
    DEPENDENCIES_AVAILABLE = False

try:
    from .tools import Tool
except ImportError:
    from tools import Tool

class ProfessionalDocumentTool(Tool):
    """
    专业文档生成工具
    
    集成功能：
    1. RAG向量检索 - 从专业知识库中检索相关信息
    2. 智能模板插入 - 保持Word模板原始结构进行AI填充
    3. AI内容合并 - 基于模板JSON生成新的专业文档
    4. 多格式支持 - 处理DOC/DOCX/PDF/TXT等格式
    """
    
    def __init__(self):
        super().__init__(
            name="professional_document_tool",
            description="专业文档工具 - 完整的RAG+AI智能文档处理功能"
        )
        self.dependencies_ok = DEPENDENCIES_AVAILABLE
        
        # 确保输出目录存在
        self.output_dir = Path("generated_docs")
        self.output_dir.mkdir(exist_ok=True)
        
        # 获取API密钥
        self.api_key = self._get_api_key()
        
        logging.info(f"🔧 专业文档工具初始化完成，依赖状态: {'✅' if self.dependencies_ok else '❌'}")
    
    def execute(self, **kwargs) -> str:
        """工具执行接口 - 兼容Tool基类"""
        file_path = kwargs.get('file_path', '')
        user_request = kwargs.get('user_request', '')
        context = kwargs.get('context', '')
        template_id = kwargs.get('template_id', 'default')
        processing_mode = kwargs.get('processing_mode', 'auto')
        
        if not file_path or not user_request:
            return "❌ 缺少必需参数: file_path 和 user_request"
        
        result = self.process_document(
            file_path=file_path,
            user_request=user_request,
            context=context,
            template_id=template_id,
            processing_mode=processing_mode
        )
        
        if result['success']:
            return f"✅ 文档处理成功\n输出路径: {result.get('output_path', '未知')}\n详情: {result.get('message', '')}"
        else:
            return f"❌ 文档处理失败: {result.get('message', '未知错误')}"
    
    def _get_api_key(self) -> Optional[str]:
        """获取API密钥"""
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            logging.warning("⚠️ 未找到OPENROUTER_API_KEY环境变量")
        return api_key
    
    def process_document(
        self,
        file_path: str,
        user_request: str,
        context: str = "",
        template_id: str = "default",
        processing_mode: str = "auto"
    ) -> Dict[str, Any]:
        """
        处理文档的主要接口
        
        Args:
            file_path: 输入文档路径
            user_request: 用户请求描述
            context: 上下文信息（可选）
            template_id: 模板标识符
            processing_mode: 处理模式 ("auto"|"template_insertion"|"content_merge")
        
        Returns:
            包含处理结果的字典
        """
        logging.info(f"🚀 开始处理文档: {file_path}")
        
        if not self.dependencies_ok:
            return self._error_result("专业文档工具依赖模块未正确加载")
        
        if not self.api_key:
            return self._error_result("缺少OPENROUTER_API_KEY环境变量")
        
        if not os.path.exists(file_path):
            return self._error_result(f"文件不存在: {file_path}")
        
        try:
            # 智能选择处理模式
            if processing_mode == "auto":
                processing_mode = self._detect_processing_mode(file_path, user_request)
            
            logging.info(f"📋 选择处理模式: {processing_mode}")
            
            if processing_mode == "template_insertion":
                return self._process_template_insertion(file_path, user_request, context)
            elif processing_mode == "content_merge":
                return self._process_content_merge(file_path, user_request, context, template_id)
            elif processing_mode == "professional_agent":
                return self._process_with_professional_agent(file_path, user_request, context, template_id)
            else:
                return self._error_result(f"不支持的处理模式: {processing_mode}")
                
        except Exception as e:
            logging.error(f"❌ 文档处理失败: {e}")
            return self._error_result(f"文档处理异常: {str(e)}")
    
    def _detect_processing_mode(self, file_path: str, user_request: str) -> str:
        """智能检测处理模式"""
        file_ext = Path(file_path).suffix.lower()
        
        # Word模板文件优先使用专业代理（包含RAG）
        if file_ext in ['.doc', '.docx']:
            logging.info("🔍 检测到Word文件，使用专业代理模式（包含RAG检索）")
            return "professional_agent"
        
        # 其他格式使用内容合并
        logging.info("📝 使用内容合并模式")
        return "content_merge"
    
    def _process_with_professional_agent(
        self, 
        file_path: str, 
        user_request: str, 
        context: str, 
        template_id: str
    ) -> Dict[str, Any]:
        """使用专业工具代理处理（完整功能：RAG + 智能选择模式）"""
        logging.info("🧠 使用专业工具代理处理...")
        
        try:
            result = run_professional_tool_agent(
                user_request=user_request,
                context=context,
                template_id=template_id,
                original_file_path=file_path,
                api_key=self.api_key
            )
            
            # 转换结果格式
            return {
                "success": result["status"] in ["success", "partial"],
                "output_path": result.get("output_path"),
                "message": result.get("message", ""),
                "metadata": {
                    "processing_mode": "professional_agent",
                    "template_id": template_id,
                    "status": result["status"],
                    "missing_fields": result.get("missing_fields", []),
                    "agent_metadata": result.get("metadata", {})
                },
                "raw_result": result
            }
            
        except Exception as e:
            logging.error(f"❌ 专业工具代理处理失败: {e}")
            return self._error_result(f"专业工具代理执行失败: {str(e)}")
    
    def _process_template_insertion(
        self, 
        file_path: str, 
        user_request: str, 
        context: str
    ) -> Dict[str, Any]:
        """模板插入处理（保持Word结构）"""
        logging.info("📄 使用模板插入模式...")
        
        try:
            # 构建增强内容
            enhanced_content = f"""
用户请求：{user_request}

上下文信息：
{context}

处理说明：请根据以上信息智能填充Word模板中的空白字段和占位符。
"""
            
            result = template_insertion_with_context(
                template_file_path=file_path,
                original_content=enhanced_content,
                api_key=self.api_key
            )
            
            return {
                "success": result["status"] == "success",
                "output_path": result.get("output_path"),
                "message": result.get("message", "模板插入处理完成"),
                "metadata": {
                    "processing_mode": "template_insertion",
                    "template_file": file_path,
                    "insertion_metadata": result.get("metadata", {})
                },
                "raw_result": result
            }
            
        except Exception as e:
            logging.error(f"❌ 模板插入处理失败: {e}")
            return self._error_result(f"模板插入失败: {str(e)}")
    
    def _process_content_merge(
        self, 
        file_path: str, 
        user_request: str, 
        context: str, 
        template_id: str
    ) -> Dict[str, Any]:
        """内容合并处理（生成新文档）"""
        logging.info("📝 使用内容合并模式...")
        
        try:
            # 1. 提取原始文档内容
            extraction_result = extract_content_from_file(file_path)
            if extraction_result["status"] != "success":
                return self._error_result(f"文档内容提取失败: {extraction_result['message']}")
            
            # 2. 构建模板JSON（基于用户请求）
            template_json = self._build_template_json(user_request, template_id)
            
            # 3. 构建增强内容
            enhanced_content = f"""
用户请求：{user_request}

上下文信息：
{context}

原始文档内容：
{extraction_result['content']}
"""
            
            # 4. 执行内容合并
            result = merge_template_with_context(
                template_json=template_json,
                original_content=enhanced_content,
                api_key=self.api_key
            )
            
            return {
                "success": result["status"] in ["success", "partial"],
                "output_path": result.get("output_path"),
                "message": result.get("message", "内容合并处理完成"),
                "metadata": {
                    "processing_mode": "content_merge",
                    "template_id": template_id,
                    "template_sections": len(template_json),
                    "missing_fields": result.get("missing_fields", []),
                    "merge_metadata": result.get("metadata", {})
                },
                "raw_result": result
            }
            
        except Exception as e:
            logging.error(f"❌ 内容合并处理失败: {e}")
            return self._error_result(f"内容合并失败: {str(e)}")
    
    def _build_template_json(self, user_request: str, template_id: str) -> Dict[str, str]:
        """基于用户请求构建模板JSON"""
        # 基础模板
        templates = {
            "construction_safety": {
                "项目概述": "项目基本信息和安全目标",
                "危险源识别": "施工过程中的主要危险源分析",
                "安全措施": "具体的安全防护措施和要求",
                "应急预案": "安全事故应急处理方案",
                "安全管理": "安全管理制度和责任分工",
                "检查验收": "安全检查和验收标准"
            },
            "construction_organization": {
                "工程概况": "项目基本信息和工程特点",
                "施工部署": "施工组织和人员安排",
                "施工方案": "主要施工方法和技术方案",
                "质量管理": "质量控制措施和验收标准",
                "安全管理": "安全管理措施和应急预案",
                "进度计划": "施工进度安排和里程碑"
            },
            "heritage_building": {
                "项目背景": "古建筑保护项目背景介绍",
                "现状调研": "建筑现状和保护价值评估",
                "保护方案": "文物保护和修缮方案",
                "施工工艺": "传统工艺和现代技术结合",
                "质量控制": "文物保护质量控制要求",
                "验收标准": "古建筑修缮验收标准"
            },
            "default": {
                "项目概述": "项目基本情况介绍",
                "技术方案": "具体技术实施方案",
                "质量管理": "质量控制措施",
                "安全管理": "安全管理要求",
                "进度安排": "项目进度计划",
                "总结建议": "项目总结和建议"
            }
        }
        
        # 根据template_id选择模板
        if template_id in templates:
            return templates[template_id]
        else:
            # 智能匹配：根据用户请求内容推断模板类型
            request_lower = user_request.lower()
            if "安全" in user_request:
                return templates["construction_safety"]
            elif "古建筑" in user_request or "文物" in user_request:
                return templates["heritage_building"]
            elif "施工" in user_request or "组织设计" in user_request:
                return templates["construction_organization"]
            else:
                return templates["default"]
    
    def extract_content(self, file_path: str) -> Dict[str, Any]:
        """提取文档内容的独立接口"""
        if not self.dependencies_ok:
            return self._error_result("专业文档工具依赖模块未正确加载")
        
        try:
            result = extract_content_from_file(file_path)
            return {
                "success": result["status"] == "success",
                "content": result.get("content", ""),
                "message": result.get("message", ""),
                "metadata": result.get("metadata", {})
            }
        except Exception as e:
            return self._error_result(f"内容提取失败: {str(e)}")
    
    def _error_result(self, message: str) -> Dict[str, Any]:
        """生成错误结果"""
        return {
            "success": False,
            "output_path": None,
            "message": message,
            "metadata": {
                "processing_mode": "error",
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取工具状态"""
        return {
            "tool_name": self.name,
            "dependencies_available": self.dependencies_ok,
            "api_key_configured": bool(self.api_key),
            "output_directory": str(self.output_dir),
            "supported_formats": [".doc", ".docx", ".pdf", ".txt"],
            "processing_modes": [
                "professional_agent",  # RAG + 智能选择
                "template_insertion",  # 保持Word结构
                "content_merge"        # 生成新文档
            ]
        } 