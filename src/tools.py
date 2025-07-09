"""
Tools for ReAct Agent - 核心五工具架构
专注于文档处理和图片RAG的五个核心工具
"""
import os
import json
from typing import Dict, Any, List, Optional

# 导入工具基类
from src.base_tool import Tool

# 核心五工具架构

class ToolRegistry:
    """工具注册表 - 核心五工具"""
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._register_core_tools()
    
    def _register_core_tools(self):
        """注册核心工具"""
        core_tools = []
        
        # 1. RAG工具 - 文档embedding处理和智能搜索
        if RAGTool:
            try:
                rag_tool = RAGTool()
                core_tools.append(rag_tool)
                print("✅ RAG工具加载成功")
            except Exception as e:
                print(f"❌ RAG工具加载失败: {e}")
        else:
            print("❌ RAG工具类不可用")
        
        # 2. 图片RAG工具 - 图片上传和基于文本描述的图片检索
        if ImageRAGTool:
            try:
                image_rag_tool = ImageRAGTool()
                core_tools.append(image_rag_tool)
                print("✅ 图片RAG工具加载成功")
            except Exception as e:
                print(f"❌ 图片RAG工具加载失败: {e}")
        else:
            print("❌ 图片RAG工具类不可用")
        
        # 3. PDF解析工具 - 智能提取PDF中的文本、图片和表格
        if PDFParserTool:
            try:
                pdf_parser_tool = PDFParserTool()
                core_tools.append(pdf_parser_tool)
                print("✅ PDF解析工具加载成功")
            except Exception as e:
                print(f"❌ PDF解析工具加载失败: {e}")
        else:
            print("❌ PDF解析工具类不可用")
        
        # 4. PDF Embedding工具 - 将解析后的PDF内容进行向量化存储
        if PDFEmbeddingTool:
            try:
                pdf_embedding_tool = PDFEmbeddingTool()
                core_tools.append(pdf_embedding_tool)
                print("✅ PDF Embedding工具加载成功")
            except Exception as e:
                print(f"❌ PDF Embedding工具加载失败: {e}")
        else:
            print("❌ PDF Embedding工具类不可用")
        
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
        summary = "🔧 ReactAgent系统全套工具:\n\n"
        
        tool_descriptions = {
            "rag_tool": "📚 RAG文档处理 - 向量化存储和智能检索",
            "image_rag_tool": "🖼️ 图片RAG工具 - 图片存储和语义检索", 
            "pdf_parser": "📄 PDF智能解析 - 提取文本、图片、表格并结构化重组",
        }
        
        for tool_name, description in tool_descriptions.items():
            if tool_name in self.tools:
                summary += f"✅ {description}\n"
            else:
                summary += f"❌ {description} (未加载)\n"
        
        summary += f"\n📊 总计: {len(self.tools)} 个工具已加载"
        summary += "\n\n🎯 系统核心功能："
        summary += "\n🖼️ 图片RAG管理 → 📄 PDF智能解析 → 📚 知识库检索"
        summary += "\n\n✅ 全套工具已启用，ReactAgent系统完全就绪！"
        return summary

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

# 系统核心功能使用指南
SYSTEM_FUNCTIONS_GUIDE = """
🎯 ReactAgent系统核心功能使用流程:

**功能1: 🖼️ 图片RAG系统**
工具: image_rag_tool
- 参数: action="upload/search", image_path="图片路径", description="图片描述", query="搜索查询"
- 功能: 图片上传和基于文本描述的图片检索
- 处理逻辑:
  * 上传图片 → AI生成描述 → 向量化存储 → 文本查询检索相关图片
- 适用场景: 图片知识库管理、基于描述的图片搜索、图片资料整理

**功能2: 📄 PDF智能解析**
工具: pdf_parser
- 参数: pdf_path="PDF文件路径", action="parse/list_models/get_stats", output_dir="输出目录", model_name="模型名称"
- 功能: 智能提取PDF中的文本、图片、表格，并重新组织为结构化数据
- 处理逻辑:
  * PDF解析 → 文本提取 → 图片/表格识别 → LLM内容重组 → 结构化JSON输出
- 适用场景: PDF文档内容提取、学术论文分析、技术文档处理、图片表格提取

**功能3: 📚 RAG检索**
工具: rag_tool
- 参数: operation="search/add_document/list_documents", query="搜索内容", file_path="文档路径"
- 功能: 文档embedding处理和智能搜索
- 适用场景: 简单问答、文档搜索、知识管理
"""

try:
    from rag_tool_chroma import RAGTool
except ImportError:
    try:
        from .rag_tool_chroma import RAGTool
    except ImportError:
        RAGTool = None

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
    from pdf_embedding_tool import PDFEmbeddingTool
except ImportError:
    try:
        from .pdf_embedding_tool import PDFEmbeddingTool
    except ImportError:
        PDFEmbeddingTool = None

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
- 🆕 PDF解析后文件夹处理（parsed_content.json自动embedding）

