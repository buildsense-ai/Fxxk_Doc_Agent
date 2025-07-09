"""
Tools for ReAct Agent - 核心五工具架构
专注于文档处理和图片RAG的五个核心工具
"""
import os
import json
from typing import Dict, Any, List, Optional

# 核心五工具架构

class Tool:
    """工具基类"""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def execute(self, **kwargs) -> str:
        """执行工具，子类需要实现这个方法"""
        raise NotImplementedError

class ToolRegistry:
    """工具注册表 - 核心五工具"""
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._register_core_tools()
    
    def _register_core_tools(self):
        """注册核心工具"""
        core_tools = []
        
        # 1. RAG工具 - 文档embedding处理和智能搜索 (暂时注释以测试PDF解析)
        # if RAGTool:
        #     try:
        #         rag_tool = RAGTool()
        #         core_tools.append(rag_tool)
        #         print("✅ RAG工具加载成功")
        #     except Exception as e:
        #         print(f"❌ RAG工具加载失败: {e}")
        # else:
        #     print("❌ RAG工具类不可用")
        print("⚠️ RAG工具已暂时注释，专注测试PDF解析")
        
        # 2. 专业文档工具 - 完整的RAG+AI智能文档处理功能 (暂时注释以测试PDF解析)
        # if ProfessionalDocumentTool:
        #     try:
        #         professional_tool = ProfessionalDocumentTool()
        #         core_tools.append(professional_tool)
        #         print("✅ 专业文档工具加载成功")
        #     except Exception as e:
        #         print(f"❌ 专业文档工具加载失败: {e}")
        # else:
        #     print("❌ 专业文档工具类不可用")
        print("⚠️ 专业文档工具已暂时注释，专注测试PDF解析")
        
        # 3. 模板分类工具 - 智能判断文档类型并分类处理 (暂时注释以测试PDF解析)
        # if TemplateClassifierTool:
        #     try:
        #         template_classifier = TemplateClassifierTool()
        #         core_tools.append(template_classifier)
        #         print("✅ 模板分类工具加载成功")
        #     except Exception as e:
        #         print(f"❌ 模板分类工具加载失败: {e}")
        # else:
        #     print("❌ 模板分类工具类不可用")
        print("⚠️ 模板分类工具已暂时注释，专注测试PDF解析")
        
        # 4. 图片RAG工具 - 图片上传和基于文本描述的图片检索 (暂时注释以测试PDF解析)
        # try:
        #     from image_rag_tool import ImageRAGTool
        # except ImportError:
        #     try:
        #         from .image_rag_tool import ImageRAGTool
        #     except ImportError:
        #         ImageRAGTool = None
        # 
        # if ImageRAGTool:
        #     try:
        #         image_rag_tool = ImageRAGTool()
        #         core_tools.append(image_rag_tool)
        #         print("✅ 图片RAG工具加载成功")
        #     except Exception as e:
        #         print(f"❌ 图片RAG工具加载失败: {e}")
        # else:
        #     print("❌ 图片RAG工具类不可用")
        print("⚠️ 图片RAG工具已暂时注释，专注测试PDF解析")
        
        # 5. 带图片的长文档生成工具 - 生成包含图片的专业长文档 (暂时注释以测试PDF解析)
        # try:
        #     from image_document_generator_tool import ImageDocumentGeneratorTool
        # except ImportError:
        #     try:
        #         from .image_document_generator_tool import ImageDocumentGeneratorTool
        #     except ImportError:
        #         ImageDocumentGeneratorTool = None
        # 
        # if ImageDocumentGeneratorTool:
        #     try:
        #         image_doc_tool = ImageDocumentGeneratorTool()
        #         core_tools.append(image_doc_tool)
        #         print("✅ 带图片的长文档生成工具加载成功")
        #     except Exception as e:
        #         print(f"❌ 带图片的长文档生成工具加载失败: {e}")
        # else:
        #     print("❌ 带图片的长文档生成工具类不可用")
        print("⚠️ 长文档生成工具已暂时注释，专注测试PDF解析")
        
        # 6. PDF解析工具 - 智能提取PDF中的文本、图片和表格
        if PDFParserTool:
            try:
                pdf_parser_tool = PDFParserTool()
                core_tools.append(pdf_parser_tool)
                print("✅ PDF解析工具加载成功")
            except Exception as e:
                print(f"❌ PDF解析工具加载失败: {e}")
        else:
            print("❌ PDF解析工具类不可用")
        
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
        summary = "🔧 PDF解析工具测试模式:\n\n"
        
        tool_descriptions = {
            "pdf_parser": "📄 PDF智能解析 - 提取文本、图片、表格并结构化重组",
        }
        
        for tool_name, description in tool_descriptions.items():
            if tool_name in self.tools:
                summary += f"✅ {description}\n"
            else:
                summary += f"❌ {description} (未加载)\n"
        
        summary += f"\n📊 总计: {len(self.tools)} 个工具已加载"
        summary += "\n\n🎯 当前测试功能："
        summary += "\n📄 PDF解析 → 智能提取 → 文本/图片/表格 → 结构化重组"
        summary += "\n\n⚠️ 其他工具暂时注释，专注测试PDF解析功能"
        return summary

    
    def register_advanced_long_document_tool(self):
        """注册高级长文档生成工具（已废弃，使用带图片的长文档生成工具）"""
        print("⚠️ 高级长文档生成工具已废弃，请使用带图片的长文档生成工具")

