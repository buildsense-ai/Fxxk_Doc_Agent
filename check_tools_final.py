#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.tools import create_core_tool_registry

def main():
    print("🔍 检查工具移除后的状态...")
    
    try:
        registry = create_core_tool_registry()
        print(f"✅ 当前工具数量: {len(registry.tools)}")
        print("\n📋 工具列表:")
        for name in registry.tools.keys():
            print(f"  - {name}")
        
        print(f"\n📊 工具摘要:")
        print(registry.get_tool_summary())
        
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    main() 