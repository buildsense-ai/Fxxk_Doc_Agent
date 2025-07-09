"""
图片RAG系统

这个包包含了完整的图片检索增强生成功能，包括：
- 图片上传和存储管理
- BGE-M3高质量文本嵌入
- Gemini 2.5 Pro AI描述生成
- ChromaDB向量数据库
- 语义相似度搜索
- MinIO对象存储
- Web界面管理
"""

__version__ = "2.0.0"
__author__ = "Image RAG Team"

# 系统组件
COMPONENTS = [
    "✅ 文本描述嵌入",
    "✅ AI图片描述生成", 
    "✅ 语义搜索",
    "✅ ChromaDB持久化",
    "✅ SQLite数据库持久化",
    "✅ MinIO对象存储",
    "✅ Web管理界面"
]

__all__ = [
    'COMPONENTS'
] 