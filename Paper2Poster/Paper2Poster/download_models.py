#!/usr/bin/env python3
"""
下载Docling所需的模型
"""

import os
from pathlib import Path
from docling.utils.model_downloader import download_models

def main():
    # 设置模型下载目录
    models_dir = Path("./models_cache")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"开始下载模型到: {models_dir.absolute()}")
    
    try:
        # 下载所有必需的模型
        download_models(
            output_dir=models_dir,
            force=False,
            progress=True,
            with_layout=True,
            with_tableformer=False,  # 暂时不下载table模型以减少下载时间
            with_code_formula=False,
            with_picture_classifier=False,
            with_smolvlm=False,
            with_easyocr=True  # EasyOCR已经安装，这个会下载其模型
        )
        
        print(f"✅ 模型下载完成！模型存储在: {models_dir.absolute()}")
        
        # 设置环境变量，让Docling使用本地模型
        print(f"\n要使用本地模型，请设置环境变量:")
        print(f"export DOCLING_CACHE_DIR={models_dir.absolute()}")
        
    except Exception as e:
        print(f"❌ 模型下载失败: {e}")
        
        # 尝试使用国内镜像源
        print("\n尝试配置Hugging Face镜像源...")
        try:
            os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
            print("已设置Hugging Face镜像源为: https://hf-mirror.com")
            
            # 重试下载
            download_models(
                output_dir=models_dir,
                force=False,
                progress=True,
                with_layout=True,
                with_tableformer=False,
                with_code_formula=False,
                with_picture_classifier=False,
                with_smolvlm=False,
                with_easyocr=True
            )
            
            print(f"✅ 使用镜像源下载成功！模型存储在: {models_dir.absolute()}")
            
        except Exception as e2:
            print(f"❌ 镜像源下载也失败: {e2}")
            print("\n请检查网络连接或手动下载模型")

if __name__ == "__main__":
    main() 