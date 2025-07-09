#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def test_minio_connection():
    """测试MinIO连接"""
    try:
        from minio import Minio
        
        # 测试不同的端口配置
        endpoints = [
            "43.139.19.144:9000",
            "43.139.19.144:9001", 
            "43.139.19.144:8000"
        ]
        
        for endpoint in endpoints:
            print(f"\n🔍 测试连接: {endpoint}")
            try:
                client = Minio(
                    endpoint,
                    access_key="minioadmin",
                    secret_key="minioadmin",
                    secure=False
                )
                
                # 尝试列出存储桶
                buckets = client.list_buckets()
                print(f"✅ 连接成功! 找到 {len(buckets)} 个存储桶:")
                for bucket in buckets:
                    print(f"   - {bucket.name} (创建于: {bucket.creation_date})")
                
                # 检查templates存储桶
                if client.bucket_exists("templates"):
                    print("✅ templates 存储桶存在")
                else:
                    print("⚠️  templates 存储桶不存在，尝试创建...")
                    client.make_bucket("templates")
                    print("✅ templates 存储桶创建成功")
                
                return endpoint  # 返回成功的端点
                
            except Exception as e:
                print(f"❌ 连接失败: {e}")
                
        print("\n❌ 所有端点都连接失败")
        return None
        
    except ImportError:
        print("❌ MinIO库未安装，请运行: pip install minio")
        return None

if __name__ == "__main__":
    test_minio_connection() 