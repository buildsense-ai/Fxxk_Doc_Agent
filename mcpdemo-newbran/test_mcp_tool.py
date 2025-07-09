#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 fill_template 工具
"""

import requests
import json

def test_fill_template():
    """测试fill_template工具"""
    url = "http://127.0.0.1:8000/tools/fill_template"
    
    # 测试数据
    template_url = "http://43.139.19.144:9000/docs/event_doc_10_20250427113334.docx"
    
    test_data = {
        "label_project_name": "广州历史建筑修复",
        "label_inspection_date": "2025年1月20日",
        "label_inspector": "张工程师",
        "label_weather": "晴朗",
        "label_temperature": "18-22℃",
        "label_humidity": "65%",
        "label_wind_level": "2级",
        "label_site_condition": "良好",
        "label_equipment_status": "正常运行",
        "label_safety_measures": "已落实到位",
        "label_progress_description": "按计划进行",
        "label_quality_assessment": "符合标准",
        "label_next_inspection": "2025年1月27日",
        "label_remarks": "无异常情况",
        "label_signature": "张工程师",
        "label_signature_date": "2025年1月20日",
        "label_review_signature": "李主管"
    }
    
    params = {
        "template_url": template_url,
        "output_filename": "巡视记录_广州历史建筑修复_20250120.docx"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print("🚀 开始测试 fill_template 工具...")
        print(f"模板URL: {template_url}")
        print(f"填充数据字段数: {len(test_data)}")
        
        response = requests.post(url, params=params, json=test_data, headers=headers)
        
        print(f"HTTP状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 测试成功!")
            print(f"成功填充字段数: {result.get('filled_fields_count', 0)}")
            print(f"输出文件名: {result.get('output_filename', 'N/A')}")
            print(f"MinIO访问地址: {result.get('minio_url', 'N/A')}")
            print(f"处理消息: {result.get('message', 'N/A')}")
        else:
            print("❌ 测试失败!")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")

if __name__ == "__main__":
    test_fill_template() 