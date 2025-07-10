#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试文档生成工具
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.document_generator import DocumentGeneratorTool
import time

def test_document_generator():
    """测试文档生成工具"""
    
    print("=== 文档生成工具测试 ===\n")
    
    # 创建工具实例
    tool = DocumentGeneratorTool()
    
    # 1. 测试工具信息
    print("1. 工具信息:")
    print(f"工具名称: {tool.name}")
    print(f"工具描述: {tool.description[:200]}...")
    print("\n" + "="*50 + "\n")
    
    # 2. 测试错误处理
    print("2. 测试错误处理:")
    result = tool.execute("invalid_action")
    print(result)
    print("\n" + "="*50 + "\n")
    
    # 3. 测试列出任务（初始状态）
    print("3. 列出任务（初始状态）:")
    result = tool.execute("list_tasks")
    print(result)
    print("\n" + "="*50 + "\n")
    
    # 4. 测试生成短文档
    print("4. 测试短文档生成:")
    chathistory = """用户: 我需要一个关于人工智能发展的报告
助手: 好的，我来帮您生成一个AI发展报告"""
    
    request = """请生成一个关于人工智能技术发展现状的报告，包括：
1. 技术发展历程
2. 当前主要应用领域
3. 未来发展趋势
4. 面临的挑战与机遇
要求内容详实，逻辑清晰，字数控制在2000字以内。"""
    
    result = tool.execute("generate_short_document", 
                         chathistory=chathistory, 
                         request=request)
    print(result)
    
    # 提取任务ID
    task_id = None
    lines = result.split('\n')
    for line in lines:
        if "任务ID" in line and ":" in line:
            task_id = line.split(": ")[1].strip()
            break
    
    print(f"\n提取的任务ID: {task_id}")
    print("\n" + "="*50 + "\n")
    
    # 5. 测试查询状态
    if task_id:
        print("5. 查询任务状态:")
        result = tool.execute("check_status", task_id=task_id)
        print(result)
        print("\n" + "="*50 + "\n")
        
        # 6. 等待片刻后再次查询
        print("6. 等待3秒后再次查询状态:")
        time.sleep(3)
        result = tool.execute("check_status", task_id=task_id)
        print(result)
        print("\n" + "="*50 + "\n")
        
        # 7. 测试获取结果
        print("7. 测试获取任务结果:")
        result = tool.execute("get_result", task_id=task_id)
        print(result)
        print("\n" + "="*50 + "\n")
    
    # 8. 测试生成长文档
    print("8. 测试长文档生成:")
    long_request = """请生成一份详细的《人工智能技术发展趋势分析报告》，包括：
1. 引言与背景
2. 技术发展历程回顾
3. 当前技术现状分析
4. 主要应用领域深度解析
5. 未来发展趋势预测
6. 技术挑战与解决方案
7. 政策环境与产业前景
8. 结论与建议

要求：
- 内容详实，数据准确
- 结构清晰，逻辑严谨
- 分析深入，见解独到
- 总字数8000-12000字"""
    
    result = tool.execute("generate_long_document", 
                         chathistory=chathistory, 
                         request=long_request)
    print(result)
    print("\n" + "="*50 + "\n")
    
    # 9. 再次列出任务
    print("9. 列出所有任务:")
    result = tool.execute("list_tasks")
    print(result)
    print("\n" + "="*50 + "\n")
    
    # 10. 测试查询不存在的任务
    print("10. 测试查询不存在的任务:")
    result = tool.execute("check_status", task_id="nonexistent-task")
    print(result)

if __name__ == "__main__":
    test_document_generator() 