#!/usr/bin/env python3
import requests
import json

def test_doc_processing():
    """测试文档处理"""
    print("🧪 测试现场复核记录文档处理...")
    
    try:
        url = "http://127.0.0.1:5000/api/chat"
        data = {
            "message": "请处理uploads/现场复核记录.doc文件"
        }
        
        print(f"📤 发送请求: {data['message']}")
        
        response = requests.post(url, json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ 请求成功")
                print(f"📄 响应: {result.get('response', '')[:200]}...")
            else:
                print(f"❌ 请求失败: {result.get('error', '')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"响应: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_doc_processing() 