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
        
        # 3. 模板分类工具 - 智能判断文档类型并分类处理
        try:
            from .template_classifier_tool import TemplateClassifierTool
            template_classifier = TemplateClassifierTool()
            core_tools.append(template_classifier)
            print("✅ 模板分类工具加载成功")
        except ImportError as e:
            print(f"❌ 模板分类工具加载失败: {e}")
        
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
        summary = "🔧 系统三大核心功能架构:\n\n"
        
        tool_descriptions = {
            "template_classifier": "📤 功能1: 文件上传智能分类 - 自动判断模板/资料文档并分类处理",
            "advanced_long_document_generator": "📄 功能2: 长文档生成 - 专业长篇文档智能生成器", 
            "professional_document_tool": "📋 功能3: 模板文档生成 - 基于模板和RAG的智能填充",
            "rag_tool": "📚 辅助工具: RAG检索 - 文档embedding处理、智能搜索"
        }
        
        for tool_name, description in tool_descriptions.items():
            if tool_name in self.tools:
                summary += f"✅ {description}\n"
            else:
                summary += f"❌ {description} (未加载)\n"
        
        summary += f"\n📊 总计: {len(self.tools)} 个工具已加载"
        summary += "\n\n🎯 三大核心功能："
        summary += "\n1. 📤 文件上传 → 智能分类 → 模板保存/RAG处理"
        summary += "\n2. 📄 长文档生成 → 创作指令 → 大纲生成 → DOCX输出"
        summary += "\n3. 📋 模板生成 → 找模板文件 → RAG检索 → 智能填充"
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

# 系统三大核心功能使用指南
SYSTEM_FUNCTIONS_GUIDE = """
🎯 ReactAgent系统三大核心功能使用流程:

**功能1: 📤 文件上传智能分类处理**
工具: template_classifier
- 参数: file_path="上传文件路径", action="classify"
- 功能: 自动判断文档类型（模板文档 vs 资料文档）
- 处理逻辑: 
  * 模板文档 → 保存到templates_storage文件夹，保留原始文件名
  * 资料文档 → 自动调用RAG工具进行embedding处理
- 适用场景: 用户刚上传文档，需要智能分类处理

**功能2: 📄 长文档生成**
工具: advanced_long_document_generator
- 参数: action="generate", request="生成需求描述", chathistory="可选对话历史"
- 功能: AI驱动的专业长篇文档智能生成
- 处理逻辑: 
  * 创作指令分析 → 智能大纲生成 → 逐章节内容生成 → 专业DOCX输出
- 适用场景: 生成技术方案、研究报告、项目计划等长篇文档

**功能3: 📋 模板文档生成**
工具: professional_document_tool
- 参数: file_path="模板文件路径", user_request="用户需求", processing_mode="auto"
- 功能: 基于模板和RAG的智能文档填充
- 处理逻辑: 
  * 从templates_storage找到用户描述的模板文件
  * 结合用户关键词进行RAG检索相关资料
  * 将检索资料智能插入到模板对应位置
- 适用场景: 各种记录表、申请表单、审批表格的智能填充

**辅助功能: 📚 RAG检索**
工具: rag_tool
- 参数: operation="search/add_document/list_documents", query="搜索内容", file_path="文档路径"
- 功能: 文档embedding处理和智能搜索
- 适用场景: 简单问答、文档搜索、知识管理

🔄 三大核心功能工作流程:

📤 **功能1工作流程：文件上传**
用户上传文档 → template_classifier智能分类 → 
模板文档保存到templates_storage / 资料文档RAG处理

📄 **功能2工作流程：长文档生成**
用户需求分析 → advanced_long_document_generator → 
创作指令 → 大纲生成 → 章节内容 → DOCX文档输出

📋 **功能3工作流程：模板文档生成**
用户需求 → professional_document_tool → 
找到模板文件 → RAG检索资料 → 智能填充插入 → 填充完成的文档

💡 系统优势:
- 🧠 智能文档类型识别和自动分类
- 🚀 专业长文档多阶段智能生成
- 📋 基于模板+RAG的智能填充系统
- 🔍 强大的向量搜索和知识管理
- 🏗️ 专为工程技术文档优化
- 📄 支持多种格式输入输出
- ⚡ 一站式文档处理解决方案

🎯 典型应用场景:
- 📤 文档管理：智能分类存储，自动知识库构建
- 📄 技术写作：施工方案、技术报告、项目计划
- 📋 表单填写：现场记录、审批申请、检测报告
- 🔍 知识检索：技术资料查询、规范标准搜索
"""

from .rag_tool_chroma import RAGTool
from .professional_document_tool import ProfessionalDocumentTool
from .template_classifier_tool import TemplateClassifierTool

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
            "name": "template_classifier",
            "description": """📋 模板分类工具 - 智能判断文档类型并分类处理

核心功能：
- 🔍 智能文档类型识别：自动分析文档内容，判断是模板文档还是资料文档
- 📋 模板文档处理：保留原始文件名，保存到templates_storage文件夹
- 📚 资料文档处理：自动调用RAG工具进行embedding处理
- 🧠 特征分析：基于空白字段、表单关键词、文档结构等多维度判断

智能识别特征：
- 模板特征：空白字段(____、【】)、表单关键词(记录、申请、审批)、模板标题
- 资料特征：内容关键词(方案、技术、分析)、文档结构(章节、条目)、长文档内容

适用场景：文档上传时的智能分类处理，自动区分模板和资料文档""",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "上传文档的文件路径"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["classify"],
                        "default": "classify",
                        "description": "操作类型：classify(分类处理文档)"
                    }
                },
                "required": ["file_path"]
            },
            "function": lambda **kwargs: TemplateClassifierTool().execute(**kwargs)
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
    
    print("✅ 已注册3个核心工具：")
    print("   📚 rag_tool - RAG文档处理工具")
    print("   🎯 professional_document_tool - 专业文档工具（完整版）")
    print("   📋 template_classifier - 模板分类工具") 