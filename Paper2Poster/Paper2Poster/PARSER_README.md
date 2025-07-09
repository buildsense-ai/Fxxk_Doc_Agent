# 解析智能体独立接口

这是Paper2Poster项目中解析智能体的独立接口，可以单独使用来解析PDF论文并提取结构化信息。

## 📁 文件说明

- `parser_agent_standalone.py` - 完整的解析智能体实现
- `test_parser_simple.py` - 简化的测试脚本
- `parser_api.py` - API接口，方便集成使用

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

### 2. 简单测试

```bash
# 将PDF文件放在当前目录下
python test_parser_simple.py
```

### 3. 命令行使用

```bash
# 使用完整接口
python parser_agent_standalone.py your_paper.pdf --output_dir output --model 4o

# 使用API接口
python parser_api.py your_paper.pdf --model 4o --simple
```

## 📖 API使用示例

### 基本用法

```python
from parser_api import parse_pdf, parse_pdf_simple, get_sections, get_meta_info

# 完整解析
result = parse_pdf("paper.pdf", model_name="4o")
print(f"Sections数量: {result['stats']['sections_count']}")
print(f"图片数量: {result['stats']['images_count']}")

# 简化解析
simple_result = parse_pdf_simple("paper.pdf")
sections = simple_result['content']['sections']
for section in sections:
    print(f"标题: {section['title']}")

# 只获取sections
sections = get_sections("paper.pdf")

# 只获取元信息
meta = get_meta_info("paper.pdf")
print(f"论文标题: {meta.get('poster_title')}")
```

### 高级用法

```python
from parser_api import ParserAPI

# 创建API实例
api = ParserAPI(model_name="4o")

# 解析PDF
result = api.parse_pdf("paper.pdf", output_dir="my_output")

# 提取图片和表格
figures = api.extract_figures("paper.pdf")
print(f"图片: {len(figures['images'])} 个")
print(f"表格: {len(figures['tables'])} 个")

# 获取特定信息
sections = api.get_sections("paper.pdf")
meta = api.get_meta_info("paper.pdf")
```

## 📊 输出格式

### 结构化内容 (parsed_content.json)

```json
{
    "meta": {
        "poster_title": "论文标题",
        "authors": "作者信息",
        "affiliations": "机构信息"
    },
    "sections": [
        {
            "title": "Poster Title & Author",
            "content": "海报标题和作者内容"
        },
        {
            "title": "Introduction",
            "content": "引言部分内容"
        },
        {
            "title": "Methodology",
            "content": "方法部分内容"
        }
    ]
}
```

### 图片信息 (images.json)

```json
{
    "1": {
        "caption": "图片标题",
        "image_path": "picture-1.png",
        "width": 800,
        "height": 600,
        "figure_size": 480000,
        "figure_aspect": 1.33
    }
}
```

### 表格信息 (tables.json)

```json
{
    "1": {
        "caption": "表格标题",
        "table_path": "table-1.png",
        "width": 600,
        "height": 400,
        "figure_size": 240000,
        "figure_aspect": 1.5
    }
}
```

### 汇总信息 (summary.json)

```json
{
    "total_sections": 5,
    "total_images": 3,
    "total_tables": 2,
    "meta_info": {
        "poster_title": "论文标题",
        "authors": "作者信息"
    },
    "section_titles": [
        "Poster Title & Author",
        "Introduction",
        "Methodology",
        "Results",
        "Conclusion"
    ]
}
```

## 🔧 配置选项

### 支持的模型

- `4o` (默认) - GPT-4o
- `4o-mini` - GPT-4o Mini
- `gpt-4.1` - GPT-4.1
- `vllm_qwen` - Qwen (需要本地vLLM服务)

### 环境变量

```bash
# 必需
OPENAI_API_KEY=your_openai_api_key

# 可选
OPENAI_BASE_URL=https://api.openai.com/v1  # 自定义API地址
```

## 🛠️ 自定义配置

### 修改解析参数

```python
from parser_agent_standalone import ParserAgent

# 创建自定义解析智能体
parser = ParserAgent(model_name="4o")

# 解析PDF
content_json, images, tables = parser.parse_raw("paper.pdf", "output_dir")

# 获取统计信息
stats = parser.get_parsing_stats(content_json, images, tables)
print(f"解析统计: {stats}")
```

### 错误处理

```python
from parser_api import parse_pdf

try:
    result = parse_pdf("paper.pdf")
    if result['success']:
        print("解析成功")
    else:
        print("解析失败")
except FileNotFoundError:
    print("PDF文件不存在")
except ImportError:
    print("依赖包未安装")
except Exception as e:
    print(f"解析错误: {e}")
```

## 📝 注意事项

1. **API密钥**: 确保设置了正确的OpenAI API密钥
2. **文件格式**: 支持标准PDF格式，建议使用文本可选择的PDF
3. **文件大小**: 建议PDF文件大小不超过50MB
4. **网络连接**: 需要稳定的网络连接访问OpenAI API
5. **依赖包**: 确保安装了所有必要的Python包

## 🔍 故障排除

### 常见问题

1. **导入错误**
   ```bash
   pip install -r requirements.txt
   ```

2. **API密钥错误**
   ```bash
   echo "OPENAI_API_KEY=your_key" > .env
   ```

3. **PDF解析失败**
   - 检查PDF文件是否损坏
   - 尝试使用不同的PDF文件
   - 检查PDF是否为扫描版（需要OCR）

4. **内存不足**
   - 减少图片分辨率设置
   - 使用更小的PDF文件

### 调试模式

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from parser_api import parse_pdf
result = parse_pdf("paper.pdf")
```

## 📞 支持

如果遇到问题，请检查：

1. 依赖包是否正确安装
2. 环境变量是否正确设置
3. PDF文件是否有效
4. 网络连接是否正常

更多信息请参考Paper2Poster项目文档。 