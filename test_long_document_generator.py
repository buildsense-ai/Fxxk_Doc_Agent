#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试长文档生成工具
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.mcp_demo_tool import LongDocumentGeneratorTool
import json
import time

def test_long_document_generator_tool():
    """测试长文档生成工具的基本功能"""
    
    # 创建工具实例
    tool = LongDocumentGeneratorTool()
    
    print("=== 长文档生成工具测试 ===\n")
    
    # 1. 测试错误处理
    print("1. 测试错误处理:")
    result = tool.execute("invalid_action")
    print(result)
    print("\n" + "="*50 + "\n")
    
    # 2. 测试列出任务（应该为空）
    print("2. 列出任务（初始状态）:")
    result = tool.execute("list_tasks")
    print(result)
    print("\n" + "="*50 + "\n")
    
    # 3. 测试生成短文档
    print("3. 测试短文档生成:")
    chathistory = "用户：我需要一个关于人工智能的报告\n助手：好的，我来帮您生成一个AI技术报告"
    request = "请生成一个关于人工智能技术发展现状的短篇报告，包括技术现状、应用领域、发展趋势等内容"
    
    result = tool.execute("generate_short_document", 
                         chathistory=chathistory, 
                         request=request)
    print(result)
    
    # 从结果中提取任务ID
    task_id = None
    lines = result.split('\n')
    for line in lines:
        if "任务ID" in line:
            task_id = line.split(": ")[1].strip()
            break
    
    print(f"\n提取的任务ID: {task_id}")
    print("\n" + "="*50 + "\n")
    
    # 4. 测试查询状态
    if task_id:
        print("4. 测试查询状态:")
        result = tool.execute("check_generation_status", task_id=task_id)
        print(result)
        print("\n" + "="*50 + "\n")
        
        # 5. 等待一段时间后再次查询
        print("5. 等待5秒后再次查询状态:")
        time.sleep(5)
        result = tool.execute("check_generation_status", task_id=task_id)
        print(result)
        print("\n" + "="*50 + "\n")
    
    # 6. 测试生成长文档
    print("6. 测试长文档生成:")
    chathistory_long = "用户：我需要一个详细的技术分析报告\n助手：好的，我来帮您生成一个详细的技术分析报告"
    request_long = "请生成一个详细的人工智能技术发展趋势分析报告，包括技术背景、现状分析、发展趋势、应用案例、挑战与机遇等完整内容"
    
    result = tool.execute("generate_long_document", 
                         chathistory=chathistory_long, 
                         request=request_long)
    print(result)
    
    # 从结果中提取任务ID
    task_id_long = None
    lines = result.split('\n')
    for line in lines:
        if "任务ID" in line:
            task_id_long = line.split(": ")[1].strip()
            break
    
    print(f"\n提取的长文档任务ID: {task_id_long}")
    print("\n" + "="*50 + "\n")
    
    # 7. 再次列出任务
    print("7. 列出所有任务:")
    result = tool.execute("list_tasks")
    print(result)
    print("\n" + "="*50 + "\n")
    
    # 8. 测试获取任务结果（应该显示未完成）
    if task_id:
        print("8. 测试获取任务结果（短文档）:")
        result = tool.execute("get_task_result", task_id=task_id)
        print(result)
        print("\n" + "="*50 + "\n")
    
    # 9. 测试查询不存在的任务
    print("9. 测试查询不存在的任务:")
    result = tool.execute("check_generation_status", task_id="nonexistent-task-id")
    print(result)
    print("\n" + "="*50 + "\n")
    
    # 10. 测试工具描述
    print("10. 工具描述:")
    print(f"工具名称: {tool.name}")
    print(f"工具描述: {tool.description[:200]}...")

if __name__ == "__main__":
    test_long_document_generator_tool() 