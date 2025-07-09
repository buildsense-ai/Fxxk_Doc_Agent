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
    
    # 更改工作目录到项目根目录
    project_root = current_dir.parent
    os.chdir(project_root)
    print(f"🔧 切换工作目录到: {project_root}")
    
    # 启动服务器 (跳过导入检查，直接启动)
    print("🚀 启动ReactAgent MCP服务器...")
    server_script_path = "server/main.py"
    os.system(f"python {server_script_path}")

if __name__ == "__main__":
    main() 