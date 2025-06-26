"""
Tools for ReAct Agent - 核心三工具架构
专注于文档处理的三个核心工具
"""
import os
import json
from typing import Dict, Any, List, Optional

# 核心三工具架构

class Tool:
    """工具基类"""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def execute(self, **kwargs) -> str:
        """执行工具，子类需要实现这个方法"""
        raise NotImplementedError

class ToolRegistry:
    """工具注册表 - 核心四工具"""
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._register_core_tools()
    
    def _register_core_tools(self):
        """注册核心工具"""
        core_tools = []
        
        # 1. RAG工具 - 文档embedding处理和智能搜索
        try:
            from .rag_tool_chroma import RAGTool
            rag_tool = RAGTool()
            core_tools.append(rag_tool)
            print("✅ RAG工具加载成功")
        except ImportError as e:
            print(f"❌ RAG工具加载失败: {e}")
        
        # 2. 专业文档工具 - 完整的RAG+AI智能文档处理功能
        try:
            from .professional_document_tool import ProfessionalDocumentTool
            professional_tool = ProfessionalDocumentTool()
            core_tools.append(professional_tool)
            print("✅ 专业文档工具加载成功")
        except ImportError as e:
            print(f"❌ 专业文档工具加载失败: {e}")
        
        # 注册所有工具
        for tool in core_tools:
            self.register_tool(tool)
        
        print(f"🎯 核心工具架构初始化完成，共加载 {len(core_tools)} 个工具")
    
    def register_tool(self, tool: Tool):
        """注册工具"""
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """获取工具"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict[str, str]]:
        """列出所有工具"""
        return [
            {"name": tool.name, "description": tool.description}
            for tool in self.tools.values()
        ]
    
    def execute_tool(self, name: str, **kwargs) -> str:
        """执行工具"""
        tool = self.get_tool(name)
        if tool:
            return tool.execute(**kwargs)
        else:
            return f"❌ 未找到工具: {name}"
    
    def get_tool_summary(self) -> str:
        """获取工具摘要"""
        summary = "🔧 核心三工具架构:\n\n"
        
        tool_descriptions = {
            "rag_tool": "📚 RAG工具 - 文档embedding处理、智能搜索",
            "professional_document_tool": "🎯 专业文档工具 - 完整的RAG+AI智能文档处理功能",
            "advanced_long_document_generator": "🚀 高级长文档生成工具 - 专业长篇文档智能生成器"
        }
        
        for tool_name, description in tool_descriptions.items():
            if tool_name in self.tools:
                summary += f"✅ {description}\n"
            else:
                summary += f"❌ {description} (未加载)\n"
        
        summary += f"\n📊 总计: {len(self.tools)} 个工具已加载"
        return summary


    
    def register_advanced_long_document_tool(self):
        """注册高级长文档生成工具"""
        try:
            from .advanced_long_document_generator_tool import AdvancedLongDocumentGeneratorTool
            advanced_tool = AdvancedLongDocumentGeneratorTool()
            self.tools[advanced_tool.name] = advanced_tool
            print("✅ 高级长文档生成工具加载成功")
        except ImportError as e:
            print(f"❌ 高级长文档生成工具加载失败: {e}")

def create_core_tool_registry(deepseek_client=None) -> ToolRegistry:
    """创建核心工具注册表"""
    registry = ToolRegistry()
    
    # 如果提供了deepseek_client，为RAG工具设置AI客户端
    if deepseek_client:
        rag_tool = registry.get_tool("rag_tool")
        if rag_tool and hasattr(rag_tool, 'field_processor'):
            field_processor = getattr(rag_tool, 'field_processor')
            if hasattr(field_processor, 'deepseek_client'):
                field_processor.deepseek_client = deepseek_client
                print("🤖 RAG工具已配置AI客户端")
    
    # 注册高级长文档生成工具（不需要deepseek_client参数）
    registry.register_advanced_long_document_tool()
    
    return registry

# 工具使用指南
TOOL_USAGE_GUIDE = """
🎯 ReactAgent核心工具使用流程:

1️⃣ RAG工具 (rag_tool):
   - 上传资料文档: action="upload", file_path="document.pdf"
   - 智能搜索: action="search", query="搜索内容"
   - 字段填充: action="fill_fields", template_fields_json={"字段名": "字段要求"}

2️⃣ 模板转换工具 (template_conversion):
   - DOC转换: template_path="template.doc"
   - 结构分析: template_path="template.docx", output_json_path="structure.json"
   - 占位符提取: 自动识别并转换占位符为标准格式

3️⃣ 模板填充工具 (template_inserter):
   - AI智能填充: json_template_path="template.json", content_data={...}
   - 支持字典、JSON文件或JSON字符串作为内容数据
   - 自动处理图片附件和复杂模板结构

