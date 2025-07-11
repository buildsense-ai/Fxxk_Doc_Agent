# RAG工具调用方法

## 🚀 基本调用

### 1. 初始化RAG工具

```python
from src.rag_tool_chroma import RAGTool

# 初始化RAG工具
rag = RAGTool(storage_dir="rag_storage")
```

## 📖 核心操作

### 2. 文档搜索

```python
# 基础搜索
results = rag.execute("search", query="医灵古庙", top_k=5)

# 带项目过滤的搜索
results = rag.execute("search", query="建筑设计", top_k=3, project_name="可塞古庙项目")

# 只搜索指定项目的内容
results = rag.execute("search", query="", top_k=10, project_name="医灵古庙保护项目")
```

### 3. 图片搜索

```python
# 搜索相关图片
image_results = rag.execute("search_images", query="古庙建筑", top_k=8)

# 统计图片数量
image_count = rag.execute("count_images", query="医灵古庙")
```

### 4. 表格搜索

```python
# 搜索表格数据
table_results = rag.execute("search_tables", query="影响评估", top_k=5)

# 统计表格数量
table_count = rag.execute("count_tables", query="评估标准")
```

### 5. 文档上传

```python
# 上传单个文档
result = rag.execute("upload", file_path="path/to/document.pdf")

# 处理PDF解析后的文件夹
result = rag.execute("process_parsed_folder", 
                    folder_path="parser_output/document_analysis", 
                    project_name="医灵古庙保护项目")
```

### 6. 项目搜索

```python
# 搜索指定项目的所有内容
results = rag.execute("search", query="", top_k=20, project_name="医灵古庙保护项目")

# 在指定项目中搜索关键词
results = rag.execute("search", query="建筑风格", top_k=5, project_name="可塞古庙项目")

# 搜索指定项目的图片
images = rag.execute("search_images", query="古庙", top_k=10, project_name="医灵古庙保护项目")

# 搜索指定项目的表格
tables = rag.execute("search_tables", query="评估", top_k=5, project_name="可塞古庙项目")
```

### 7. 数据管理

```python
# 列出所有文档
documents = rag.execute("list")

# 清空所有数据
rag.execute("clear")
```

## 🎯 支持的操作类型

| 操作 | 说明 | 示例 |
|------|------|------|
| `search` | 通用搜索 | `rag.execute("search", query="关键词", top_k=5)` |
| `search_images` | 图片搜索 | `rag.execute("search_images", query="图片描述", top_k=8)` |
| `search_tables` | 表格搜索 | `rag.execute("search_tables", query="表格内容", top_k=5)` |
| `count_images` | 统计图片 | `rag.execute("count_images", query="关键词")` |
| `count_tables` | 统计表格 | `rag.execute("count_tables", query="关键词")` |
| `upload` | 上传文档 | `rag.execute("upload", file_path="文档路径")` |
| `list` | 列出文档 | `rag.execute("list")` |
| `clear` | 清空数据 | `rag.execute("clear")` |
| `process_parsed_folder` | 处理解析文件夹 | `rag.execute("process_parsed_folder", folder_path="路径")` |

## 📋 常用参数

- `query`: 搜索关键词（可为空字符串""）
- `top_k`: 返回结果数量（默认5）
- `project_name`: 项目名称过滤，只搜索指定项目的内容
- `file_path`: 文件路径
- `folder_path`: 文件夹路径

### 🎯 项目名称使用说明

- **指定项目搜索**: `project_name="医灵古庙保护项目"`
- **搜索所有项目**: 不传project_name参数或传None
- **获取项目所有内容**: 使用空查询 `query=""` + `project_name="项目名"`

## 💡 使用示例

```python
from src.rag_tool_chroma import RAGTool

# 初始化
rag = RAGTool()

# 上传文档
rag.execute("upload", file_path="古庙设计方案.pdf")

# 搜索文档
results = rag.execute("search", query="古庙建筑风格", top_k=5)
print(f"找到 {len(results)} 条相关文档")

# 搜索指定项目的内容
project_results = rag.execute("search", query="建筑设计", top_k=5, project_name="医灵古庙保护项目")
print(f"在项目中找到 {len(project_results)} 条相关文档")

# 获取指定项目的所有内容
all_project_content = rag.execute("search", query="", top_k=50, project_name="医灵古庙保护项目")
print(f"项目总共有 {len(all_project_content)} 条内容")

# 搜索图片
images = rag.execute("search_images", query="古庙外观", top_k=3)
print(f"找到 {len(images)} 张相关图片")

# 搜索指定项目的图片
project_images = rag.execute("search_images", query="古庙", top_k=10, project_name="医灵古庙保护项目")
print(f"项目中找到 {len(project_images)} 张相关图片")

# 统计数据
image_count = rag.execute("count_images", query="古庙")
print(f"古庙相关图片共 {image_count} 张")
``` 