def create_core_tool_registry(deepseek_client=None) -> ToolRegistry:
    """创建核心工具注册表"""
    registry = ToolRegistry()
    
    # 如果提供了deepseek_client，为RAG工具设置AI客户端 (暂时注释，专注测试PDF解析)
    # if deepseek_client:
    #     rag_tool = registry.get_tool("rag_tool")
    #     if rag_tool and hasattr(rag_tool, 'field_processor'):
    #         field_processor = getattr(rag_tool, 'field_processor')
    #         if hasattr(field_processor, 'deepseek_client'):
    #             field_processor.deepseek_client = deepseek_client
    #             print("🤖 RAG工具已配置AI客户端")
    print("⚠️ PDF解析测试模式，RAG工具配置已暂时跳过")
    
    return registry

# 系统六大核心功能使用指南
SYSTEM_FUNCTIONS_GUIDE = """
🎯 ReactAgent系统六大核心功能使用流程:

**功能1: 📤 文件上传智能分类处理**
工具: template_classifier
- 参数: file_path="上传文件路径", action="classify"
- 功能: 自动判断文档类型（模板文档 vs 资料文档）
- 处理逻辑: 
  * 模板文档 → 保存到templates_storage文件夹，保留原始文件名
  * 资料文档 → 自动调用RAG工具进行embedding处理
- 适用场景: 用户刚上传文档，需要智能分类处理

**功能2: 📄 带图片长文档生成**
工具: image_document_generator
- 参数: action="generate", request="生成需求描述", chathistory="可选对话历史"
- 功能: AI驱动的专业长篇文档智能生成（支持图片插入）
- 处理逻辑: 
  * 创作指令分析 → 智能大纲生成 → 逐章节内容生成 → 图片检索插入 → 专业DOCX输出
- 适用场景: 生成技术方案、研究报告、项目计划等包含图片的长篇文档

**功能3: 📋 模板文档生成**
工具: professional_document_tool
- 参数: file_path="模板文件路径", user_request="用户需求", processing_mode="auto"
- 功能: 基于模板和RAG的智能文档填充
- 处理逻辑: 
  * 从templates_storage找到用户描述的模板文件
  * 结合用户关键词进行RAG检索相关资料
  * 将检索资料智能插入到模板对应位置
- 适用场景: 各种记录表、申请表单、审批表格的智能填充

**功能4: 🖼️ 图片RAG系统**
工具: image_rag_tool
- 参数: action="upload/search", image_path="图片路径", description="图片描述", query="搜索查询"
- 功能: 图片上传和基于文本描述的图片检索
- 处理逻辑:
  * 上传图片 → AI生成描述 → 向量化存储 → 文本查询检索相关图片
- 适用场景: 图片知识库管理、基于描述的图片搜索、图片资料整理

**功能5: 📄 PDF智能解析**
工具: pdf_parser
- 参数: pdf_path="PDF文件路径", action="parse/list_models/get_stats", output_dir="输出目录", model_name="模型名称"
- 功能: 智能提取PDF中的文本、图片、表格，并重新组织为结构化数据
- 处理逻辑:
  * PDF解析 → 文本提取 → 图片/表格识别 → LLM内容重组 → 结构化JSON输出
- 适用场景: PDF文档内容提取、学术论文分析、技术文档处理、图片表格提取

**辅助功能: 📚 RAG检索**
工具: rag_tool
- 参数: operation="search/add_document/list_documents", query="搜索内容", file_path="文档路径"
- 功能: 文档embedding处理和智能搜索
- 适用场景: 简单问答、文档搜索、知识管理

🔄 五大核心功能工作流程:

📤 **功能1工作流程：文件上传**
用户上传文档 → template_classifier智能分类 → 
模板文档保存到templates_storage / 资料文档RAG处理

📄 **功能2工作流程：带图片长文档生成**
用户需求分析 → image_document_generator → 
创作指令 → 大纲生成 → 章节内容 → 图片检索插入 → DOCX文档输出

📋 **功能3工作流程：模板文档生成**
用户需求 → professional_document_tool → 
找到模板文件 → RAG检索资料 → 智能填充插入 → 填充完成的文档

🖼️ **功能4工作流程：图片RAG系统**
用户上传图片 → image_rag_tool → 
AI生成描述 → 向量化存储 → 文本查询 → 检索相关图片

📄 **功能5工作流程：PDF智能解析**
用户上传PDF → pdf_parser → 
智能解析提取 → 文本/图片/表格分离 → LLM内容重组 → 结构化输出

💡 系统优势:
- 🧠 智能文档类型识别和自动分类
- 🚀 专业长文档多阶段智能生成（支持图片）
- 📋 基于模板+RAG的智能填充系统
- 🖼️ 强大的图片RAG检索和管理
- 📄 智能PDF解析和内容提取
- 🔍 强大的向量搜索和知识管理
- 🏗️ 专为工程技术文档优化
- 📄 支持多种格式输入输出
- ⚡ 一站式文档和图片处理解决方案
"""

