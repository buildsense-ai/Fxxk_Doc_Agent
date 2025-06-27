#!/usr/bin/env python3
"""
Standalone Site Review Record Generator
一号楼现场复核记录生成器 - 独立版本
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """主函数 - 生成一号楼现场复核记录"""
    try:
        print("🏗️ 一号楼现场复核记录生成器")
        print("=" * 50)
        print(f"🕐 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Import required modules
        print("📦 正在加载必要模块...")
        from src.deepseek_client import DeepSeekClient
        from src.enhanced_react_agent import EnhancedReActAgent
        
        # Initialize DeepSeek client
        print("🔧 正在初始化DeepSeek AI客户端...")
        client = DeepSeekClient()
        print("✅ DeepSeek客户端初始化成功")
        
        # Initialize ReactAgent
        print("🤖 正在初始化ReactAgent...")
        agent = EnhancedReActAgent(client, verbose=True)
        print("✅ ReactAgent初始化成功")
        
        # Generate site review record
        print("\n🎯 开始生成一号楼现场复核记录...")
        print("-" * 30)
        
        user_request = "生成一个一号楼的现场复核记录"
        response = agent.solve(user_request)
        
        print("\n" + "=" * 50)
        print("🎉 生成完成!")
        print("📋 生成结果:")
        print(response)
        
        # Check if document was generated
        if "generated_docs" in response and ".docx" in response:
            print("\n✅ 文档已成功生成并保存!")
            print("📁 请查看项目根目录下的 generated_docs 文件夹")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 生成过程中出现错误: {str(e)}")
        print("\n🔧 可能的解决方案:")
        print("1. 检查网络连接")
        print("2. 确认DeepSeek API密钥配置正确")
        print("3. 确保所有依赖包已安装")
        print("4. 检查模板文件是否存在于 templates_storage 目录")
        
        import traceback
        print("\n📝 详细错误信息:")
        traceback.print_exc()
        return False

def check_environment():
    """检查环境配置"""
    print("🔍 检查环境配置...")
    
    # Check API key
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if api_key:
        print(f"✅ DeepSeek API Key: {api_key[:10]}...")
    else:
        print("❌ DeepSeek API Key 未配置")
        return False
    
    # Check base URL
    base_url = os.getenv("DEEPSEEK_BASE_URL")
    print(f"✅ Base URL: {base_url}")
    
    # Check template directory
    template_dir = "templates_storage"
    if os.path.exists(template_dir):
        template_files = [f for f in os.listdir(template_dir) if f.endswith(('.doc', '.docx'))]
        print(f"✅ 模板目录存在，找到 {len(template_files)} 个模板文件")
        if template_files:
            print("   📄 可用模板:")
            for template in template_files[:5]:  # Show first 5
                print(f"      - {template}")
    else:
        print("⚠️ 模板目录不存在")
    
    return True

if __name__ == "__main__":
    print("🚀 一号楼现场复核记录生成器 v1.0")
    print("🏗️ Building Site Review Record Generator")
    print("=" * 60)
    
    # Check environment first
    if not check_environment():
        print("\n❌ 环境检查失败，请检查配置后重试")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    
    # Run main generation process
    success = main()
    
    if success:
        print("\n🎉 一号楼现场复核记录生成完成!")
        print("📁 请查看 generated_docs 文件夹中的生成文档")
    else:
        print("\n❌ 生成失败，请检查错误信息后重试")
        sys.exit(1) 