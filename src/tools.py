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
    """工具注册表 - 核心三工具"""
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
        

        # 2. 模板转换工具 - DOC/DOCX转JSON结构化数据
        try:
            from .template_conversion_tool import TemplateConversionTool
            template_converter = TemplateConversionTool()
            core_tools.append(template_converter)
            print("✅ 模板转换工具加载成功")
        except ImportError as e:
            print(f"❌ 模板转换工具加载失败: {e}")
        
        # 3. 模板填充工具 - AI智能填充Word文档
        try:
            from .template_inserter_tool import TemplateInserterTool
            template_inserter = TemplateInserterTool()
            core_tools.append(template_inserter)
            print("✅ 模板填充工具加载成功")
        except ImportError as e:
            print(f"❌ 模板填充工具加载失败: {e}")
        
        # 4. 专业文档代理工具 - 高级文档生成协调器
        try:
            from .professional_document_agent_tool import ProfessionalDocumentAgentTool
            professional_agent = ProfessionalDocumentAgentTool()
            core_tools.append(professional_agent)
            print("✅ 专业文档代理工具加载成功")
        except ImportError as e:
            print(f"❌ 专业文档代理工具加载失败: {e}")
        
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
            "rag_tool": "📚 RAG工具 - 文档embedding处理、智能搜索、基于模板字段的内容填充",
            "template_conversion": "🔄 模板转换工具 - DOC/DOCX模板转换为JSON结构化数据，智能占位符识别",
            "template_inserter": "🎯 模板填充工具 - AI智能将JSON内容数据填充到模板中生成Word文档",
            "professional_document_agent": "🧠 专业文档代理工具 - RAG检索+AI智能合并的高级文档生成协调器"
        }
        
        for tool_name, description in tool_descriptions.items():
            if tool_name in self.tools:
                summary += f"✅ {description}\n"
            else:
                summary += f"❌ {description} (未加载)\n"
        
        summary += f"\n📊 总计: {len(self.tools)} 个工具已加载"
        return summary

    def register_long_document_tool(self, deepseek_client):
        """注册长文档生成工具"""
        try:
            from .long_document_generator_tool import LongDocumentGeneratorTool
            long_doc_tool = LongDocumentGeneratorTool(deepseek_client)
            # 直接添加到工具字典，避免类型检查问题
            self.tools[long_doc_tool.name] = long_doc_tool
            print("✅ 长文档生成工具加载成功")
        except ImportError as e:
            print(f"❌ 长文档生成工具加载失败: {e}")

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
        
        # 注册长文档生成工具
        registry.register_long_document_tool(deepseek_client)
    
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

4️⃣ 长文档生成工具 (long_document_generator):
   - 生成长文档: action="generate", request="生成技术报告", chat_history="对话历史"
   - 查询任务状态: action="status", task_id="任务ID"
   - 获取生成文档: action="get_document", task_id="任务ID"
   - 任务列表: action="list_tasks"

5️⃣ 专业文档代理工具 (professional_document_agent):
   - 生成专业文档: action="generate", request="用户需求", template_id="模板ID"
   - RAG独立检索: action="search", query="搜索内容", template_id="模板ID"
   - 获取模板信息: action="template", template_id="模板ID"

🔄 推荐工作流程:

📋 模板文档处理流程:
资料文档 → RAG工具(embedding) → 旧模板(DOC) → 模板转换工具(转换+分析) → 
模板填充工具(AI智能填充) → 填充好的docx文档

📄 长文档生成流程:
用户需求 → 长文档生成工具(多阶段生成) → 创作指令分析 → 大纲生成与精炼 → 
章节内容生成 → 文档整合 → 完整的长篇文档

🧠 专业文档代理流程:
用户需求 → 专业文档代理工具(协调处理) → RAG检索相关信息 → 模板智能管理 → 
多源信息整合 → AI智能合并 → 专业级文档输出

💡 核心优势:
- 支持旧版DOC格式模板处理
- 智能占位符识别和转换
- AI智能内容映射和填充
- 多阶段长文档智能生成
- 任务状态管理和进度跟踪
- 极简的文档处理工作流
- 高质量文档输出和结构化数据
- 一站式文档解决方案

🎯 适用场景:
- 施工组织设计等模板文档填充
- 技术报告、研究文档生成
- 项目方案、分析报告撰写
- 长篇专业文档创作
- 文档模板标准化处理
""" 