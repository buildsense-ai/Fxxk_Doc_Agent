#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from urllib.parse import urlencode

def check_ports():
    """检查常用端口上的服务"""
    ports = [8000, 8001, 8080, 3000, 5000]
    
    for port in ports:
        try:
            response = requests.get(f"http://127.0.0.1:{port}/docs", timeout=3)
            if response.status_code == 200:
                print(f"✅ 端口 {port}: FastAPI 文档页面可访问")
                
                # 检查是否有我们的工具
                try:
                    test_response = requests.get(f"http://127.0.0.1:{port}/tools/fill_template", timeout=3)
                    print(f"   - fill_template 端点状态: {test_response.status_code}")
                except:
                    print(f"   - fill_template 端点不可访问")
                    
            else:
                print(f"⚠️  端口 {port}: HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ 端口 {port}: 连接被拒绝")
        except requests.exceptions.Timeout:
            print(f"⏱️  端口 {port}: 连接超时")
        except Exception as e:
            print(f"❓ 端口 {port}: {e}")

if __name__ == "__main__":
    check_ports() 