#!/usr/bin/env python3
"""
ReactAgent MCP服务器启动脚本
确保正确的Python路径和依赖
"""

import sys
import os
from pathlib import Path

def main():
    # 获取当前脚本目录
    current_dir = Path(__file__).parent
    
    # 添加ReactAgent的src目录到Python路径
    reactagent_src = current_dir.parent / "src"
    paper2poster_dir = current_dir.parent / "Paper2Poster" / "Paper2Poster"
    
    # 添加路径到sys.path
    paths_to_add = [str(reactagent_src), str(paper2poster_dir)]
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)
    
    print(f"✅ 添加Python路径:")
    for path in paths_to_add:
        print(f"   - {path}")
    
    # 检查必要的依赖
    try:
        import fastapi
        import uvicorn
        print("✅ FastAPI和Uvicorn已安装")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请安装: pip install fastapi uvicorn")
        return
    
    # 检查ReactAgent组件
    try:
        from tools import create_core_tool_registry
        from deepseek_client import DeepSeekClient
        from enhanced_react_agent import EnhancedReActAgent
        print("✅ ReactAgent组件检查通过")
    except ImportError as e:
        print(f"❌ ReactAgent组件导入失败: {e}")
        return
    
    # 启动服务器
    print("🚀 启动ReactAgent MCP服务器...")
    os.system(f"cd {current_dir} && python reactagent-mcp-server.py")

if __name__ == "__main__":
    main() 