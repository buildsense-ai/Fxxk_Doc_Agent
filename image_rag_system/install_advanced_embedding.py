#!/usr/bin/env python3
"""
高质量嵌入模型安装脚本
安装 BGE-M3 (多功能、多语言、轻量级)
"""

import subprocess
import sys
import torch
import time

def run_command(command, description):
    """运行命令并显示进度"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} 完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失败:")
        print(f"错误: {e.stderr}")
        return False

def check_gpu():
    """检查GPU可用性"""
    print("\n🔍 检查系统配置...")
    
    if torch.cuda.is_available():
        gpu_count = torch.cuda.device_count()
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        
        print(f"✅ 检测到 {gpu_count} 个GPU")
        print(f"   主GPU: {gpu_name}")
        print(f"   显存: {gpu_memory:.1f} GB")
        
        if gpu_memory < 2:
            print("⚠️  警告: BGE-M3 推荐至少2GB显存")
            print("   不过CPU模式也可以运行")
        else:
            print("✅ 显存充足，可以运行BGE-M3")
        return True
    else:
        print("❌ 未检测到CUDA GPU")
        print("   注意: 高质量模型需要GPU支持")
        return False

def install_dependencies():
    """安装依赖包"""
    print("\n📦 安装依赖包...")
    
    # 核心依赖
    packages = [
        "transformers>=4.35.0",
        "sentence-transformers>=2.2.0", 
        "FlagEmbedding>=1.2.0",
        "torch>=2.0.0"
    ]
    
    # 可选但推荐的包
    optional_packages = [
        "xformers",           # 内存优化
    ]
    
    # 安装核心依赖
    for package in packages:
        if not run_command(f"pip install {package}", f"安装 {package}"):
            return False
    
    # 尝试安装可选依赖
    for package in optional_packages:
        print(f"\n🔧 尝试安装 {package} (可选优化包)...")
        try:
            subprocess.run(f"pip install {package}", shell=True, check=True, capture_output=True)
            print(f"✅ {package} 安装成功")
        except:
            print(f"⚠️  {package} 安装失败，跳过 (不影响基本功能)")
    
    return True

def download_model():
    """预下载模型"""
    print("\n📥 预下载模型...")
    
    download_script = '''
import torch
from FlagEmbedding import BGEM3FlagModel

print("正在下载 BGE-M3 模型...")
try:
    model = BGEM3FlagModel(
        'BAAI/bge-m3',
        use_fp16=False,  # CPU模式下不使用FP16
        device="cpu"     # 先在CPU上加载，避免显存问题
    )
    print("✅ BGE-M3模型下载完成")
    
    # 测试编码
    test_text = "这是一个测试文本"
    output = model.encode(test_text, return_dense=True, return_sparse=False, return_colbert_vecs=False)
    embeddings = output['dense_vecs']
    print(f"✅ 模型测试成功，嵌入维度: {embeddings.shape}")
    
except Exception as e:
    print(f"❌ BGE-M3模型下载失败: {e}")
    exit(1)
'''
    
    try:
        with open("temp_download_model.py", "w", encoding="utf-8") as f:
            f.write(download_script)
        
        result = subprocess.run([sys.executable, "temp_download_model.py"], 
                              capture_output=True, text=True, timeout=600)
        
        # 清理临时文件
        import os
        if os.path.exists("temp_download_model.py"):
            os.remove("temp_download_model.py")
            
        if result.returncode == 0:
            print("✅ 模型预下载成功")
            return True
        else:
            print(f"❌ 模型下载失败: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 模型下载超时")
        return False
    except Exception as e:
        print(f"❌ 模型下载异常: {e}")
        return False

def test_embedding_service():
    """测试嵌入服务"""
    print("\n🧪 测试嵌入服务...")
    
    test_script = '''
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from app.services.embedding_service_advanced import AdvancedEmbeddingService
    
    print("初始化高质量嵌入服务...")
    service = AdvancedEmbeddingService()
    
    # 测试文本嵌入
    text = "测试中文文本嵌入效果"
    text_embedding = service.encode_text(text)
    print(f"✅ 文本嵌入成功，维度: {text_embedding.shape}")
    
    # 测试图片嵌入（如果CLIP可用）
    from PIL import Image
    import numpy as np
    
    # 创建测试图片
    test_image = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))
    image_embedding = service.encode_image(test_image)
    print(f"✅ 图片嵌入成功，维度: {image_embedding.shape}")
    
    # 测试相似度计算
    similarity = service.compute_similarity(text_embedding, image_embedding)
    print(f"✅ 相似度计算成功: {similarity:.4f}")
    
    # 清理资源
    service.cleanup()
    print("✅ 所有测试通过")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
'''
    
    try:
        with open("temp_test_service.py", "w", encoding="utf-8") as f:
            f.write(test_script)
        
        result = subprocess.run([sys.executable, "temp_test_service.py"], 
                              capture_output=True, text=True, timeout=300)
        
        # 清理临时文件
        import os
        if os.path.exists("temp_test_service.py"):
            os.remove("temp_test_service.py")
            
        if result.returncode == 0:
            print("✅ 嵌入服务测试成功")
            print(result.stdout)
            return True
        else:
            print(f"❌ 嵌入服务测试失败:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def main():
    """主安装流程"""
    print("🚀 BGE-M3嵌入模型安装脚本")
    print("="*50)
    print("模型: BAAI/bge-m3")
    print("特性: 多功能(Dense+Sparse+ColBERT)、多语言(100+)、长文本(8192)")
    print("显存需求: ~2GB (vs Qwen2的16GB+)")
    print("="*50)
    
    # 1. 检查GPU
    gpu_ok = check_gpu()
    if not gpu_ok:
        response = input("\n是否继续安装? (y/N): ")
        if response.lower() != 'y':
            print("安装取消")
            return
    
    # 2. 安装依赖
    if not install_dependencies():
        print("❌ 依赖安装失败")
        return
    
    # 3. 下载模型
    if not download_model():
        print("❌ 模型下载失败")
        return
    
    # 4. 测试服务
    if not test_embedding_service():
        print("❌ 服务测试失败")
        return
    
    print("\n🎉 BGE-M3嵌入模型安装完成!")
    print("\n📋 安装总结:")
    print("  ✅ 依赖包已安装")
    print("  ✅ BGE-M3 模型已下载")
    print("  ✅ 嵌入服务测试通过")
    print("\n🚀 下一步:")
    print("  1. 运行: python app_complete.py")
    print("  2. 访问: http://localhost:8080")
    print("  3. 查看: 系统将自动使用BGE-M3模型")

if __name__ == "__main__":
    main() 