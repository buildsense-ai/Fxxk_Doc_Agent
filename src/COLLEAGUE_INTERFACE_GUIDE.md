# Professional Agent Tool - Interface Guide for Colleagues

## 📝 **What Your Colleague Needs to Provide**

Your original thought was **mostly correct** but missing 2 required parameters. Here's the complete interface:

### ✅ **Required Inputs**

```python
from professional_tool_agent_function import run_professional_tool_agent

result = run_professional_tool_agent(
    user_request="Generate a construction safety plan with risk assessment",     # ✅ Your "quest"
    context="Project details and background information",                       # ✅ Your "context" 
    template_id="construction_safety",                                          # ⚠️ MISSING in your list
    original_file_path="templates/safety_template.doc",                        # ✅ Your "template doc file"
    api_key="your-openrouter-api-key",                                         # ⚠️ MISSING in your list
    session_id="optional_session_001"                                          # Optional
)
```

## 📋 **Parameter Details**

### 1. `user_request` (str) - Your "quest" ✅
**What it is**: The user's request/query describing what they want to generate

**Examples**:
```python
"生成一份施工组织设计方案，重点包含安全措施和质量控制要求"
"Create a construction safety management plan with risk assessment"
"Generate building permit application documentation"
```

### 2. `context` (str) - Your "context" ✅  
**What it is**: Background information and project details

**Can be**: Plain text or JSON string

**Examples**:
```python
# Plain text
context = """
Project Name: Heritage Building Restoration
Location: Beijing Dongcheng District  
Project Type: Cultural Heritage Protection
Special Requirements: Fire safety, structural reinforcement
"""

# JSON format (recommended)
context = json.dumps({
    "project_name": "古建筑保护修缮工程",
    "project_type": "文物保护建筑", 
    "location": "北京市东城区",
    "requirements": ["文物保护", "安全施工", "质量控制"],
    "special_considerations": ["文物价值保护", "施工安全", "环境保护"]
}, ensure_ascii=False)
```

### 3. `template_id` (str) - ⚠️ **MISSING from your list**
**What it is**: Template identifier for RAG search and template management

**Available options**:
```python
"construction_organization_design"              # 施工组织设计
"heritage_building_comprehensive_plan_v2.1"    # 古建筑综合方案  
"construction_safety"                           # 施工安全方案
"default"                                       # 默认模板
```

### 4. `original_file_path` (str) - Your "template doc file" ✅
**What it is**: Path to the Word template file (.doc or .docx)

**Examples**:
```python
"templates/construction_template.doc"
"safety_plan_template.docx" 
"施工组织设计模板.doc"
```

**⚠️ Important**: If this is a `.doc`/`.docx` file, it will use **Template Insertion Mode** (preserves structure). If it's any other file type, it will use **Content Generation Mode**.

### 5. `api_key` (str) - ⚠️ **MISSING from your list**  
**What it is**: OpenRouter API key for AI processing

**How to get**: Your colleague needs their own OpenRouter API key from https://openrouter.ai/

**Usage**:
```python
api_key = "sk-or-v1-your-colleague-api-key",
```

### 6. `session_id` (Optional[str]) - Optional
**What it is**: Session identifier for tracking (optional)

**Examples**:
```python
session_id = "user_session_20250626_001"
session_id = None  # Can be omitted
```

## 🔄 **What Your Colleague Gets Back**

```python
{
    "status": "success",                    # success/need_more_info/error
    "output_path": "generated_docs/...",    # Path to generated document
    "missing_fields": [],                   # List of fields that need more info
    "message": "Word模板插入完成，原始结构已保持",
    "metadata": {
        "template_id": "construction_safety",
        "processing_mode": "template_insertion",  # or "content_merger"
        "template_file_used": "template.doc",
        "completion_rate": 0.95,
        "rag_results_count": 3
    },
    "session_id": "user_session_001",
    "timestamp": "2025-06-26T16:18:07.886"
}
```

## 💡 **Summary: What Was Missing**

Your original thought: **"template doc file, quest, context"** ✅

**What you missed**:
1. `template_id` - Required for RAG search and template selection
2. `api_key` - Required for AI processing

**Complete list**:
1. ✅ Template doc file (`original_file_path`)
2. ✅ Quest (`user_request`) 
3. ✅ Context (`context`)
4. ⚠️ Template ID (`template_id`)
5. ⚠️ API Key (`api_key`)
6. 🔲 Session ID (`session_id`) - Optional

## 🚀 **Simple Example for Your Colleague**

```python
from professional_tool_agent_function import run_professional_tool_agent

# Your colleague's code:
result = run_professional_tool_agent(
    user_request="Generate safety documentation for construction project",
    context=json.dumps({
        "project_name": "Modern Office Building",
        "location": "Shanghai Pudong",
        "project_type": "Commercial Construction"
    }),
    template_id="construction_safety", 
    original_file_path="my_template.doc",  # Their Word template
    api_key="sk-or-v1-their-api-key",     # Their API key
    session_id="project_001"               # Optional
)

print(f"Status: {result['status']}")
print(f"Generated file: {result['output_path']}")
```

## ⚡ **Quick Setup Checklist for Colleague**

- [ ] Word template file ready (`.doc` or `.docx`)
- [ ] OpenRouter API key obtained
- [ ] Template ID chosen from available options
- [ ] User request prepared
- [ ] Context information gathered (preferably in JSON format)
- [ ] Python environment with required packages installed 