3️⃣ 专业文档工具 (professional_document_tool):
   - 智能文档处理: file_path="文档路径", user_request="用户需求"
   - RAG检索模式: processing_mode="professional_agent"
   - 模板插入模式: processing_mode="template_insertion"
   - 内容合并模式: processing_mode="content_merge"

🔄 推荐工作流程:

📋 模板文档处理流程:
资料文档 → RAG工具(embedding) → 旧模板(DOC) → 模板转换工具(转换+分析) → 
模板填充工具(AI智能填充) → 填充好的docx文档

🎯 专业文档处理流程:
用户需求 → 专业文档工具(智能处理) → RAG检索相关信息 → 模板智能填充 → 
多模式处理选择 → AI智能合并 → 专业级文档输出

💡 核心优势:
- 支持旧版DOC格式模板处理
- 智能占位符识别和转换
- AI智能内容映射和填充
- RAG向量检索和知识管理
- 多模式智能处理选择
- 极简的文档处理工作流
- 高质量文档输出和结构化数据
- 一站式文档解决方案

🎯 适用场景:
- 施工组织设计等模板文档填充
- 专业技术文档智能生成
- 项目方案、分析报告撰写
- 知识库文档管理和检索
- 文档模板标准化处理
"""

from .rag_tool_chroma import RAGTool
from .professional_document_tool import ProfessionalDocumentTool

def register_tools(agent):
    """注册所有工具到ReAct Agent"""
    tools = [
        {
            "name": "rag_tool",
            "description": """📚 RAG文档处理工具 - 专业知识库embedding和检索系统

核心功能：
- 文档embedding向量化（支持DOC/DOCX/PDF/TXT等格式）
- 基于Chroma向量数据库的语义检索  
- 多模态内容提取和索引
- 智能文档相似度搜索

适用场景：当需要对大量文档进行知识管理、语义搜索或构建专业知识库时使用""",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["add_document", "search", "list_documents", "delete_document"],
                        "description": "操作类型：add_document(添加文档), search(搜索), list_documents(列出文档), delete_document(删除文档)"
                    },
                    "file_path": {
                        "type": "string", 
                        "description": "文档文件路径（add_document和delete_document时需要）"
                    },
                    "query": {
                        "type": "string",
                        "description": "搜索查询语句（search时需要）"
                    },
                    "top_k": {
                        "type": "integer",
                        "default": 5,
                        "description": "返回结果数量（search时可选，默认5）"
                    }
                },
                "required": ["operation"]
            },
            "function": lambda **kwargs: RAGTool().execute(**kwargs)
        },


        {
            "name": "professional_document_tool",
            "description": """🎯 专业文档工具 - 完整的RAG+AI智能文档处理功能

这是一个集成化的专业文档处理工具，整合了用户提供的完整专业工具代理和模板插入功能。

核心特性：
- 🔍 RAG向量检索：从专业知识库中检索相关信息
- 📄 智能模板插入：保持Word模板原始结构进行AI填充
- 🧠 AI内容合并：基于模板JSON生成新的专业文档
- 📋 多格式支持：处理DOC/DOCX/PDF/TXT等格式
- 🖼️ 图像占位符处理：支持图片引用和附件管理
- 🏗️ 建筑工程领域优化：专业术语和规范

智能处理模式：
- professional_agent：RAG检索 + 智能选择模式（推荐）
- template_insertion：保持Word结构的模板填充
- content_merge：基于JSON模板生成新文档

适用场景：需要专业性强、格式规范的工程技术文档生成""",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "输入文档文件路径"
                    },
                    "user_request": {
                        "type": "string", 
                        "description": "用户需求描述"
                    },
                    "context": {
                        "type": "string",
                        "description": "项目背景或上下文信息",
                        "default": ""
                    },
                    "template_id": {
                        "type": "string",
                        "enum": ["construction_safety", "construction_organization", "heritage_building", "default"],
                        "default": "default",
                        "description": "模板标识符"
                    },
                    "processing_mode": {
                        "type": "string",
                        "enum": ["auto", "professional_agent", "template_insertion", "content_merge"],
                        "default": "auto", 
                        "description": "处理模式：auto(智能选择), professional_agent(RAG+智能), template_insertion(模板插入), content_merge(内容合并)"
                    }
                },
                "required": ["file_path", "user_request"]
            },
            "function": lambda **kwargs: ProfessionalDocumentTool().process_document(**kwargs)
        }
    ]
    
    for tool in tools:
        agent.register_tool(
            name=tool["name"],
            description=tool["description"], 
            parameters=tool["parameters"],
            function=tool["function"]
        )
    
    print("✅ 已注册2个核心工具：")
    print("   📚 rag_tool - RAG文档处理工具")
    print("   🎯 professional_document_tool - 专业文档工具（完整版）") 