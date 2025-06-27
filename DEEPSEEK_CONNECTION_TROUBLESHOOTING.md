# DeepSeek API 连接问题排查指南

## 问题描述
用户在使用 ReactAgent 时遇到 "DeepSeek API 请求失败: Connection error" 错误。

## 问题根因分析

### 1. 主要原因
- **API Base URL 配置错误**: 原始配置为 `https://api.deepseek.com`，缺少 `/v1` 路径
- **网络连接问题**: 网络不稳定或代理配置问题
- **API 密钥配置问题**: 环境变量未正确加载

### 2. 解决方案

#### 方案一：修正 API 配置（已解决）
```bash
# 检查 .env 文件配置
DEEPSEEK_API_KEY=sk-6617ec8529ec49f8a632b7532d2c8760
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1  # 正确的URL，包含/v1
```

#### 方案二：使用独立生成器（推荐）
如果 Web 界面仍有问题，可以使用独立的生成器：

```bash
# 运行独立的现场复核记录生成器
python generate_site_review.py
```

#### 方案三：网络问题排查
1. **检查代理设置**
   ```python
   # 在 DeepSeek 客户端中已经处理了代理问题
   # 会自动移除 ALL_PROXY 环境变量
   ```

2. **测试网络连接**
   ```bash
   # 测试 DeepSeek API 连接
   curl -X POST "https://api.deepseek.com/v1/chat/completions" \
     -H "Authorization: Bearer your-api-key" \
     -H "Content-Type: application/json" \
     -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"Hello"}]}'
   ```

## 快速解决步骤

### 步骤1：检查环境配置
```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('API Key:', os.getenv('DEEPSEEK_API_KEY')[:10] + '...' if os.getenv('DEEPSEEK_API_KEY') else 'Not found')
print('Base URL:', os.getenv('DEEPSEEK_BASE_URL'))
"
```

### 步骤2：使用独立生成器
```bash
# 直接运行现场复核记录生成器
python generate_site_review.py
```

### 步骤3：检查生成结果
```bash
# 查看生成的文档
dir generated_docs
```

## 已验证的解决方案

### ✅ 已修复的问题
1. **API Base URL**: 已从 `https://api.deepseek.com` 修正为 `https://api.deepseek.com/v1`
2. **代理处理**: DeepSeek 客户端已处理代理冲突
3. **独立生成器**: 创建了 `generate_site_review.py` 作为备用方案

### ✅ 测试结果
- DeepSeek API 连接正常
- 现场复核记录生成成功
- 文档保存路径：`generated_docs/template_inserted_现场复核记录_TIMESTAMP.docx`

## 预防措施

### 1. 定期检查环境配置
```bash
# 创建检查脚本
python -c "
from src.deepseek_client import DeepSeekClient
try:
    client = DeepSeekClient()
    response = client.generate_response('Test')
    print('✅ DeepSeek API 连接正常')
except Exception as e:
    print(f'❌ 连接失败: {e}')
"
```

### 2. 备用方案
- 使用独立生成器 `generate_site_review.py`
- 检查网络连接状态
- 确认 API 密钥有效性

### 3. 错误监控
- 在 Web 应用中添加详细的错误日志
- 实现自动重试机制
- 提供用户友好的错误提示

## 联系支持

如果问题仍然存在，请提供以下信息：
1. 错误日志的完整输出
2. 网络环境信息
3. DeepSeek API 密钥状态
4. 操作系统和 Python 版本

## 文档更新记录
- 2025-06-27: 初始版本，解决了 Base URL 配置问题
- 2025-06-27: 添加了独立生成器作为备用方案
- 2025-06-27: 验证了解决方案的有效性 