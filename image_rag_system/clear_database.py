#!/usr/bin/env python3
"""
清理数据库脚本 - 删除所有表并重新创建
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.database_service import DatabaseService

def clear_database():
    """清理数据库表"""
    try:
        print("🗄️ 清理数据库表...")
        
        # 创建数据库服务实例
        db_service = DatabaseService()
        
        # 重建表（删除所有数据）
        db_service.recreate_tables()
        
        print("✅ 数据库表清理完成")
        
    except Exception as e:
        print(f"❌ 数据库清理失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧹 开始清理数据库...")
    success = clear_database()
    
    if success:
        print("🎉 数据库清理成功！")
    else:
        print("💥 数据库清理失败！")
        sys.exit(1) 