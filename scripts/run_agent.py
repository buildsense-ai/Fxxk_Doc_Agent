#!/usr/bin/env python3
"""
Enhanced ReAct Agent - 核心三工具架构版本
运行增强版ReAct智能体，专注于文档处理的三个核心工具
"""

import sys
import os
import argparse

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from enhanced_react_agent import EnhancedReActAgent
from deepseek_client import DeepSeekClient
from tools import create_core_tool_registry

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Enhanced ReAct Agent - 核心三工具架构")
    parser.add_argument("--task", type=str, help="要执行的单个任务")
    args = parser.parse_args()

    print("🚀 启动Enhanced ReAct Agent - 核心三工具架构")
    print("=" * 60)
    
    # 初始化DeepSeek客户端
    try:
        deepseek_client = DeepSeekClient()
        print("✅ DeepSeek AI客户端初始化成功")
    except Exception as e:
        print(f"⚠️ DeepSeek AI客户端初始化失败: {e}")
        print("💡 将使用基础模式运行（无AI增强功能）")
        deepseek_client = None
    
    # 创建核心工具注册表
    print("\n🔧 初始化核心三工具架构...")
    tool_registry = create_core_tool_registry(deepseek_client)
    
    # 显示工具摘要
    print("\n" + tool_registry.get_tool_summary())
    
    # 初始化增强版ReAct Agent
    print("\n🤖 初始化Enhanced ReAct Agent...")
    agent = EnhancedReActAgent(
        deepseek_client=deepseek_client,
        tool_registry=tool_registry,
        verbose=True  # 启用详细输出
    )
    
    print("\n" + "=" * 60)
    print("🎯 Enhanced ReAct Agent 已启动！")
    
    if args.task:
        print(f"🔄 正在执行任务: {args.task}")
        print("-" * 50)
        response = agent.solve(args.task)
        print("-" * 50)
        print(f"🤖 Agent回复:\n{response}")
        return

    print("\n📋 核心三工具架构说明:")
    print("1️⃣ rag_tool - 文档embedding处理和智能搜索")
    print("2️⃣ template_processor - 模板字段提取")
    print("3️⃣ document_generator_new - 最终文档生成")
    
    print("\n💡 使用示例:")
    print("- 上传资料: '请上传test/会议纪要.docx到RAG系统'")
    print("- 处理模板: '请处理test/template.docx模板文件'")
    print("- 生成文档: '基于模板和资料生成最终文档'")
    print("- 查看工具: '列出所有可用工具'")
    print("- 退出系统: 'quit' 或 'exit'")
    
    print("\n" + "=" * 60)
    
    # 主交互循环
    while True:
        try:
            # 获取用户输入
            user_input = input("\n🤔 请输入您的问题或需求: ").strip()
            
            # 检查退出命令
            if user_input.lower() in ['quit', 'exit', '退出', 'q']:
                print("\n👋 感谢使用Enhanced ReAct Agent！")
                break
            
            # 检查空输入
            if not user_input:
                print("⚠️ 请输入有效的问题或需求")
                continue
            
            # 检查帮助命令
            if user_input.lower() in ['help', '帮助', 'h']:
                continue
            
            # 处理用户请求
            print(f"\n🔄 处理中: {user_input}")
            print("-" * 50)
            
            response = agent.solve(user_input)
            
            print("-" * 50)
            print(f"🤖 Agent回复:\n{response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 用户中断，退出系统")
            break
        except Exception as e:
            print(f"\n❌ 处理过程中出现错误: {e}")
            print("💡 请重新输入您的问题")

if __name__ == "__main__":
    main() 