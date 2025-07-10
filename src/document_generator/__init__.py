#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文档生成工具包

提供AI自动化文档生成功能
"""

from .document_generator_tool import DocumentGeneratorTool

__all__ = ['DocumentGeneratorTool']

def create_document_generator_tool():
    """创建文档生成工具实例"""
    return DocumentGeneratorTool() 