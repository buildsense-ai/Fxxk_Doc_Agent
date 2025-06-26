#!/usr/bin/env python3
"""
测试ReactAgent是否能正确区分模板文档和长文档
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_document_type_detection():
    """测试Agent是否能正确区分文档类型"""
    print("🧪 测试ReactAgent文档类型判断")
    print("=" * 50)
    
    try:
        from src.enhanced_react_agent import EnhancedReActAgent
        from src.deepseek_client import DeepSeekClient
        from src.tools import create_core_tool_registry
        
        # 初始化组件
        print("🔧 初始化组件...")
        deepseek_client = DeepSeekClient()
        tool_registry = create_core_tool_registry(deepseek_client)
        agent = EnhancedReActAgent(
            deepseek_client=deepseek_client,
            tool_registry=tool_registry,
            verbose=True,
            max_iterations=2  # 限制迭代次数用于测试
        )
        
        # 测试用例 - 模板文档 vs 长文档
        test_cases = [
            # 模板文档类型
            {
                'query': '帮我生成春香园复核记录',
                'expected_tool': 'template_conversion', 
                'document_type': '模板文档',
                'reason': '包含"复核记录"关键词'
            },
            {
                'query': '生成施工现场检查记录表',
                'expected_tool': 'template_conversion',
                'document_type': '模板文档', 
                'reason': '包含"检查记录"关键词'
            },
            {
                'query': '创建材料进场验收记录',
                'expected_tool': 'template_conversion',
                'document_type': '模板文档',
                'reason': '包含"验收记录"关键词'
            },
            
            # 长文档类型
            {
                'query': '帮我生成一号楼施工方案',
                'expected_tool': 'long_document_generator',
                'document_type': '长文档',
                'reason': '包含"施工方案"关键词'
            },
            {
                'query': '写一个项目可行性研究报告',
                'expected_tool': 'long_document_generator',
                'document_type': '长文档',
                'reason': '包含"研究报告"关键词'
            },
            {
                'query': '制定安全管理制度',
                'expected_tool': 'long_document_generator',
                'document_type': '长文档',
                'reason': '包含"管理制度"关键词'
            }
        ]
        
        correct_count = 0
        total_count = len(test_cases)
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n🔍 测试案例 {i}: {case['document_type']}")
            print(f"📝 查询: {case['query']}")
            print(f"🎯 期望工具: {case['expected_tool']}")
            print(f"💡 判断依据: {case['reason']}")
            print("-" * 40)
            
            try:
                # 运行Agent (只看第一轮的工具选择)
                agent.conversation_history = []  # 清空历史
                response = agent.solve(case['query'])
                
                # 检查是否调用了期望的工具
                conversation_text = ' '.join([
                    str(entry.get('content', ''))
                    for entry in agent.conversation_history
                ])
                
                tool_used = case['expected_tool'] in conversation_text
                
                if tool_used:
                    print(f"✅ 正确：Agent选择了 {case['expected_tool']} 工具")
                    correct_count += 1
                else:
                    print(f"❌ 错误：Agent没有选择期望的工具")
                    # 显示实际选择的工具
                    tools = ['template_conversion', 'long_document_generator', 'rag_tool', 'professional_document_agent']
                    actual_tools = [tool for tool in tools if tool in conversation_text]
                    if actual_tools:
                        print(f"   实际选择: {actual_tools[0]}")
                    else:
                        print(f"   实际选择: 未识别到工具调用")
                
            except Exception as e:
                print(f"❌ 测试执行失败: {e}")
        
        print("\n" + "=" * 50)
        print(f"🎯 测试结果: {correct_count}/{total_count} 正确")
        print(f"📊 准确率: {correct_count/total_count*100:.1f}%")
        
        if correct_count == total_count:
            print("🎉 完美！Agent能正确区分模板文档和长文档")
        elif correct_count >= total_count * 0.8:
            print("😊 良好！Agent大部分情况能正确判断")
        else:
            print("😓 需要改进！Agent的判断准确率较低")
            
        print("\n💡 关键区别:")
        print("📋 模板文档: 记录、表格、申请、审批、检查、验收")
        print("📄 长文档: 方案、报告、计划、规程、制度、分析")
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_document_type_detection() 