try:
    from rag_tool_chroma import RAGTool
except ImportError:
    try:
        from .rag_tool_chroma import RAGTool
    except ImportError:
        RAGTool = None

try:
    from professional_document_tool import ProfessionalDocumentTool
except ImportError:
    try:
        from .professional_document_tool import ProfessionalDocumentTool
    except ImportError:
        ProfessionalDocumentTool = None

try:
    from template_classifier_tool import TemplateClassifierTool
except ImportError:
    try:
        from .template_classifier_tool import TemplateClassifierTool
    except ImportError:
        TemplateClassifierTool = None

try:
    from pdf_parser_tool import PDFParserTool
except ImportError:
    try:
        from .pdf_parser_tool import PDFParserTool
    except ImportError:
        PDFParserTool = None

try:
    from image_rag_tool import ImageRAGTool
except ImportError:
    try:
        from .image_rag_tool import ImageRAGTool
    except ImportError:
        ImageRAGTool = None

try:
    from advanced_long_document_generator_tool import AdvancedLongDocumentGeneratorTool
except ImportError:
    try:
        from .advanced_long_document_generator_tool import AdvancedLongDocumentGeneratorTool
    except ImportError:
        AdvancedLongDocumentGeneratorTool = None

try:
    from image_document_generator_tool import ImageDocumentGeneratorTool
