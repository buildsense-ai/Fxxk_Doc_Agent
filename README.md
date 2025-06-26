# Enhanced ReAct Agent - 纯ReAct智能文档处理系统

## 🎯 项目概述

Enhanced ReAct Agent 是一个基于DeepSeek AI的智能文档处理系统，采用**纯ReAct架构**和**四工具生态**，通过Agent自主推理和决策来处理各种文档相关任务。

## 🧠 纯ReAct架构设计

### 核心理念
- **🧠 Reasoning**: Agent通过思考分析当前情况
- **🎯 Acting**: Agent自主选择合适的工具行动  
- **🔄 循环迭代**: 基于观察结果继续推理和行动

### 架构流程
```
用户请求 → ReAct循环 → Thought → Action → Observation → Final Answer
```

**关键特性:**
- ✅ 所有请求都通过ReAct循环处理
- ✅ Agent自主推理和工具选择
- ✅ 完全透明的决策过程
- ✅ 高度灵活和可扩展

## 🔧 四工具生态架构

### 工具架构图
```
文档上传 → RAG工具(embedding&搜索) → 模板转换工具(DOC→JSON) → 
模板填充工具(智能填充) → 长文档生成工具(多阶段生成) → 最终文档
```

### 四个核心工具

1. **🔍 RAG工具 (rag_tool)**
   - 文档embedding处理和向量化存储
   - 智能搜索和内容检索
   - 文档管理和清理功能

2. **📋 模板转换工具 (template_conversion)**
   - DOC/DOCX文件转换为JSON结构化数据
   - 模板字段提取和分析
   - 支持多种占位符格式

3. **📝 模板填充工具 (template_inserter)**
   - 基于模板JSON和内容进行智能填充
   - AI驱动的内容生成和适配
   - 保持原有格式和样式

4. **📄 长文档生成工具 (long_document_generator)**
   - 多阶段智能长文档生成
   - 创作指令分析 → 大纲生成 → 精炼循环 → 章节生成 → 文档整合
   - 支持技术报告、项目方案、分析文档等

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd ReactAgent

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置 DEEPSEEK_API_KEY
```

### 2. 运行系统

#### Web界面（推荐）
```bash
# 启动Web对话界面
python web_app.py
```
然后在浏览器中访问 http://localhost:5000 开始对话

#### 命令行界面
```bash
# 启动命令行界面
python run_agent.py
```

### 3. 使用示例

**文档管理:**
```
🤔 用户: 查看我上传了哪些文档
🤖 Agent: [自动选择rag_tool，查询文档列表]
```

**模板处理:**
```
🤔 用户: 使用模板填充施工组织设计
🤖 Agent: [自动选择template_conversion + template_inserter]
```

**长文档生成:**
```
🤔 用户: 生成一份技术报告
🤖 Agent: [自动选择long_document_generator，启动多阶段生成]
```

## 🧪 Agent推理示例

### 用户请求: "生成技术报告"

**Agent推理过程:**
```
Thought: 用户要求生成技术报告，这是一个长文档生成任务。
我需要使用long_document_generator工具来完成这个任务。

Action: long_document_generator
Action Input: {"action": "generate", "request": "生成技术报告"}

Observation: 技术报告生成任务已启动，任务ID: xxx...

Final Answer: 技术报告《Emerging Technology Trends 2023》已成功生成...
```

## 📋 工具详细说明

### RAG工具 (rag_tool)

**核心功能:**
- 文档上传和embedding处理
- 智能搜索和内容检索
- 文档列表查看和管理

**Agent自动调用场景:**
- "查看文档列表"
- "上传文档到RAG"
- "搜索相关内容"

### 模板转换工具 (template_conversion)

**核心功能:**
- DOC/DOCX转换为JSON结构
- 模板字段提取和分析
- 模板列表管理

**Agent自动调用场景:**
- "处理模板文件"
- "转换模板格式"
- "分析模板结构"

### 模板填充工具 (template_inserter)

**核心功能:**
- 基于模板进行智能填充
- AI驱动的内容生成
- 保持原有文档格式

**Agent自动调用场景:**
- "使用模板填充"
- "基于模板生成文档"
- "模板内容插入"

### 长文档生成工具 (long_document_generator)

**核心功能:**
- 五阶段智能生成流程
- 支持多种文档类型
- 任务状态跟踪和管理

**Agent自动调用场景:**
- "生成技术报告"
- "创建项目方案"
- "撰写分析文档"

**五阶段生成流程:**
1. **创作指令分析** (5%): 分析用户需求
2. **初始大纲生成** (15%): 生成文档大纲
3. **大纲精炼循环** (25-40%): AI自我评审优化
4. **章节内容生成** (40-85%): 逐章生成内容
5. **文档整合** (85-100%): 生成完整文档

## 📁 项目结构

```
ReactAgent/
├── src/                                    # 源代码目录
│   ├── enhanced_react_agent.py            # 纯ReAct Agent核心
│   ├── rag_tool_chroma.py                 # RAG工具
│   ├── template_conversion_tool.py        # 模板转换工具
│   ├── template_inserter_tool.py          # 模板填充工具
│   ├── long_document_generator_tool.py    # 长文档生成工具
│   ├── tools.py                           # 工具注册表
│   └── deepseek_client.py                 # DeepSeek API客户端
├── long_generator/                        # 长文档生成器模块
│   ├── generator.py                       # 核心生成逻辑
│   ├── services.py                        # 外部服务接口
│   └── config.py                          # 配置管理
├── templates/                             # Web模板目录
├── test/                                   # 测试文件目录
├── generated_documents/                    # 生成的文档目录
├── rag_storage/                           # RAG向量存储目录
├── templates_storage/                     # 模板存储目录
├── web_app.py                             # Web对话界面
├── run_agent.py                           # 命令行启动脚本
└── README.md                             # 项目说明
```

## 🎯 支持的使用场景

### 文档管理
- "查看我上传了哪些文档"
- "清空所有文档"
- "上传新的PDF文件"

### 模板处理
- "处理这个Word模板"
- "使用模板填充施工组织设计"
- "基于模板生成报告"

### 长文档生成
- "生成一份技术报告"
- "创建项目实施方案"
- "撰写详细的分析文档"
- "制作可行性研究报告"

### 复合任务
- "基于上传的资料和模板生成最终文档"
- "先处理模板再填充内容"

## 🛠️ 依赖项

- **python-docx**: Word文档处理
- **chromadb**: 向量数据库
- **PyMuPDF**: PDF文档处理
- **requests**: HTTP请求
- **python-dotenv**: 环境变量管理
- **colorama**: 终端颜色输出

## 📖 配置指南

### 环境变量配置

在 `.env` 文件中配置：

```bash
# DeepSeek API配置
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 可选配置
RAG_STORAGE_DIR=rag_storage
TEMPLATES_STORAGE_DIR=templates_storage
GENERATED_DOCS_DIR=generated_documents
```

## 🎉 架构优势

1. **真正的ReAct设计**: 所有请求都通过推理循环处理
2. **智能决策**: Agent自主选择最合适的工具
3. **高度灵活**: 无需预设处理逻辑，动态适应
4. **完全透明**: 每步推理过程都可见可追踪
5. **易于扩展**: 新工具即插即用，无需修改核心逻辑

**现在的ReactAgent是一个真正智能的文档处理系统，会根据用户需求自主思考、推理并选择合适的工具来完成任务！** 🚀
