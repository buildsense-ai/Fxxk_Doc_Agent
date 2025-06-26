#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试上传docx文件到MinIO云存储
"""

import os
from long_generator.upload_cloud import upload_to_minio

def test_upload_docx():
    """
    测试上传docx文件
    """
    # docx文件路径  
    docx_file_path = "tasks/task_c8104b2b-5aa0-42dc-8422-62dfaf6b40f8.docx"
    
    # 检查文件是否存在
    if not os.path.exists(docx_file_path):
        print(f"错误：文件不存在 - {docx_file_path}")
        return False
    
    # 生成对象名称（云存储中的文件名）
    object_name = "test_uploads/task_c8104b2b-5aa0-42dc-8422-62dfaf6b40f8.docx"
    
    print(f"准备上传文件：{docx_file_path}")
    print(f"目标对象名称：{object_name}")
    
    # 调用上传函数
    try:
        result_url = upload_to_minio(docx_file_path, object_name)
        
        if result_url:
            print(f"✅ 上传成功！")
            print(f"文件访问URL: {result_url}")
            return True
        else:
            print("❌ 上传失败！")
            return False
            
    except Exception as e:
        print(f"❌ 上传过程中发生异常: {e}")
        return False

if __name__ == "__main__":
    print("=== 测试MinIO云存储上传功能 ===")
    success = test_upload_docx()
    
    if success:
        print("\n🎉 测试完成：上传功能正常工作！")
    else:
        print("\n💥 测试失败：请检查配置和网络连接") 