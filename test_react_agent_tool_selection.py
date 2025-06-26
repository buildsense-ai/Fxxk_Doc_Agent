#!/usr/bin/env python3
"""
测试ReactAgent是否正确选择长文档生成工具
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_agent_tool_selection():
    """测试Agent是否会选择正确的工具"""
    print("🧪 测试ReactAgent工具选择逻辑")
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
            max_iterations=3  # 限制迭代次数用于测试
        )
        
        # 测试用例
        test_cases = [
            {
                'query': '帮我生成一个一号楼的施工方案',
                'expected_tool': 'long_document_generator',
                'description': '施工方案生成'
            },
            {
                'query': '处理这个模板文件：uploads/template.docx', 
                'expected_tool': 'template_conversion',
                'description': '模板文件处理'
            },
            {
                'query': '搜索关于项目管理的相关资料',
                'expected_tool': 'rag_tool',
                'description': 'RAG搜索'
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n🔍 测试案例 {i}: {case['description']}")
            print(f"📝 查询: {case['query']}")
            print(f"🎯 期望工具: {case['expected_tool']}")
            print("-" * 40)
            
            try:
                # 运行Agent
                response = agent.solve(case['query'])
                
                # 简单检查是否调用了期望的工具（通过检查对话历史）
                conversation_contains_tool = any(
                    case['expected_tool'] in str(entry.get('content', ''))
                    for entry in agent.conversation_history
                )
                
                if conversation_contains_tool:
                    print(f"✅ 成功：Agent尝试使用了 {case['expected_tool']} 工具")
                else:
                    print(f"❌ 失败：Agent没有使用期望的工具")
                    
                print(f"📄 响应: {response[:200]}{'...' if len(response) > 200 else ''}")
                
            except Exception as e:
                print(f"❌ 测试执行失败: {e}")
        
        print("\n" + "=" * 50)
        print("🎯 测试完成！")
        print("\n💡 如果看到Agent正确调用了long_document_generator工具，")
        print("   说明修改生效，现在可以正确处理长文档生成请求了！")
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agent_tool_selection() 