except ImportError:
    try:
        from .image_document_generator_tool import ImageDocumentGeneratorTool
    except ImportError:
        ImageDocumentGeneratorTool = None

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
        },

        {
            "name": "pdf_parser",
            "description": """📄 PDF智能解析工具 - 提取文本、图片、表格并结构化重组

核心功能：
- 📄 智能PDF解析：使用Docling和LLM技术提取PDF内容
- 🖼️ 图片识别和保存：自动识别并保存PDF中的图片
- 📊 表格识别和保存：自动识别并保存PDF中的表格
- 🧠 内容重组：使用LLM重新组织内容为结构化数据
- 📋 多模型支持：支持GPT-4o、Claude-3.5等多种AI模型
- 📊 统计信息：提供详细的解析统计和内容分析

输出文件：
- parsed_content.json: 结构化文本内容
- images.json: 图片信息
- tables.json: 表格信息
- summary.json: 汇总信息
- picture-*.png: 提取的图片文件
- table-*.png: 提取的表格文件

适用场景：PDF文档内容提取、学术论文分析、技术文档处理、图片表格提取""",
            "parameters": {
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "PDF文件路径"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["parse", "list_models", "get_stats"],
                        "default": "parse",
                        "description": "操作类型：parse(解析PDF), list_models(列出可用模型), get_stats(获取统计信息)"
                    },
                    "output_dir": {
                        "type": "string",
                        "default": "parser_output",
                        "description": "输出目录路径"
                    },
                    "model_name": {
                        "type": "string",
                        "default": "gpt-4o",
                        "description": "使用的AI模型名称"
                    }
                },
                "required": []
            },
            "function": lambda **kwargs: PDFParserTool().execute(**kwargs)
        },

        {
            "name": "image_rag_tool",
            "description": """🖼️ 图片RAG工具 - 图片上传和基于文本描述的图片检索

核心功能：
- 🖼️ 图片上传存储：支持多种图片格式上传和存储
- 📝 智能描述生成：AI自动生成图片描述
- 🔍 文本检索图片：基于描述搜索相关图片
- 💾 向量化存储：图片描述向量化存储和管理
- 🗄️ 图片知识库：建立企业图片资产管理

存储系统：
- MinIO对象存储：图片文件存储
- MySQL数据库：图片元数据管理
- ChromaDB向量库：描述向量化检索

适用场景：图片知识库管理、基于描述的图片搜索、图片资料整理""",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["upload", "search", "list"],
                        "description": "操作类型：upload(上传图片), search(搜索图片), list(列出图片)"
                    },
                    "image_path": {
                        "type": "string",
                        "description": "图片文件路径（upload时需要）"
                    },
                    "description": {
                        "type": "string",
                        "description": "图片描述（upload时可选）"
                    },
                    "query": {
                        "type": "string",
                        "description": "搜索查询（search时需要）"
                    },
                    "top_k": {
                        "type": "integer",
                        "default": 5,
                        "description": "返回结果数量（search时可选）"
                    }
                },
                "required": ["action"]
            },
            "function": lambda **kwargs: ImageRAGTool().execute(**kwargs)
        },

        {
            "name": "image_document_generator",
            "description": """📄 带图片长文档生成工具 - AI驱动的专业长篇文档智能生成（支持图片插入）

核心功能：
- 🧠 智能大纲生成：AI自动规划文档章节结构
- 📝 逐章节生成：分步骤生成详细内容
- 🖼️ 图片智能插入：自动检索和插入相关图片
- 📄 专业格式化：生成符合标准的DOCX文档
- 🎯 领域优化：针对技术、管理等专业领域

生成流程：
1. 创作指令分析
2. 智能大纲规划
3. 章节内容生成
4. 图片检索插入
5. 专业格式输出

适用场景：技术方案、研究报告、项目计划、培训材料等长篇文档生成""",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["generate"],
                        "default": "generate",
                        "description": "操作类型：generate(生成文档)"
                    },
                    "request": {
                        "type": "string",
                        "description": "文档生成需求描述"
                    },
                    "chathistory": {
                        "type": "string",
                        "description": "对话历史上下文（可选）",
                        "default": ""
                    }
                },
                "required": ["request"]
            },
            "function": lambda **kwargs: ImageDocumentGeneratorTool().execute(**kwargs)
        },

        {
            "name": "advanced_long_document_generator",
            "description": """📄 高级长文档生成工具 - 专业长篇文档智能生成器（3000-8000字）

核心功能：
- 📊 智能文档规划：AI自动分析需求和规划文档结构
- 📝 多阶段生成：分阶段生成高质量长篇内容
- 🎯 专业领域优化：针对建筑、工程、管理等专业领域
- 📋 多种模板支持：建筑安全、施工组织、古建保护等
- 🔍 RAG增强：结合知识库生成专业内容

生成特点：
- 文档长度：3000-8000字
- 专业术语：确保术语使用准确规范
- 格式标准：符合专业文档格式要求
- 内容丰富：包含详细分析和实用建议

适用场景：技术方案、可行性报告、施工方案、研究报告、管理制度""",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["generate", "list_templates"],
                        "default": "generate",
                        "description": "操作类型：generate(生成文档), list_templates(列出模板)"
                    },
                    "request": {
                        "type": "string",
                        "description": "文档生成需求描述"
                    },
                    "template_type": {
                        "type": "string",
                        "enum": ["construction_safety", "construction_organization", "heritage_building", "general_technical", "management_system"],
                        "default": "general_technical",
                        "description": "文档模板类型"
                    },
                    "context": {
                        "type": "string",
                        "description": "项目背景或上下文信息",
                        "default": ""
                    }
                },
                "required": ["request"]
            },
            "function": lambda **kwargs: AdvancedLongDocumentGeneratorTool().execute(**kwargs)
        }
    ]
    
    for tool in tools:
        agent.register_tool(
            name=tool["name"],
            description=tool["description"], 
            parameters=tool["parameters"],
            function=tool["function"]
        )
    
    print("✅ 已注册7个核心工具：")
    print("   📚 rag_tool - RAG文档处理工具")
    print("   🎯 professional_document_tool - 专业文档工具（完整版）")
    print("   📋 template_classifier - 模板分类工具") 
    print("   📄 pdf_parser - PDF智能解析工具")
    print("   🖼️ image_rag_tool - 图片RAG工具")
    print("   📄 image_document_generator - 带图片长文档生成工具")
    print("   📄 advanced_long_document_generator - 高级长文档生成工具") 