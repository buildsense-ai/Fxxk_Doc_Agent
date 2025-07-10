#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文档生成工具 - 基于AI的智能文档生成系统

这个工具专注于AI自动化文档生成功能
"""

from .document_generator import DocumentGeneratorTool

# 为了保持向后兼容，使用新的工具类
class DocumentGeneratorToolWrapper(DocumentGeneratorTool):
    """文档生成工具 - 兼容性包装"""
    pass

# 创建工具实例的函数
def create_document_generator_tool():
    """创建文档生成工具实例"""
    return DocumentGeneratorToolWrapper()

# 为了兼容性，保留旧的函数名
def create_mcp_demo_tool():
    """创建MCP Demo工具实例（已重定向到文档生成工具）"""
    return DocumentGeneratorToolWrapper()

def create_long_document_generator_tool():
    """创建长文档生成工具实例（已重定向到文档生成工具）"""
    return DocumentGeneratorToolWrapper() 