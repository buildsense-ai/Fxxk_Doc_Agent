#!/usr/bin/env python3
"""
测试ReactAgent的完整工作流程
验证所有交互都通过ReAct循环处理
"""

import requests
import json
import time

def test_react_agent_flow():
    """测试ReactAgent的ReAct循环处理流程"""
    
    base_url = "http://localhost:5000"
    
    print("🧪 测试ReactAgent的ReAct循环处理...")
    
    # 测试用例
    test_cases = [
        {
            "name": "简单查询",
            "message": "你好，请介绍一下你的工作原理",
            "expected_keywords": ["Thought", "Action", "Observation"]
        },
        {
            "name": "工具选择测试",
            "message": "请帮我搜索一下关于项目管理的资料",
            "expected_keywords": ["rag_tool", "搜索", "检索"]
        },
        {
            "name": "文档生成测试",
            "message": "请生成一份项目计划书",
            "expected_keywords": ["文档", "生成", "计划书"]
        },
        {
            "name": "模板处理测试",
            "message": "请处理一个Word模板文件",
            "expected_keywords": ["模板", "处理", "转换"]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ 测试: {test_case['name']}")
        print(f"请求: {test_case['message']}")
        
        try:
            # 发送请求到ReactAgent
            response = requests.post(f"{base_url}/api/chat", 
                                   json={"message": test_case['message'], "stream": False})
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    agent_response = data['response']
                    print(f"✅ ReactAgent响应成功")
                    print(f"响应长度: {len(agent_response)} 字符")
                    
                    # 检查响应中是否包含预期关键词
                    found_keywords = []
                    for keyword in test_case['expected_keywords']:
                        if keyword in agent_response:
                            found_keywords.append(keyword)
                    
                    if found_keywords:
                        print(f"🎯 找到相关关键词: {', '.join(found_keywords)}")
                    else:
                        print(f"⚠️  未找到预期关键词: {test_case['expected_keywords']}")
                    
                    # 显示响应摘要
                    print(f"响应摘要: {agent_response[:100]}...")
                    
                else:
                    print(f"❌ ReactAgent处理失败: {data['error']}")
            else:
                print(f"❌ 请求失败，状态码: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 测试过程出错: {e}")
        
        # 等待一段时间避免请求过快
        time.sleep(1)
    
    print("\n🎉 ReactAgent工作流程测试完成！")

def test_react_agent_verbose():
    """测试ReactAgent的详细输出（启用verbose模式）"""
    print("\n🔍 测试ReactAgent详细输出...")
    
    # 这里可以添加更详细的测试，比如检查ReAct循环的每个步骤
    test_message = "请分析一下你可以使用哪些工具"
    
    try:
        response = requests.post("http://localhost:5000/api/chat", 
                               json={"message": test_message, "stream": False})
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print("✅ ReactAgent详细响应:")
                print("-" * 50)
                print(data['response'])
                print("-" * 50)
            else:
                print(f"❌ 错误: {data['error']}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试出错: {e}")

if __name__ == "__main__":
    # 首先检查服务是否运行
    try:
        response = requests.get("http://localhost:5000/api/system/tools")
        if response.status_code == 200:
            data = response.json()
            print(f"🚀 ReactAgent系统运行正常，已加载 {data['count']} 个工具")
            
            # 运行测试
            test_react_agent_flow()
            test_react_agent_verbose()
        else:
            print("❌ ReactAgent系统未运行，请先启动 python web_app.py")
    except Exception as e:
        print(f"❌ 无法连接到ReactAgent系统: {e}")
        print("请确保已启动 python web_app.py") 