# OpenRouter解析智能体使用指南

这个版本支持使用OpenRouter上的多种模型来解析PDF论文。

## 🚀 快速开始

### 1. 获取OpenRouter API密钥
1. 访问 [OpenRouter官网](https://openrouter.ai/)
2. 注册账号并获取API密钥
3. 充值账户

### 2. 设置环境变量
```bash
# 设置OpenRouter API密钥
echo "OPENAI_API_KEY=sk-or-your-key-here" > .env
```

### 3. 查看可用模型
```bash
python parser_agent_openrouter.py --list-models
```

### 4. 测试解析
```bash
# 使用GPT-4o解析
python parser_agent_openrouter.py your_paper.pdf --model gpt-4o

# 使用Claude解析
python parser_agent_openrouter.py your_paper.pdf --model claude-3.5-sonnet

# 使用开源模型解析
python parser_agent_openrouter.py your_paper.pdf --model qwen2.5-7b
```

## 📋 支持的模型

### OpenAI模型
- `gpt-4o` - GPT-4o (推荐)
- `gpt-4o-mini` - GPT-4o Mini (经济型)
- `gpt-3.5-turbo` - GPT-3.5-turbo (最便宜)

### Anthropic模型
- `claude-3.5-sonnet` - Claude 3.5 Sonnet
- `claude-3-haiku` - Claude 3 Haiku

### Meta模型
- `llama-3.1-8b` - Llama 3.1 8B
- `llama-3.1-70b` - Llama 3.1 70B

### Google模型
- `gemini-pro` - Gemini Pro

### 开源模型
- `qwen2.5-7b` - Qwen 2.5 7B
- `qwen2.5-32b` - Qwen 2.5 32B

## 💰 成本对比

| 模型 | 输入价格 | 输出价格 | 推荐度 |
|------|----------|----------|--------|
| gpt-3.5-turbo | $0.0015/1K | $0.002/1K | ⭐⭐⭐⭐ |
| gpt-4o-mini | $0.00015/1K | $0.0006/1K | ⭐⭐⭐⭐⭐ |
| claude-3-haiku | $0.00025/1K | $0.00125/1K | ⭐⭐⭐⭐ |
| qwen2.5-7b | $0.0002/1K | $0.0002/1K | ⭐⭐⭐ |
| gpt-4o | $0.0025/1K | $0.01/1K | ⭐⭐⭐⭐ |

## 🛠️ 使用示例

### 命令行使用
```bash
# 基本使用
python parser_agent_openrouter.py paper.pdf

# 指定模型和输出目录
python parser_agent_openrouter.py paper.pdf --model claude-3.5-sonnet --output_dir my_output

# 详细输出
python parser_agent_openrouter.py paper.pdf --model gpt-4o --verbose

# 列出所有可用模型
python parser_agent_openrouter.py --list-models
```

### Python代码中使用
```python
from parser_agent_openrouter import OpenRouterParserAgent

# 创建解析智能体
parser = OpenRouterParserAgent(model_name="gpt-4o")

# 解析PDF
content_json, images, tables = parser.parse_raw("paper.pdf", "output_dir")

# 获取统计信息
stats = parser.get_parsing_stats(content_json, images, tables)
print(f"使用模型: {stats['model_used']}")
print(f"Sections数量: {stats['sections_count']}")
```

## 🔧 配置说明

### 环境变量
```bash
# 必需
OPENAI_API_KEY=sk-or-your-key-here

# 可选 (如果使用其他OpenAI兼容服务)
OPENAI_BASE_URL=https://openrouter.ai/api/v1
```

### 模型选择建议

**经济型** (推荐新手):
```bash
python parser_agent_openrouter.py paper.pdf --model gpt-4o-mini
```

**平衡型** (推荐日常使用):
```bash
python parser_agent_openrouter.py paper.pdf --model gpt-4o
```

**高性能** (重要论文):
```bash
python parser_agent_openrouter.py paper.pdf --model claude-3.5-sonnet
```

**开源** (本地部署):
```bash
python parser_agent_openrouter.py paper.pdf --model qwen2.5-7b
```

## 📊 输出结果

解析完成后，您会得到：

1. **parsed_content.json** - 结构化内容
2. **images.json** - 图片信息
3. **tables.json** - 表格信息
4. **summary.json** - 汇总信息（包含使用的模型）

### 示例输出
```json
{
  "total_sections": 5,
  "total_images": 3,
  "total_tables": 2,
  "model_used": "gpt-4o",
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

## ⚠️ 注意事项

1. **API密钥**: 确保使用正确的OpenRouter API密钥
2. **账户余额**: 确保账户有足够余额
3. **模型可用性**: 某些模型可能暂时不可用
4. **网络连接**: 需要稳定的网络连接
5. **文件大小**: 建议PDF文件不超过50MB

## 🔍 故障排除

### 常见问题

1. **API密钥错误**
   ```bash
   # 检查密钥格式
   echo $OPENAI_API_KEY
   # 应该以 sk-or- 开头
   ```

2. **模型不可用**
   ```bash
   # 查看可用模型
   python parser_agent_openrouter.py --list-models
   ```

3. **余额不足**
   - 访问 [OpenRouter控制台](https://openrouter.ai/keys) 充值

4. **网络问题**
   - 检查网络连接
   - 尝试使用VPN

## 💡 使用技巧

1. **首次测试**: 使用 `gpt-4o-mini` 进行快速测试
2. **重要论文**: 使用 `gpt-4o` 或 `claude-3.5-sonnet` 获得更好效果
3. **批量处理**: 可以编写脚本批量处理多个PDF
4. **成本控制**: 使用 `--verbose` 查看token使用量

## 📞 支持

如果遇到问题：
1. 检查OpenRouter账户状态
2. 查看模型可用性
3. 确认API密钥正确
4. 检查网络连接

更多信息请访问 [OpenRouter文档](https://openrouter.ai/docs)。 