适用场景：当需要对大量文档进行知识管理、语义搜索或构建专业知识库时使用""",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["upload", "search", "fill_fields", "list", "clear", "process_parsed_folder"],
                        "description": "操作类型：upload(上传文档), search(搜索), fill_fields(填充模板字段), list(列出文档), clear(清空), process_parsed_folder(处理PDF解析文件夹)"
                    },
                    "file_path": {
                        "type": "string", 
                        "description": "文档文件路径（upload时需要）"
                    },
                    "query": {
                        "type": "string",
                        "description": "搜索查询语句（search时需要）"
                    },
                    "folder_path": {
                        "type": "string",
                        "description": "PDF解析后的文件夹路径（process_parsed_folder时需要）"
                    },
                    "project_name": {
                        "type": "string",
                        "description": "项目名称（process_parsed_folder时可选）"
                    },
                    "template_fields_json": {
                        "type": "object",
                        "description": "模板字段JSON（fill_fields时需要）"
                    },
                    "filename": {
                        "type": "string",
                        "description": "文件名（upload时可选）"
                    }
                },
                "required": ["action"]
            },
            "function": lambda **kwargs: RAGTool().execute(**kwargs)
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
- 🆕 PDF解析后images.json批量处理：自动处理context并embedding

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
                        "enum": ["upload", "search", "list", "stats", "process_images_json"],
                        "description": "操作类型：upload(上传图片), search(搜索图片), list(列出图片), stats(统计信息), process_images_json(处理PDF解析的images.json)"
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
                    "folder_path": {
                        "type": "string",
                        "description": "PDF解析后的文件夹路径（process_images_json时需要）"
                    },
                    "project_name": {
                        "type": "string",
                        "description": "项目名称（process_images_json时可选）"
                    },
                    "top_k": {
                        "type": "integer",
                        "default": 5,
                        "description": "返回结果数量（search时可选）"
                    },
                    "min_score": {
                        "type": "number",
                        "default": 0.0,
                        "description": "最小相似度分数（search时可选）"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 20,
                        "description": "列表显示数量（list时可选）"
                    },
                    "offset": {
                        "type": "integer",
                        "default": 0,
                        "description": "列表偏移量（list时可选）"
                    }
                },
                "required": ["action"]
            },
            "function": lambda **kwargs: ImageRAGTool().execute(**kwargs)
        },

        {
            "name": "pdf_embedding",
            "description": """📊 PDF内容向量化工具 - 统一处理文本和图片的embedding存储

核心功能：
- 📊 统一向量化：将parsed_content.json和images.json统一进行embedding
- 🔍 智能搜索：支持按内容类型过滤的统一语义搜索
- 📋 元数据管理：完整保留源文件、页面、位置等元数据
- 📈 统计分析：提供embedding统计和集合信息

存储优势：
- 单一集合存储：文本和图片存储在同一个ChromaDB集合中
- 元数据区分：通过content_type字段区分文本和图片
- 统一搜索：一个接口可以搜索文本、图片或全部内容

工作流程：
1. PDF解析 → parsed_content.json + images.json
2. PDF embedding → 统一向量化存储
3. 智能搜索 → 按类型过滤的语义检索

适用场景：PDF内容知识库构建、多模态语义搜索、内容分析""",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["embed", "search", "stats"],
                        "default": "embed",
                        "description": "操作类型：embed(向量化PDF内容), search(统一搜索), stats(统计信息)"
                    },
                    "parser_output_dir": {
                        "type": "string",
                        "description": "PDF解析器输出目录路径（embed操作必需）"
                    },
                    "query": {
                        "type": "string",
                        "description": "搜索查询内容（search操作必需）"
                    },
                    "content_type": {
                        "type": "string",
                        "enum": ["text", "image", "all"],
                        "default": "all",
                        "description": "内容类型过滤：text(仅文本), image(仅图片), all(全部内容)"
                    },
                    "top_k": {
                        "type": "integer",
                        "default": 5,
                        "description": "返回结果数量（search操作可选）"
                    },
                    "source_file_filter": {
                        "type": "string",
                        "description": "按源文件过滤搜索结果（search操作可选）"
                    }
                },
                "required": ["action"]
            },
            "function": lambda **kwargs: PDFEmbeddingTool().execute(**kwargs)
        }
    ]
    
    for tool in tools:
        agent.register_tool(
            name=tool["name"],
            description=tool["description"], 
            parameters=tool["parameters"],
            function=tool["function"]
        )
    
    print(f"✅ 已注册{len(tools)}个核心工具：")
    print("   📚 rag_tool - RAG文档处理工具")
    print("   📄 pdf_parser - PDF智能解析工具")
    print("   🖼️ image_rag_tool - 图片RAG工具")
    print("   📊 pdf_embedding - PDF内容向量化工具") 