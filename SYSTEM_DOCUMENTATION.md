# ReactAgent 智能文档处理系统 - 完整说明文档

## 📋 目录

1. [系统概述](#系统概述)
2. [核心功能](#核心功能)
3. [技术架构](#技术架构)
4. [安装配置](#安装配置)
5. [使用指南](#使用指南)
6. [功能详解](#功能详解)
7. [API接口](#api接口)
8. [故障排除](#故障排除)
9. [开发指南](#开发指南)
10. [更新日志](#更新日志)

---

## 🎯 系统概述

### 什么是 ReactAgent？

ReactAgent 是一个基于 **ReAct（Reasoning + Acting）** 框架的智能文档处理系统，专门设计用于处理和生成专业技术文档。该系统结合了人工智能推理、RAG检索技术和模板处理能力，为用户提供智能化的文档处理解决方案。

### 🌟 系统特色

- **🧠 智能推理**: 基于DeepSeek AI的智能推理和决策能力
- **📚 知识增强**: RAG（检索增强生成）技术，结合向量数据库检索
- **🔄 流式处理**: 实时显示AI思考过程，提供透明的处理体验
- **📋 模板智能**: 智能识别和处理各种文档模板
- **🎯 专业优化**: 针对建筑工程、安全管理等专业领域优化

### 🏆 核心价值

1. **效率提升**: 自动化文档生成，减少人工重复工作
2. **质量保证**: AI辅助确保文档格式规范和内容准确
3. **知识管理**: 建立企业知识库，实现知识复用
4. **流程优化**: 标准化文档处理流程，提高工作效率

---

## 🚀 核心功能

### 1. 📤 智能文档分类处理

#### 功能描述
系统能够自动识别上传文档的类型，并选择合适的处理策略：

- **模板文档**: 自动保存到模板库，用于后续生成工作
- **资料文档**: 进行向量化处理，加入知识库

#### 技术实现
- AI内容分析 + 规则匹配
- 支持格式：DOC、DOCX、PDF、TXT
- 智能关键词识别和内容特征分析

#### 使用场景
- 企业文档库建设
- 模板标准化管理
- 知识资产积累

### 2. 📋 专业模板文档生成

#### 功能描述
基于已有模板生成专业的填充文档：

- **智能字段匹配**: 自动识别模板中的填写字段
- **内容智能填充**: 结合RAG检索结果智能填充内容
- **格式保持**: 保持原有模板的格式和结构

#### 支持的模板类型
- 📝 现场复核记录
- 🏗️ 施工检查表
- 📊 质量验收单
- 🔒 安全管理表格
- 📄 技术审批单

#### 生成流程
1. 选择合适的模板文件
2. RAG检索相关资料
3. AI智能分析和匹配
4. 自动填充生成文档
5. 格式化输出DOCX文件

### 3. 📄 长文档智能生成

#### 功能描述
生成3000-8000字的专业长篇文档：

- **智能大纲生成**: AI自动规划文档章节结构
- **分章节生成**: 逐章节生成详细内容
- **专业术语优化**: 确保术语使用准确规范
- **格式标准化**: 符合专业文档格式要求

#### 适用文档类型
- 📋 技术方案
- 📊 可行性报告
- 🏗️ 施工方案
- 📝 研究报告
- 📄 管理制度

### 4. 🔍 RAG智能检索

#### 功能描述
基于向量数据库的智能知识检索：

- **语义搜索**: 不仅仅是关键词匹配，理解语义含义
- **上下文理解**: 结合问题上下文提供精准结果
- **多源融合**: 整合多个文档来源的信息
- **相关性排序**: 按相关度排序检索结果

#### 技术特点
- 使用ChromaDB向量数据库
- 支持多种文档格式的向量化
- 实时索引更新
- 高效的相似度计算

---

## 🏗️ 技术架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        ReactAgent 系统架构                        │
├─────────────────────────────────────────────────────────────────┤
│  🌐 前端层 (Frontend)                                             │
│  ├── 📱 响应式Web界面 (HTML5/CSS3/JavaScript)                    │
│  ├── 🎨 流式思考过程可视化                                        │
│  ├── 📎 文件上传处理                                             │
│  └── 💬 实时聊天交互                                             │
├─────────────────────────────────────────────────────────────────┤
│  🔧 应用层 (Application)                                         │
│  ├── 🌐 Flask Web服务器                                         │
│  ├── 📡 SSE流式响应                                             │
│  ├── 🔄 文件管理系统                                             │
│  └── 🤖 Agent调度器                                             │
├─────────────────────────────────────────────────────────────────┤
│  🧠 核心层 (Core)                                               │
│  ├── 🤖 Enhanced ReAct Agent                                   │
│  ├── 🔧 智能工具注册表                                           │
│  ├── 💭 记忆管理系统                                             │
│  └── 🎯 流式处理引擎                                             │
├─────────────────────────────────────────────────────────────────┤
│  🛠️ 工具层 (Tools)                                              │
│  ├── 📚 RAG检索工具                                             │
│  ├── 🎯 专业文档工具                                             │
│  ├── 📋 模板分类工具                                             │
│  ├── 🚀 长文档生成工具                                           │
│  └── 🔌 DeepSeek客户端                                          │
├─────────────────────────────────────────────────────────────────┤
│  💾 存储层 (Storage)                                             │
│  ├── 🗄️ ChromaDB向量数据库                                      │
│  ├── 📁 文件存储系统                                             │
│  ├── 📝 文档生成目录                                             │
│  └── 🧠 Agent记忆存储                                           │
└─────────────────────────────────────────────────────────────────┘
```

### 核心组件说明

#### 1. Enhanced ReAct Agent
- **位置**: `src/enhanced_react_agent.py`
- **功能**: 核心推理引擎，负责问题分析和工具调用决策
- **特点**: 支持多轮对话、记忆管理、流式输出

#### 2. 工具系统 (Tools)
- **RAG工具**: 文档向量化和智能检索
- **专业文档工具**: 完整的文档处理流程
- **模板分类工具**: 智能文档类型识别
- **长文档生成工具**: 专业长篇文档生成

#### 3. DeepSeek客户端
- **位置**: `src/deepseek_client.py`
- **功能**: 与DeepSeek AI API的接口封装
- **特点**: 支持缓存、错误处理、代理配置

---

## ⚙️ 安装配置

### 环境要求

- **Python**: 3.8+
- **操作系统**: Windows 10+, macOS 10.15+, Linux
- **内存**: 建议8GB以上
- **磁盘空间**: 至少5GB可用空间

### 安装步骤

#### 1. 克隆项目
```bash
git clone <repository-url>
cd ReactAgent
```

#### 2. 安装依赖
```bash
pip install -r requirements.txt
```

#### 3. 配置环境变量
创建 `.env` 文件：
```env
# DeepSeek API配置
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# OpenRouter API配置（用于专业文档工具）
OPENROUTER_API_KEY=your_openrouter_api_key

# RAG服务配置
RAG_SERVICE_URL=http://43.139.19.144:3000
RAG_TIMEOUT=30

# Web应用配置
WEB_HOST=0.0.0.0
WEB_PORT=8000

# Agent配置
MAX_ITERATIONS=8
ENABLE_CACHE_MONITORING=true
VERBOSE_MODE=false
```

#### 4. 初始化数据库
```bash
# 系统会自动创建必要的目录和数据库
python -c "from src.rag_tool_chroma import RAGTool; RAGTool().initialize_storage()"
```

#### 5. 安装LibreOffice（可选）
用于处理DOC格式文件：
- Windows: 下载安装LibreOffice
- macOS: `brew install libreoffice`
- Linux: `sudo apt-get install libreoffice`

### 配置验证

运行配置检查脚本：
```bash
python -c "
from src.deepseek_client import DeepSeekClient
try:
    client = DeepSeekClient()
    print('✅ 配置验证成功')
except Exception as e:
    print(f'❌ 配置错误: {e}')
"
```

---

## 📖 使用指南

### Web界面使用

#### 1. 启动Web服务
```bash
python web_app.py
```

#### 2. 访问界面
打开浏览器访问: `http://localhost:8000`

#### 3. 基本操作

##### 文档上传
1. 点击上传按钮或拖拽文件到指定区域
2. 系统自动识别文档类型
3. 根据类型自动处理：
   - 模板文档 → 保存到模板库
   - 资料文档 → 向量化处理

##### 生成文档
1. 在聊天框输入需求，例如：
   - "生成一个一号楼的现场复核记录"
   - "基于安全检查模板生成检查报告"
   - "生成建筑施工安全技术方案"

2. 系统会显示AI思考过程：
   - 🤔 分析需求
   - 🔍 检索相关资料
   - 🛠️ 选择合适工具
   - 📝 生成文档

3. 下载生成的文档

### 命令行使用

#### 1. 交互模式
```bash
python run_agent.py
```

#### 2. 直接生成现场复核记录
```bash
python generate_site_review.py
```

#### 3. 批量处理
```python
from src.enhanced_react_agent import EnhancedReActAgent
from src.deepseek_client import DeepSeekClient

# 初始化
client = DeepSeekClient()
agent = EnhancedReActAgent(client)

# 批量处理多个请求
requests = [
    "生成一号楼现场复核记录",
    "生成安全检查表",
    "生成质量验收报告"
]

for req in requests:
    result = agent.solve(req)
    print(f"处理完成: {req}")
```

### 高级功能

#### 1. 自定义模板
1. 准备Word模板文件
2. 使用特殊标记表示填写字段：
   - `{字段名}`: 简单字段
   - `____`: 下划线填空
   - `【】`: 方括号占位符

3. 上传模板到 `templates_storage` 目录
4. 在对话中引用模板名称

#### 2. 知识库管理
```python
# 添加文档到知识库
from src.rag_tool_chroma import RAGTool

rag = RAGTool()
rag.process_document("path/to/document.pdf")

# 查询知识库
results = rag.search_documents("建筑安全规范")
```

#### 3. 自定义工具
```python
# 创建自定义工具
from src.tools import Tool

class CustomTool(Tool):
    def __init__(self):
        super().__init__(
            name="custom_tool",
            description="自定义工具描述"
        )
    
    def execute(self, **kwargs):
        # 工具逻辑
        return {"result": "处理结果"}
```

---

## 🔧 功能详解

### 1. 智能文档分类 (`template_classifier`)

#### 工作原理
1. **内容分析**: 提取文档文本内容
2. **特征识别**: 识别模板特征（空白字段、标签等）
3. **AI判断**: 使用AI模型进行类型判断
4. **规则验证**: 基于规则进行二次验证

#### 识别规则
```python
# 模板文档特征
template_features = [
    "____",           # 下划线填空
    "【】", "（）",    # 括号占位符
    "填写:", "签名:",  # 填写标签
    "日期:", "地点:"   # 结构化字段
]

# 资料文档特征
material_features = [
    "项目名称", "负责部门",
    "完成情况", "分析结果",
    "根据调研", "经过讨论"
]
```

#### 处理结果
- **模板文档**: 保存到 `templates_storage/` 目录
- **资料文档**: 调用RAG工具进行向量化
- **未知类型**: 提示用户确认

### 2. 专业文档生成 (`professional_document_tool`)

#### 三种处理模式

##### 模式1: 智能代理模式 (`professional_agent`)
- **适用场景**: 复杂的专业文档需求
- **处理流程**:
  1. RAG检索相关资料
  2. 分析用户需求
  3. 智能选择处理策略
  4. 生成专业文档

##### 模式2: 模板插入模式 (`template_insertion`)
- **适用场景**: 基于现有模板填充内容
- **处理流程**:
  1. 解析模板结构
  2. 识别填写字段
  3. 智能匹配内容
  4. 保持原有格式

##### 模式3: 内容合并模式 (`content_merge`)
- **适用场景**: 基于JSON模板生成新文档
- **处理流程**:
  1. 加载JSON模板
  2. 合并检索内容
  3. 重新组织结构
  4. 生成标准文档

#### 配置示例
```json
{
  "template_id": "construction_safety",
  "processing_mode": "professional_agent",
  "output_format": "docx",
  "include_rag": true,
  "professional_field": "construction"
}
```

### 3. RAG检索系统 (`rag_tool_chroma`)

#### 技术架构
- **向量数据库**: ChromaDB
- **向量化模型**: sentence-transformers
- **检索算法**: 余弦相似度
- **存储格式**: SQLite + 向量索引

#### 文档处理流程
1. **文档解析**: 支持PDF、DOC、DOCX、TXT
2. **文本分块**: 智能分段，保持语义完整
3. **向量化**: 转换为高维向量表示
4. **索引存储**: 存储到ChromaDB数据库
5. **元数据管理**: 保存文档来源和属性信息

#### 检索策略
```python
# 检索参数配置
search_params = {
    "query": "用户查询",
    "top_k": 5,              # 返回前5个结果
    "score_threshold": 0.3,   # 相关性阈值
    "include_metadata": True  # 包含元数据
}
```

### 4. 长文档生成 (`advanced_long_document_generator`)

#### 生成流程
1. **需求分析**: 解析用户生成需求
2. **大纲规划**: AI自动生成文档大纲
3. **内容生成**: 分章节生成详细内容
4. **质量检查**: 检查内容质量和格式
5. **文档输出**: 生成DOCX格式文档

#### 支持的文档类型
- **技术方案**: 软件、硬件、系统方案
- **研究报告**: 技术研究、市场分析
- **管理制度**: 企业制度、操作规程
- **项目文档**: 项目计划、实施方案

#### 配置参数
```python
generator_config = {
    "document_type": "technical_report",
    "target_length": 5000,      # 目标字数
    "sections": [               # 章节结构
        "概述", "技术方案", "实施计划", "风险评估", "总结"
    ],
    "professional_field": "construction",
    "output_format": "docx"
}
```

---

## 🔌 API接口

### RESTful API

#### 1. 聊天接口
```http
POST /api/chat
Content-Type: application/json

{
  "message": "用户消息",
  "stream": false
}
```

**响应**:
```json
{
  "success": true,
  "response": "AI回复内容",
  "timestamp": "2025-06-27T10:00:00Z"
}
```

#### 2. 流式聊天接口
```http
POST /api/chat/stream
Content-Type: application/json

{
  "message": "用户消息"
}
```

**响应** (Server-Sent Events):
```
data: {"type": "thinking", "content": "正在思考..."}

data: {"type": "tool_call", "content": "调用RAG工具"}

data: {"type": "content", "content": "生成的内容"}

data: {"type": "complete", "content": "处理完成"}
```

#### 3. 文件上传接口
```http
POST /api/upload
Content-Type: multipart/form-data

file: [文件内容]
```

**响应**:
```json
{
  "success": true,
  "message": "文件处理完成",
  "file_type": "template",
  "saved_path": "templates_storage/example.doc"
}
```

#### 4. 系统状态接口
```http
GET /api/system/status
```

**响应**:
```json
{
  "agent_initialized": true,
  "tools_count": 4,
  "tools": [
    {
      "name": "rag_tool",
      "description": "RAG检索工具"
    }
  ]
}
```

### Python SDK

#### 基本使用
```python
from src.enhanced_react_agent import EnhancedReActAgent
from src.deepseek_client import DeepSeekClient

# 初始化客户端
client = DeepSeekClient(
    api_key="your-api-key",
    base_url="https://api.deepseek.com/v1"
)

# 初始化Agent
agent = EnhancedReActAgent(client)

# 处理请求
response = agent.solve("生成现场复核记录")
print(response)
```

#### 高级配置
```python
# 自定义配置
agent = EnhancedReActAgent(
    deepseek_client=client,
    max_iterations=10,
    verbose=True,
    enable_memory=True,
    memory_file="custom_memory.pkl"
)

# 获取记忆摘要
memory_summary = agent.memory_manager.get_memory_summary()
print(memory_summary)

# 清空记忆
agent.clear_memory()
```

---

## 🔧 故障排除

### 常见问题

#### 1. DeepSeek API连接失败
**错误信息**: `Connection error`

**解决方案**:
1. 检查API密钥配置
2. 确认Base URL正确 (`https://api.deepseek.com/v1`)
3. 检查网络连接
4. 使用独立生成器 `python generate_site_review.py`

**详细排查**: 参考 `DEEPSEEK_CONNECTION_TROUBLESHOOTING.md`

#### 2. 文档转换失败
**错误信息**: `LibreOffice not found`

**解决方案**:
1. 安装LibreOffice
2. 确认安装路径正确
3. 检查文件权限

#### 3. 向量数据库错误
**错误信息**: `ChromaDB connection failed`

**解决方案**:
```bash
# 重新初始化数据库
rm -rf rag_storage/
python -c "from src.rag_tool_chroma import RAGTool; RAGTool().initialize_storage()"
```

#### 4. 内存不足
**错误信息**: `Memory allocation failed`

**解决方案**:
1. 增加系统内存
2. 减少批处理数量
3. 清理临时文件

### 调试工具

#### 1. 系统诊断
```bash
python -c "
import sys
from src.deepseek_client import DeepSeekClient
from src.enhanced_react_agent import EnhancedReActAgent

print('Python版本:', sys.version)
try:
    client = DeepSeekClient()
    print('✅ DeepSeek客户端正常')
    agent = EnhancedReActAgent(client)
    print('✅ ReactAgent正常')
except Exception as e:
    print('❌ 错误:', e)
"
```

#### 2. 工具测试
```bash
python -c "
from src.tools import create_core_tool_registry
tools = create_core_tool_registry()
print('可用工具:')
for tool in tools.list_tools():
    print(f'  - {tool[\"name\"]}: {tool[\"description\"]}')
"
```

#### 3. 日志分析
```bash
# 启用详细日志
export VERBOSE_MODE=true
python web_app.py
```

### 性能优化

#### 1. 缓存配置
```env
# 启用缓存监控
ENABLE_CACHE_MONITORING=true

# 调整缓存大小
CACHE_SIZE=1000
```

#### 2. 并发配置
```python
# 在web_app.py中调整
app.config['THREADED'] = True
app.config['PROCESSES'] = 4
```

#### 3. 数据库优化
```python
# RAG工具配置
rag_config = {
    "batch_size": 100,
    "index_type": "hnsw",
    "memory_limit": "2GB"
}
```

---

## 👨‍💻 开发指南

### 项目结构
```
ReactAgent/
├── src/                          # 源代码目录
│   ├── __init__.py
│   ├── deepseek_client.py        # DeepSeek API客户端
│   ├── enhanced_react_agent.py   # 核心Agent
│   ├── tools.py                 # 工具注册表
│   ├── rag_tool_chroma.py       # RAG工具
│   ├── professional_document_tool.py  # 专业文档工具
│   ├── template_classifier_tool.py    # 模板分类工具
│   └── advanced_long_document_generator_tool.py  # 长文档生成工具
├── templates/                    # 前端模板
│   └── chat.html                # 主界面
├── templates_storage/           # 模板文件存储
├── uploads/                     # 上传文件目录
├── generated_docs/             # 生成文档目录
├── rag_storage/                # RAG数据库存储
├── web_app.py                  # Web应用主文件
├── run_agent.py                # 命令行入口
├── generate_site_review.py     # 现场复核记录生成器
├── requirements.txt            # 依赖配置
├── .env                       # 环境变量配置
└── README.md                  # 项目说明
```

### 开发环境搭建

#### 1. 开发依赖
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖
```

#### 2. 代码规范
- **Python**: 遵循PEP 8规范
- **文档**: 使用Google风格的docstring
- **测试**: 使用pytest进行单元测试

#### 3. 提交规范
```bash
git commit -m "feat: 添加新功能"
git commit -m "fix: 修复bug"
git commit -m "docs: 更新文档"
```

### 自定义工具开发

#### 1. 工具基类
```python
from src.tools import Tool

class CustomTool(Tool):
    def __init__(self):
        super().__init__(
            name="custom_tool",
            description="自定义工具功能描述",
            parameters={
                "input_param": {
                    "type": "string",
                    "description": "输入参数描述"
                }
            }
        )
    
    def execute(self, input_param: str) -> dict:
        """
        执行工具逻辑
        
        Args:
            input_param: 输入参数
            
        Returns:
            dict: 执行结果
        """
        # 实现工具逻辑
        result = self.process_input(input_param)
        
        return {
            "success": True,
            "result": result,
            "message": "处理完成"
        }
    
    def process_input(self, input_param: str) -> str:
        """具体的处理逻辑"""
        return f"处理结果: {input_param}"
```

#### 2. 工具注册
```python
# 在tools.py中注册新工具
from .custom_tool import CustomTool

def create_extended_tool_registry(deepseek_client):
    registry = create_core_tool_registry(deepseek_client)
    
    # 添加自定义工具
    custom_tool = CustomTool()
    registry.register_tool(custom_tool)
    
    return registry
```

#### 3. 工具测试
```python
import unittest
from src.custom_tool import CustomTool

class TestCustomTool(unittest.TestCase):
    def setUp(self):
        self.tool = CustomTool()
    
    def test_execute(self):
        result = self.tool.execute("测试输入")
        self.assertTrue(result["success"])
        self.assertIn("处理结果", result["result"])

if __name__ == '__main__':
    unittest.main()
```

### 前端开发

#### 1. 技术栈
- **HTML5**: 语义化标记
- **CSS3**: 响应式设计，CSS Grid/Flexbox
- **JavaScript**: ES6+，原生JS（无框架依赖）

#### 2. 组件结构
```html
<!-- 主要组件 -->
<div id="chat-container">          <!-- 聊天容器 -->
  <div id="messages"></div>        <!-- 消息列表 -->
  <div id="input-container">       <!-- 输入容器 -->
    <input id="user-input" />      <!-- 用户输入 -->
    <button id="send-btn">发送</button>
  </div>
</div>

<div id="upload-area">             <!-- 上传区域 -->
  <input type="file" id="file-input" />
</div>
```

#### 3. 样式规范
```css
/* 使用CSS变量 */
:root {
  --primary-color: #007bff;
  --secondary-color: #6c757d;
  --success-color: #28a745;
  --warning-color: #ffc107;
  --danger-color: #dc3545;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .container {
    padding: 1rem;
  }
}
```

### API扩展

#### 1. 新增API端点
```python
@app.route('/api/custom', methods=['POST'])
def custom_endpoint():
    try:
        data = request.get_json()
        # 处理逻辑
        result = process_custom_request(data)
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

#### 2. 中间件
```python
@app.before_request
def before_request():
    # 请求前处理
    g.start_time = time.time()

@app.after_request
def after_request(response):
    # 请求后处理
    duration = time.time() - g.start_time
    response.headers['X-Response-Time'] = str(duration)
    return response
```

---

## 📊 性能监控

### 系统指标

#### 1. 性能指标
- **响应时间**: 平均响应时间 < 5秒
- **并发处理**: 支持50+并发用户
- **文档处理**: 单文档处理时间 < 30秒
- **内存使用**: 正常运行内存 < 2GB

#### 2. 监控工具
```python
# 性能监控装饰器
import time
import functools

def monitor_performance(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        print(f"{func.__name__} 执行时间: {end_time - start_time:.2f}秒")
        return result
    return wrapper

# 使用示例
@monitor_performance
def process_document(file_path):
    # 文档处理逻辑
    pass
```

#### 3. 日志配置
```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reactagent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

### 缓存机制

#### 1. DeepSeek缓存
系统自动启用DeepSeek的Context Caching功能：
- 自动缓存重复的prompt内容
- 显著降低API调用成本
- 提高响应速度

#### 2. 文档缓存
```python
# 文档处理结果缓存
from functools import lru_cache

@lru_cache(maxsize=100)
def process_document_cached(file_hash):
    return process_document(file_hash)
```

---

## 🔄 更新日志

### v2.0.0 (2025-06-27)
#### 🎉 新增功能
- ✅ 修复DeepSeek API连接问题
- ✅ 新增独立现场复核记录生成器
- ✅ 完善系统文档和故障排除指南
- ✅ 优化Web界面流式输出体验

#### 🔧 改进
- 📈 提升文档生成质量和速度
- 🔒 增强错误处理和异常恢复
- 📱 优化移动端界面适配
- 🎨 改进AI思考过程可视化

#### 🐛 修复
- 🔧 修复API Base URL配置错误
- 📄 修复DOC文件转换问题
- 🗄️ 修复向量数据库连接异常
- 🔗 修复文件路径处理问题

### v1.5.0 (2025-06-26)
#### 🎉 新增功能
- 🚀 高级长文档生成工具
- 📋 智能模板分类工具
- 🎯 专业文档处理工具
- 🔍 RAG检索系统优化

#### 🔧 改进
- 🧠 增强ReAct推理能力
- 📊 优化工具选择策略
- 💾 改进记忆管理系统
- 🎨 提升界面用户体验

### v1.0.0 (2025-06-20)
#### 🎉 初始版本
- 🤖 基础ReAct Agent框架
- 📚 RAG文档处理功能
- 🌐 Web界面开发
- 🔧 核心工具架构

---

## 📞 技术支持

### 联系方式
- **技术支持**: 通过GitHub Issues提交问题
- **文档更新**: 查看最新版本文档
- **社区讨论**: 参与开发者社区讨论

### 贡献指南
1. Fork项目仓库
2. 创建功能分支 (`git checkout -b feature/new-feature`)
3. 提交更改 (`git commit -am 'Add new feature'`)
4. 推送到分支 (`git push origin feature/new-feature`)
5. 创建Pull Request

### 许可证
本项目采用MIT许可证，详情请参阅LICENSE文件。

---

## 🏆 致谢

感谢以下技术栈和开源项目的支持：
- **DeepSeek AI**: 强大的推理能力
- **ChromaDB**: 高效的向量数据库
- **Flask**: 轻量级Web框架
- **OpenAI**: API接口标准
- **LibreOffice**: 文档格式转换

---

**ReactAgent** - 让文档处理更智能，让工作更高效！ 🚀

*最后更新时间: 2025-06-27* 